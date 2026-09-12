# -*- coding: utf-8 -*-
"""Luy-SheetSage2 音频扒谱节点（CJ-Nodes/service/music）

音频 → 乐谱(ABC) / MIDI / 调性 / 和弦 / 曲式结构 / 节拍标注，供 "Luy-YuE2音乐生成" 做旋律复刻。

模型目录（全部相对路径，无硬编码绝对路径）:
    ComfyUI/models/YuE2/models/SheetSage2/          适配器权重 + 推理代码（含 transformers 5.x 兼容补丁）
    ComfyUI/models/YuE2/models/MERT-v2-FullSong/    编码器 backbone（SheetSage2 的 base_model）

关键实现说明（踩坑记录，勿删）:
1) SheetSage2 的 config.json 里 base_model_name_or_path 填的是 HF 仓库名（联网+token 才能用），
   节点改为运行时传 base_model_path=<本地 backbone 绝对路径>（模型代码里有 kwargs.pop("base_model_path")），
   因此完全离线、无需改 config.json。
2) 编码器代码实际来自 MERT 父目录（SheetSage2 目录里的 modeling_mert2.py 只用于 sha256 完整性校验）。
   transformers 5.x 改为 meta 设备初始化 + 直接写 module._buffers[name]（绕过 nn.Module._apply），
   导致 RotaryEmbedding 的非持久 buffer inv_freq（不在 checkpoint 里）变成**未初始化内存**
   → 位置编码全错 → 长音频转写结果崩坏（短片段可能侥幸正常，极具迷惑性）。
   节点加载后调用 _ensure_rotary_buffers() 自检并按公式修复，即便模型目录是原版文件也能正常出谱。
3) 一次推理即可产出两版 ABC：主产物按 melody_only 生成，另一版用 notation.build_rebuilt_abc_score
   从 <run_dir>/notation/* 重建。两版与 YuE2 的 cot 语义严格对应（见 protocol.py 的 COT 描述）:
       无和弦旋律谱(abc_melody) ↔ cot="melody"   官方推荐用于翻唱/旋律复刻
       带和弦完整谱(abc_full)   ↔ cot="full"
4) SheetSage2 是贪心解码、完全确定性（同输入同输出，实测逐位一致），所以节点没有 seed 参数。
5) 渲染钢琴音频/五线谱(render_audio/render_score)需要 playwright + render_assets，且与本机
   torch 无关地依赖浏览器，节点不暴露；需要时用官方 CLI 的 setup_render.py。
"""
import gc
import importlib
import json
import os
import re
import time
from pathlib import Path

import numpy as np
import torch
import folder_paths

# ═══════════════════════════ 模型目录注册（folder_paths 相对路径方式）═══════════════════════════
_SS2_FOLDER = "SheetSage2"
_SS2_BASE = os.path.join(folder_paths.models_dir, "YuE2", "models")
os.makedirs(_SS2_BASE, exist_ok=True)


def _ensure_folder(name, path):
    """幂等注册（热重载会重复执行 import，避免重复追加）。"""
    try:
        entry = folder_paths.folder_names_and_paths.get(name)
        if entry and any(os.path.abspath(p) == os.path.abspath(path) for p in entry[0]):
            return
    except Exception:
        pass
    folder_paths.add_model_folder_path(name, path)


_ensure_folder(_SS2_FOLDER, _SS2_BASE)

# 进程级缓存: 模型按 (variant, dtype) 复用
_STATE = {"model": None, "key": None, "device": None, "dtype": None}

_PLACEHOLDER = "(未找到模型: 请放到 models/YuE2/models/SheetSage2)"


def _norm(names):
    return [n.replace("\\", "/") for n in names]


def scan_sheetsage2_models():
    """列出 SheetSage2 适配器目录（相对名）。变体 = 一级子目录，含
    model.safetensors + config.json + modeling_sheetsage2.py。"""
    try:
        names = _norm(folder_paths.get_filename_list(_SS2_FOLDER))
    except Exception:
        return []
    variants = set()
    for name in names:
        if "/" not in name:
            continue
        d = name.split("/")[0]
        if (f"{d}/model.safetensors" in names and f"{d}/config.json" in names
                and f"{d}/modeling_sheetsage2.py" in names):
            variants.add(d)
    return sorted(variants)


def _resolve_ss2_dir(variant):
    full = folder_paths.get_full_path(_SS2_FOLDER, f"{variant}/model.safetensors")
    if full is None:
        raise FileNotFoundError(
            "SheetSage2 模型不存在: %s（应位于 models/YuE2/models/<变体>/）" % variant)
    return os.path.dirname(full)


def _resolve_mert_dir(ss2_dir):
    """解析 SheetSage2 的编码器 backbone 目录（相对路径推导，允许环境变量覆盖）。"""
    env = os.environ.get("SHEETSAGE2_MERT_DIR")
    if env and os.path.isfile(os.path.join(env, "model.safetensors")):
        return env
    search_root = os.path.dirname(ss2_dir)
    parent_name = ""
    try:
        cfg = json.loads(Path(ss2_dir, "config.json").read_text(encoding="utf-8"))
        parent_name = os.path.basename(
            str(cfg.get("base_model_name_or_path", "")).replace("\\", "/").rstrip("/"))
    except Exception:
        parent_name = ""
    if parent_name:
        cand = os.path.join(search_root, parent_name)
        if os.path.isfile(os.path.join(cand, "model.safetensors")):
            return cand
    # 兜底: 兄弟目录里找含 modeling_mert2.py + model.safetensors 的
    try:
        for name in sorted(os.listdir(search_root)):
            cand = os.path.join(search_root, name)
            if (os.path.isfile(os.path.join(cand, "modeling_mert2.py"))
                    and os.path.isfile(os.path.join(cand, "model.safetensors"))):
                return cand
    except OSError:
        pass
    raise FileNotFoundError(
        "未找到 SheetSage2 的编码器 backbone(MERT-v2-FullSong): 请放到 %s\\<MERT目录>"
        "（需含 modeling_mert2.py + model.safetensors），或设置环境变量 SHEETSAGE2_MERT_DIR"
        % search_root)


# ═══════════════════════════ 模型加载 / 卸载 ═══════════════════════════

def _ensure_rotary_buffers(model):
    """自检并修复 RotaryEmbedding 的 inv_freq（非持久 buffer，meta 加载会被清空）。

    返回被修复的模块名列表（空列表 = 一切正常）。修复后必须清掉 cos/sin 缓存，
    否则会继续复用按错误频率算出的位置编码。
    """
    repaired = []
    for name, module in model.named_modules():
        if type(module).__name__ != "RotaryEmbedding":
            continue
        head_dim, base = getattr(module, "head_dim", None), getattr(module, "base", None)
        current = getattr(module, "inv_freq", None)
        if head_dim is None or base is None or current is None:
            continue
        expected = 1.0 / (float(base) ** (
            torch.arange(0, int(head_dim), 2, dtype=torch.float32) / int(head_dim)))
        try:
            ok = (tuple(current.shape) == tuple(expected.shape)
                  and torch.equal(current.detach().float().cpu(), expected))
        except Exception:
            ok = False
        if ok:
            continue
        module.inv_freq = expected.to(device=current.device, dtype=torch.float32)
        for attr, value in (("_cos", None), ("_sin", None),
                            ("_sequence_length", 0), ("_cache_device", None)):
            try:
                setattr(module, attr, value)
            except Exception:
                pass
        repaired.append(name)
    return repaired


def unload_model():
    """释放 SheetSage2 显存（模型仅 ~2.7GB，重载约 15-20s）。"""
    _STATE.update({"model": None, "key": None, "device": None, "dtype": None})
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return True


def get_model(variant, dtype_str, log):
    key = (variant, dtype_str)
    if _STATE["model"] is not None and _STATE["key"] == key:
        return _STATE["model"]
    unload_model()

    ss2_dir = _resolve_ss2_dir(variant)
    mert_dir = _resolve_mert_dir(ss2_dir)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log("加载 SheetSage2: %s | backbone: %s | 设备: %s" % (
        variant, os.path.basename(mert_dir), device))
    if device == "cpu":
        log("警告: 无 CUDA，CPU 推理会非常慢（长音频建议先设 max_seconds 试跑）")

    from transformers import AutoModel  # 惰性导入，避免拖慢 ComfyUI 启动
    t0 = time.time()
    # base_model_path: 让适配器去本地 backbone 取权重（否则会去 HF 仓库名找，需要联网）
    model = AutoModel.from_pretrained(
        ss2_dir, trust_remote_code=True, local_files_only=True,
        base_model_path=mert_dir, attn_implementation="sdpa",
    ).eval().to(device)

    repaired = _ensure_rotary_buffers(model)
    if repaired:
        log("⚠ 已自动修复被清空的位置编码 buffer(transformers 5.x meta 加载已知问题): %s" % repaired)

    _STATE.update({"model": model, "key": key, "device": device, "dtype": dtype_str})
    log("模型就绪（%.1fs）" % (time.time() - t0))
    return model


# ═══════════════════════════ 结果解读（.lab 标注 → 可读信息）═══════════════════════════

def _read_tsv(path):
    rows = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return rows
    for line in text.splitlines():
        if line.strip():
            rows.append(line.split("\t"))
    return rows


def _interval_rows(path):
    """interval 标注: 起始 \\t 结束 \\t 值。"""
    out = []
    for parts in _read_tsv(path):
        if len(parts) < 3:
            continue
        try:
            out.append((float(parts[0]), float(parts[1]), parts[2].strip()))
        except ValueError:
            continue
    return out


def _beat_rows(path):
    """节拍标注: 时间 \\t 拍号 \\t 每小节拍数 \\t 拍值。"""
    out = []
    for parts in _read_tsv(path):
        if len(parts) < 3:
            continue
        try:
            out.append((float(parts[0]), int(float(parts[1])), int(float(parts[2]))))
        except ValueError:
            continue
    return out


def _time_rows(path):
    out = []
    for parts in _read_tsv(path):
        try:
            out.append(float(parts[0]))
        except (ValueError, IndexError):
            continue
    return out


def _meter_from_labs(run_dir):
    """从 beat.lab 第一行取拍号（每小节拍数 / 拍值）。"""
    rows = _read_tsv(os.path.join(run_dir, "beat.lab"))
    if not rows or len(rows[0]) < 4:
        return ""
    try:
        return "%d/%d" % (int(float(rows[0][2])), int(float(rows[0][3])))
    except ValueError:
        return ""


def _prettify_key(symbol):
    if ":" in symbol:
        tonic, mode = symbol.split(":", 1)
        return "%s %s" % (tonic, mode)
    return symbol


_CHORD_QUALITY = {"maj": "", "min": "m", "min7": "m7", "maj7": "maj7", "maj6": "6",
                  "min6": "m6", "dom7": "7", "7": "7", "sus2": "sus2", "sus4": "sus4",
                  "dim": "dim", "aug": "aug", "hdim7": "m7b5"}


def _prettify_chord(symbol):
    """'B:sus2' → 'Bsus2'、'D:maj' → 'D'、'B:min7/b7' → 'Bm7/b7'（原始写法仍在 chord.lab 里）。"""
    if ":" not in symbol:
        return symbol
    root, quality = symbol.split(":", 1)
    bass = ""
    if "/" in quality:
        quality, bass = quality.split("/", 1)
        bass = "/" + bass
    return root + _CHORD_QUALITY.get(quality, quality) + bass


def _summarize_structure(rows):
    """相邻同名段落合并 → 'intro → verse×2 → chorus×2 → outro'。"""
    merged = []          # [label, 乐句数, 起始, 结束]
    for start, end, label in rows:
        if merged and merged[-1][0] == label:
            merged[-1][1] += 1
            merged[-1][3] = end
        else:
            merged.append([label, 1, start, end])
    text = " → ".join("%s×%d" % (m[0], m[1]) if m[1] > 1 else m[0] for m in merged)
    return text, merged


def _summarize_chords(rows, limit=8):
    order, counts = [], {}
    for _, _, raw_chord in rows:
        chord = _prettify_chord(raw_chord)
        if chord not in counts:
            order.append(chord)
            counts[chord] = 0
        counts[chord] += 1
    ranked = sorted(counts, key=lambda c: (-counts[c], order.index(c)))
    text = "、".join("%s×%d" % (c, counts[c]) for c in ranked[:limit])
    if len(ranked) > limit:
        text += "、…（共 %d 种）" % len(ranked)
    return text, ranked, counts


def _tempo_from_abc(abc_text):
    for line in (abc_text or "").splitlines():
        if line.startswith("Q:"):
            match = re.search(r"=\s*(\d+(?:\.\d+)?)", line)
            if match:
                return float(match.group(1))
    return 0.0


def _tempo_from_labs(run_dir):
    downbeats = _time_rows(os.path.join(run_dir, "downbeat.lab"))
    beats = _beat_rows(os.path.join(run_dir, "beat.lab"))
    if len(downbeats) >= 3:
        period = float(np.median(np.diff(downbeats)))
        numerator = beats[0][2] if beats else 4
        if period > 0:
            return round(60.0 * numerator / period, 2)
    return 0.0

def _build_style_hint(key_text, tempo, meter, structure_text, chart):
    """factual 风格底稿（可直接接生成节点的 style，再补人声/流派/乐器标签）。"""
    if tempo <= 0:
        tempo_part = "unknown tempo"
    elif tempo < 70:
        tempo_part = "%g BPM, very slow" % tempo
    elif tempo < 95:
        tempo_part = "%g BPM, slow" % tempo
    elif tempo < 120:
        tempo_part = "%g BPM, medium tempo" % tempo
    elif tempo < 150:
        tempo_part = "%g BPM, upbeat" % tempo
    else:
        tempo_part = "%g BPM, fast" % tempo
    parts = [key_text or "unknown key", tempo_part]
    if meter:
        parts.append(meter)
    if chart:
        parts.append("harmony built on " + ", ".join(chart[:4]))
    if structure_text:
        if "chorus" in structure_text and "verse" in structure_text:
            parts.append("verse-chorus form")
        parts.append("sections: " + structure_text)
    return ", ".join(parts)


def _derive_other_abc(model, run_dir, main_melody_only):
    """用本次推理写出的 notation 中间文件重建"另一版" ABC（一次推理拿两版）。"""
    notation_dir = os.path.join(run_dir, "notation")
    needed = ["song_melody.mid", "song_beats.txt", "song_chords.txt",
              "song_keys.txt", "song_structures.txt"]
    missing = [n for n in needed if not os.path.isfile(os.path.join(notation_dir, n))]
    if missing:
        return None, "缺少 notation 中间文件 %s（本次 ABC 未生成成功）" % missing
    try:
        pkg = type(model).__module__.rsplit(".", 1)[0]
        notation = importlib.import_module(pkg + ".notation_sheetsage2")
        score = notation.build_rebuilt_abc_score(
            os.path.join(notation_dir, "song_melody.mid"),
            os.path.join(notation_dir, "song_beats.txt"),
            os.path.join(notation_dir, "song_chords.txt"),
            os.path.join(notation_dir, "song_keys.txt"),
            os.path.join(notation_dir, "song_structures.txt"),
            melody_only=not main_melody_only,
        )
        return notation.score_to_abc(score), None
    except Exception as exc:                                  # noqa: BLE001 - 需要把原因回传给用户
        return None, "%s: %s" % (type(exc).__name__, exc)


# ═══════════════════════════ 节点 1：音频扒谱 ═══════════════════════════

class CJSheetSage2Transcribe:
    @classmethod
    def INPUT_TYPES(s):
        models = scan_sheetsage2_models() or [_PLACEHOLDER]
        return {
            "required": {
                "sheetsage2_model": (models, {
                    "tooltip": "models/YuE2/models 下的 SheetSage2 适配器目录；新增模型后需重启 ComfyUI 或点“重载插件”",
                }),
                "audio": ("AUDIO", {
                    "tooltip": "任意采样率/声道，节点内部自动转单声道并重采样到 24kHz（依赖 torchaudio）",
                }),
            },
            "optional": {
                "melody_only": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "存档产物是否去掉和弦（对应 YuE2 的 cot=melody）。无论开关如何，"
                               "两版 ABC 字符串都会同时输出",
                }),
                "dtype": (["bf16", "fp32"], {
                    "default": "bf16",
                    "tooltip": "bf16 又快又省显存；若出现数值异常可改 fp32（显存约翻倍）",
                }),
                "max_seconds": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 3600.0, "step": 1.0,
                    "tooltip": "只处理前 N 秒（0=整首）。长音频自动分 300s 窗滚动推理；"
                               "调参试跑时设 60 之类可省时间",
                }),
                "preset": (["default", "paper"], {
                    "default": "default",
                    "tooltip": "default=通用（推荐）；paper=论文/评测口径（多任务提示词不同，且改用 torchaudio+ffmpeg 读音频）",
                }),
                "overlap_seconds": ("FLOAT", {
                    "default": -1.0, "min": -1.0, "max": 300.0, "step": 1.0,
                    "tooltip": "高级：相邻窗口重叠秒数；-1=用模型默认（200s，实测最稳），不要随意改",
                }),
                "lookahead_seconds": ("FLOAT", {
                    "default": -1.0, "min": -1.0, "max": 300.0, "step": 1.0,
                    "tooltip": "高级：窗口前瞻秒数；-1=用模型默认（100s），不要随意改",
                }),
                "release_after": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "转写后释放显存（约 2.7GB），给后面的音乐生成节点让路；"
                               "关掉可保留模型以便连续扒多段（重载约 15-20s）",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "FLOAT",
                    "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("abc_melody", "abc_full", "style_hint", "key", "tempo",
                    "chords", "structure", "midi_dir", "info")
    FUNCTION = "transcribe"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "SheetSage2 音频扒谱：音频 → 乐谱(ABC)/MIDI/调性/和弦/曲式/节拍。\n"
        "接生成节点的用法：abc_melody → abc_text 且 cot=melody（推荐，旋律复刻）；"
        "abc_full → abc_text 且 cot=full（保留和弦色彩）。\n"
        "style_hint 可直接接生成节点的 style 再补人声/流派标签；歌词需自行提供。\n"
        "8GB 卡约 2.7GB 显存，5 分钟歌约 20-30s；贪心解码、结果确定性，无需 seed。"
    )

    def transcribe(self, sheetsage2_model, audio, melody_only=False, dtype="bf16",
                   max_seconds=0.0, preset="default", overlap_seconds=-1.0,
                   lookahead_seconds=-1.0, release_after=True):
        from comfy.utils import ProgressBar
        import comfy.model_management as comfy_mm

        if sheetsage2_model == _PLACEHOLDER:
            raise FileNotFoundError(
                "未找到 SheetSage2 模型。请把模型放到 %s\\SheetSage2\\（需含 "
                "model.safetensors + config.json + modeling_sheetsage2.py），"
                "并把 backbone 放到同级的 MERT-v2-FullSong\\，然后重启或点“重载插件”" % _SS2_BASE)

        logs = []

        def log(message):
            line = "[Luy-SheetSage2] %s" % message
            print(line, flush=True)
            logs.append(str(message))

        # ── 音频输入（ComfyUI AUDIO: {"waveform": (B,C,T), "sample_rate": int}）──
        if not isinstance(audio, dict) or "waveform" not in audio:
            raise ValueError("请输入 ComfyUI AUDIO 类型（可用核心节点 LoadAudio）")
        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])
        if not torch.is_tensor(waveform):
            waveform = torch.as_tensor(np.asarray(waveform))
        waveform = waveform.detach().float().cpu()
        if waveform.dim() == 3:                      # (B,C,T) → (C,T)
            waveform = waveform[0]
        elif waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        if waveform.dim() != 2:
            raise ValueError("音频张量形状不支持: %s" % (tuple(waveform.shape),))
        seconds = waveform.shape[-1] / max(1, sample_rate)
        log("输入音频: %s 采样率 %d，时长 %.2fs" % (
            "x".join(str(v) for v in waveform.shape), sample_rate, seconds))

        # ── 输出目录（ComfyUI 标准 output 目录下的时间戳子目录）──
        run_dir = os.path.join(folder_paths.get_output_directory(), "SheetSage2",
                               time.strftime("%Y%m%d-%H%M%S"))
        os.makedirs(run_dir, exist_ok=True)

        # ── 进度回调（stage: audio/encoding/decoding/window_complete/notation/complete）──
        progress = {"bar": None, "windows": 0}

        def on_progress(value):
            try:
                comfy_mm.throw_exception_if_processing_interrupted()
            except Exception:
                pass
            stage = str(value.get("stage", ""))
            windows = int(value.get("windows") or 0)
            if progress["bar"] is None and windows:
                progress["bar"] = ProgressBar(windows)
                progress["windows"] = windows
            if stage == "encoding" and windows:
                log("转写第 %s/%s 窗…" % (value.get("window"), windows))
            elif stage == "decoding":
                tokens = int(value.get("tokens") or 0)
                if tokens and tokens % 512 == 0:
                    log("  第 %s/%s 窗已生成 %d token" % (
                        value.get("window"), windows, tokens))
            elif stage == "window_complete" and progress["bar"] is not None:
                progress["bar"].update(1)
                log("  第 %s/%s 窗完成（%s token）" % (
                    value.get("window"), windows, value.get("tokens")))

        # ── 模型 + 推理 ──
        options = {"dtype": dtype, "preset": preset, "output_dir": run_dir,
                   "render_audio": False, "render_score": False,
                   "render_parts": ("mix",), "progress": on_progress}
        if float(max_seconds) > 0:
            options["max_seconds"] = float(max_seconds)
        if float(overlap_seconds) >= 0:
            options["overlap_seconds"] = float(overlap_seconds)
        if float(lookahead_seconds) >= 0:
            options["lookahead_seconds"] = float(lookahead_seconds)
        if melody_only:
            options["melody_only"] = True

        t0 = time.time()
        model = get_model(sheetsage2_model, dtype, log)
        try:
            try:
                result = model.transcribe(waveform, sampling_rate=sample_rate, **options)
            except RuntimeError as exc:
                # melody_only 且 ABC 构建失败时 transcribe 会抛错，但转写结果在 exc.result 里
                partial = getattr(exc, "result", None)
                if partial is None:
                    raise
                log("警告: %s（已保留转录结果，仅 ABC/MIDI 受影响）" % exc)
                result = partial
            elapsed = time.time() - t0

            # ── 一次推理 → 两版 ABC ──
            abc_full = ""
            abc_melody = ""
            abc_notes = []
            main_abc = result.get("abc") or ""
            abc_error = result.get("abc_error")
            if main_abc:
                if melody_only:
                    abc_melody = main_abc
                else:
                    abc_full = main_abc
            other, other_error = _derive_other_abc(model, run_dir, melody_only)
            if other:
                if melody_only:
                    abc_full = other
                else:
                    abc_melody = other
            elif other_error:
                abc_notes.append("另一版 ABC 未生成: %s" % other_error)
            if abc_error:
                abc_notes.append("模型未产出 ABC: %s" % abc_error)
            # 落盘：两版 ABC 都存一份，方便直接用
            if abc_melody:
                Path(run_dir, "score_melody.abc").write_text(
                    abc_melody, encoding="utf-8", newline="\n")
        finally:
            if release_after:
                unload_model()
                log("已释放显存")

        # ── 标注解读 ──
        key_rows = _interval_rows(os.path.join(run_dir, "key.lab"))
        chord_rows = _interval_rows(os.path.join(run_dir, "chord.lab"))
        structure_rows = _interval_rows(os.path.join(run_dir, "structure.lab"))

        key_text = _prettify_key(key_rows[0][2]) if key_rows else ""
        meter = _meter_from_labs(run_dir)
        structure_text, structure_merged = _summarize_structure(structure_rows)
        chord_text, chord_ranked, chord_counts = _summarize_chords(chord_rows)
        tempo = _tempo_from_abc(abc_full or abc_melody) or _tempo_from_labs(run_dir)
        style_hint = _build_style_hint(key_text, tempo, meter, structure_text, chord_ranked)

        info_lines = [
            "时长 %.1fs | %s | %s BPM %s | 和弦 %d 种" % (
                float(result.get("duration_seconds") or seconds), key_text or "调性未知",
                ("%g" % tempo) if tempo else "?", meter, len(chord_ranked)),
            "音符 %s（人声 %s / 器乐 %s） | 小节 %s | ABC 错误: %s" % (
                result.get("melody_notes"), result.get("vocal_notes"),
                result.get("instrumental_notes"), result.get("abc_measures"),
                abc_error or "无"),
            "结构: %s" % (structure_text or "未知"),
            "和弦: %s" % (chord_text or "未知"),
            "style_hint: %s" % style_hint,
            "ABC: melody %d 字符(用 cot=melody) / full %d 字符(用 cot=full)" % (
                len(abc_melody), len(abc_full)),
            "产物目录: %s" % run_dir,
            "耗时 %.1fs | 峰值显存 %s MiB" % (elapsed, result.get("peak_gpu_mib")),
        ]
        for note in abc_notes:
            info_lines.append("提示: %s" % note)
        for warning in (result.get("warnings") or []):
            info_lines.append("警告: %s" % warning)
        info = "\n".join(info_lines)
        for line in info_lines:
            log(line)

        # 供工作流后续节点/人工查看
        Path(run_dir, "summary.txt").write_text(
            info + "\n\nstyle_hint:\n" + style_hint + "\n", encoding="utf-8", newline="\n")

        return (abc_melody, abc_full, style_hint, key_text, float(tempo),
                chord_text, structure_text, run_dir, info)


# ═══════════════════════════ 节点 2：卸载模型 ═══════════════════════════

class CJSheetSage2Unload:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "unload"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = True
    DESCRIPTION = "卸载 SheetSage2 并释放显存（约 2.7GB）。扒谱节点默认已 release_after=True，一般无需手动卸载。"

    def unload(self):
        unload_model()
        return ("SheetSage2 已卸载",)


NODE_CLASS_MAPPINGS = {
    "CJSheetSage2Transcribe": CJSheetSage2Transcribe,
    "CJSheetSage2Unload": CJSheetSage2Unload,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CJSheetSage2Transcribe": "Luy-SheetSage2扒谱",
    "CJSheetSage2Unload": "Luy-SheetSage2卸载模型",
}
