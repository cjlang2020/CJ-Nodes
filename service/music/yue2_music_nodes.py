# -*- coding: utf-8 -*-
"""Luy-YuE2 音乐生成节点（CJ-Nodes/service/music）

模型来源: m-a-p/YuE2-3B 的 NF4 量化版；推理引擎 yue2 包内置在 CJ-Nodes/libs/yue2/（无外部绝对路径）。
模型目录约定（ComfyUI 标准相对路径，通过 folder_paths 注册/解析）:
    models/YuE2/models/<variant>/   每个一级子目录一个模型变体（当前 nf4）
    models/YuE2/vae/                VAE（自动加载，不向用户暴露；根目录或子目录均可）

加载流程（约 160-200s，进程级缓存，输入不变不重载）:
    config 骨架(_from_config) -> 换 LinearNF4 槽位 -> Params4bit.from_prequantized 注入全部权重
    -> 猴子补丁 modeling_yue2.YuE2ForCausalLM -> YuE2Pipeline(memory_budget_gib=8,
    backend="torch-eager", offload_ar=True)

其它说明:
- 引擎源码可用环境变量 YUE2_SRC 覆盖（默认用 CJ-Nodes/libs）。
- 引擎必须放在 service/ 之外：CJ-Nodes/nodes.py 会递归加载 service/ 下所有 .py，
  包目录（含 __init__.py）放进去会被当节点文件逐个加载而报相对导入错误。
- 新增模型变体/VAE **不需要重启**：`folder_paths.get_filename_list` 有 mtime 失效检查，新增/删除文件或子目录会立刻反映，刷新页面（F5）即可（2026-09 实测）。
- 严禁在 ComfyUI 的 python_embeded 环境升级/降级 torch/transformers/numpy（会破坏 ComfyUI）。
"""
import os
import sys
import gc
import json
import re
import time

import torch
import folder_paths

# ── 引擎源码路径（默认 CJ-Nodes/libs，内含 yue2 包；可用 YUE2_SRC 覆盖）──────
_HERE = os.path.dirname(os.path.abspath(__file__))          # service/music
_CJ_ROOT = os.path.dirname(os.path.dirname(_HERE))          # CJ-Nodes
_YUE2_SRC = os.environ.get("YUE2_SRC", os.path.join(_CJ_ROOT, "libs"))
if _YUE2_SRC not in sys.path:
    sys.path.insert(0, _YUE2_SRC)

# ── ComfyUI 标准模型目录注册（相对路径方式）─────────────────────────────
# 注册后走 folder_paths.get_filename_list / get_full_path 枚举与解析，
# 下拉值与缓存键均为相对名，代码不硬编码绝对模型路径。
_YUE2_FOLDER = "YuE2"          # 主模型变体（一级子目录 = 变体名，如 nf4）
_YUE2_VAE_FOLDER = "YuE2_VAE"   # VAE

_MODELS_BASE = os.path.join(folder_paths.models_dir, "YuE2", "models")
_VAE_BASE = os.path.join(folder_paths.models_dir, "YuE2", "vae")
os.makedirs(_MODELS_BASE, exist_ok=True)
os.makedirs(_VAE_BASE, exist_ok=True)
folder_paths.add_model_folder_path(_YUE2_FOLDER, _MODELS_BASE)
folder_paths.add_model_folder_path(_YUE2_VAE_FOLDER, _VAE_BASE)

# NF4 需要跳过的敏感层（与 quantize_yue2_nf4.py 保持一致）
_SKIP_PREFIXES = ("lm_head", "llm2vae", "vae2llm", "time_embedder", "latent_pos_embed")
_QUANT_PREFIX = "model.layers."

# 进程级缓存: 主模型对象按 variant 复用；pipeline 按 (variant, vae) 复用
_STATE = {"model": None, "variant": None, "variant_dir": None, "pipelines": {}, "last": None}

# 同一插件里其它音乐节点的模块名（CJ-Nodes 的 loader 用 cj_nodes_<文件名> 命名）。
# 8GB 卡上 YuE2(2.1GB) + 扇谱(峰值 ~3.4GB) 同时常驻会撞 ComfyUI 的 6GB/进程上限，
# 所以两边在加载前都会看一下空闲显存，不够就请对方先让开（需要时会自动重载）。
_MUSIC_MODULES = ("cj_nodes_sheetsage2_music_nodes", "cj_nodes_yue2_music_nodes")


def _free_sibling_models(keep_module, log):
    """加载大模型前无条件请同级音乐节点让出显存。

    为什么不做“够不够”的判断：实测 OOM 报的是 **ComfyUI 的 6GB/进程额度**（
    “6.00 GiB allowed, 507.75 MiB free”），而 torch.cuda.mem_get_info() 报的是**设备**空闲量，
    看不出额度快满。YuE2(2.1GB) + 扇谱(峰值 ~3.4GB) 在这张 8GB 卡上就是不该同时常驻，
    所以直接互换：重载 25-30s，比 OOM 掉一次 20 分钟的生成划算得多。
    同级模块未加载模型时，unload_model() 本身是空操作，不影响单独跑任一节点。
    """
    try:
        if torch.cuda.is_available():
            free = torch.cuda.mem_get_info()[0] / 1024 ** 3
        else:
            free = 0.0
        for name in _MUSIC_MODULES:
            if keep_module in name:
                continue
            module = sys.modules.get(name)
            unload = getattr(module, "unload_model", None) if module is not None else None
            if callable(unload):
                unload()                      # 真去卸；没必要区分本来就没加载的情况
                log("已请另一个音乐模型让出显存（当时设备空闲 %.1fGB），需要时会自动重载" % free)
        gc.collect()
        torch.cuda.empty_cache()
    except Exception as exc:                      # 清理失败不能阻断生成
        log("清理同级模型时出错（已忽略）: %s" % exc)

# NAR attention 分块大小。本机 torch 2.10+cu130 (Windows) 的
# torch.backends.cuda.is_flash_attention_available() == False，SDPA 会回退到 math 后端
# 而**物化**注意力矩阵：实测前半长 2000 token 时整块申请 654MB，分块 256 仅 117MB，
# 且两者输出逐位相同（max|diff|=0）。长歌的 NAR 预填充阶段因此必项分块。
_NAR_QCHUNK = 256


def _install_nar_guard():
    """给 nar.synthesize 注入 query_chunk_size（默认整块会物化注意力矩阵而 OOM）。"""
    import yue2.nar as nar_mod
    if getattr(nar_mod, "_luy_guarded", False):
        return
    orig = nar_mod.synthesize

    def guarded(model, prefix, codec, seed, **kw):
        kw.setdefault("query_chunk_size", _NAR_QCHUNK)
        gc.collect()
        torch.cuda.empty_cache()          # 释放语义阶段的 KV 缓存池
        job = _ACTIVE_JOB.get("job")
        if job is not None:
            inner = kw.get("on_progress")

            def chain(completed, total, _inner=inner):
                if callable(_inner):
                    _inner(completed, total)      # 引擎自己的进度条照旧
                job.nar_step(completed, total)     # 额外上报给节点的 ETA 计算

            kw["on_progress"] = chain
        print("[Luy-YuE2] nar prefill 分块 attention (query_chunk_size=%d)" % kw["query_chunk_size"],
              flush=True)
        return orig(model, prefix, codec, seed, **kw)

    nar_mod.synthesize = guarded
    nar_mod._luy_guarded = True


def _install_vae_progress():
    """给 YuE2VAE.decode_tiled 挂 on_progress（VAE 分块解码，每块 ~1s）。"""
    import yue2.modeling_vae as vae_mod
    if getattr(vae_mod, "_luy_vae_hooked", False):
        return
    orig = vae_mod.YuE2VAE.decode_tiled

    def hooked(self, *args, **kw):
        job = _ACTIVE_JOB.get("job")
        if job is not None:
            inner = kw.get("on_progress")

            def chain(completed, total, _inner=inner):
                if callable(_inner):
                    _inner(completed, total)
                job.vae_chunk(completed, total)

            kw["on_progress"] = chain
        return orig(self, *args, **kw)

    vae_mod.YuE2VAE.decode_tiled = hooked
    vae_mod._luy_vae_hooked = True


def _guard_pipeline_stages(pipe):
    """在重显存阶段前清缓存（pipeline.__call__ 内部会调用这两个方法）。"""
    if getattr(pipe, "_luy_guarded", False):
        return pipe
    _install_nar_guard()
    _install_vae_progress()
    orig_synth, orig_decode = pipe.synthesize, pipe.decode

    def synth(semantic, *, cancelled=None, **kw):
        gc.collect()
        torch.cuda.empty_cache()
        return orig_synth(semantic, cancelled=cancelled, **kw)

    def decode(latents, **kw):
        gc.collect()
        torch.cuda.empty_cache()
        return orig_decode(latents, **kw)

    pipe.synthesize, pipe.decode = synth, decode
    pipe._luy_guarded = True
    return pipe


# ═══════════════════════════ 目录扫描（folder_paths 相对路径方式）═══════════════════════════

def _norm(names):
    return [n.replace("\\", "/") for n in names]


# YuE2 生成模型的专属标记文件（用于把同目录下的 SheetSage2 / MERT backbone 排除掉）
_YUE2_ONLY_FILES = ("modeling_yue2.py", "qwen.tiktoken")
_NON_YUE2_FILES = ("modeling_sheetsage2.py", "modeling_mert2.py", "configuration_mert2.py")


def scan_model_variants():
    """列出 YuE2 文件夹下的模型变体（相对目录名，如 'nf4'）。
    变体 = 同时含 model.safetensors + config.json + YuE2 专属文件的一级子目录。
    注意: models/YuE2/models 下同时放有 SheetSage2 与 MERT-v2-FullSong（扒谱用），
    它们也含 model.safetensors + config.json，必须靠专属标记文件排除，
    否则会在本节点的模型下拉里出现（选了会加载失败）。"""
    try:
        names = _norm(folder_paths.get_filename_list(_YUE2_FOLDER))
    except Exception:
        return []
    variants = set()
    for name in names:
        if "/" not in name:
            continue
        d = name.split("/")[0]
        if f"{d}/model.safetensors" not in names or f"{d}/config.json" not in names:
            continue
        if not any(f"{d}/{marker}" in names for marker in _YUE2_ONLY_FILES):
            continue
        if any(f"{d}/{marker}" in names for marker in _NON_YUE2_FILES):
            continue
        variants.add(d)
    return sorted(variants)


def scan_vaes():
    """列出可选 VAE（相对名）: 根目录合法则含 '(根目录)'，另加合法子目录。"""
    try:
        names = _norm(folder_paths.get_filename_list(_YUE2_VAE_FOLDER))
    except Exception:
        return []
    has_root = "model.safetensors" in names and "config.json" in names
    subdirs = set()
    for name in names:
        if "/" not in name:
            continue
        d = name.split("/")[0]
        if f"{d}/model.safetensors" in names and f"{d}/config.json" in names:
            subdirs.add(d)
    return (["(根目录)"] if has_root else []) + sorted(subdirs)


def _resolve_vae(vae_choice):
    """VAE 相对名 → 真实目录。"""
    rel = "model.safetensors" if vae_choice == "(根目录)" else f"{vae_choice}/model.safetensors"
    full = folder_paths.get_full_path(_YUE2_VAE_FOLDER, rel)
    if full is None:
        raise FileNotFoundError(f"VAE 不存在: {vae_choice}")
    return os.path.dirname(full)


def default_vae():
    """自动选择 VAE（不向用户暴露）: 优先根目录，其次第一个合法子目录。"""
    vaes = scan_vaes()
    if not vaes:
        raise FileNotFoundError(
            "未找到 VAE: 请将 VAE 放到 ComfyUI/models/YuE2/vae/ "
            "（目录需含 config.json + model.safetensors）")
    return vaes[0]


def _resolve_model_dir(model_variant):
    full = folder_paths.get_full_path(_YUE2_FOLDER, f"{model_variant}/model.safetensors")
    if full is None:
        raise FileNotFoundError(f"模型变体不存在: {model_variant}")
    return os.path.dirname(full)


# ═══════════════════════════ 进度估算（百分比 / 预计剩余时间）═══════════════════════════
# 引擎自带的 Progress 在“总量未知”时不给百分比（ABC 规划与语义生成两阶段），而这两阶段
# 恰恰是最让人等得焦心的。本模块按项目内实测标度估算总量，从两三给出百分比与 ETA：
#   目标时长 s ≈ 歌词行数 × 330 ÷ BPM（BPM 从风格文本里解析，缺省 88）
#   帧数 = s × 25；语义 token ≈ 帧数（1 token = 40ms）
#   ABC token ≈ s × BPM × 0.13（经验值：实测 132s/80BPM 的歌词生出 1348 token；
#        引擎本身不暴露该总量，只能估）
#   NAR ≈ ode_steps 步（默认 32），每步耗时随帧数超线性增长（实测 1500/3000/6000/9000 帧
#        → 150/336/992/1900 s），先用幂律预估，跑起来后用实测步速修正
#   VAE ≈ 每 512 帧 1 s
# 估算只用于显示；某阶段一开始，ETA 就改用该阶段的实测速率。任何异常都不得影响生成。
# 控制台每 5 秒只打一行（避免刷屏），进度条则每次回调都更新（ComfyUI 内部自带节流）。
_ACTIVE_JOB = {"job": None}
_STAGE_ORDER = ("规划乐谱(ABC)", "语义生成", "流匹配(NAR)", "VAE解码")
_ABC_TOKENS_PER_BPM_SECOND = 0.13         # ABC token ≈ 音频秒数 × BPM × 0.13（实测）
_RATE_ABC = 8.0                            # token/s 经验值（实测 7-18，随桌面负载波动）
_RATE_SEMANTIC = 10.0

_PHASE_STAGE = {"abc": "规划乐谱(ABC)", "semantic": "语义生成"}


def _fmt_duration(seconds):
    seconds = max(0.0, float(seconds))
    if seconds < 60:
        return "%.0fs" % seconds
    if seconds < 3600:
        return "%d分%02d秒" % (int(seconds // 60), int(seconds % 60))
    return "%d小时%02d分" % (int(seconds // 3600), int((seconds % 3600) // 60))


def _parse_bpm(style):
    match = re.search(r"(\d+(?:\.\d+)?)\s*BPM", str(style or ""), re.IGNORECASE)
    return float(match.group(1)) if match else 0.0


def _count_lyric_lines(lyrics):
    """统计有效歌词行（去掉空行与 [Verse]/[Chorus] 这类结构标签）。"""
    count = 0
    for line in str(lyrics or "").splitlines():
        text = line.strip()
        if not text or (text.startswith("[") and text.endswith("]")):
            continue
        count += 1
    return count


def _nar_seconds_estimate(frames):
    """从实测点插值（幂律，实测 1500/3000/6000/9000 帧 → 150/336/992/1900 s）。"""
    frames = max(1.0, float(frames))
    return 0.00475 * (frames ** 1.417)


class _JobProgress:
    """把 yue2 的分阶段进度换算成整体百分比/预计剩余时间，并驱动 ComfyUI 进度条。"""

    def __init__(self, style="", lyrics="", abc_text="", cot="full",
                 ode_steps=32, vae_core_frames=512, log=print):
        self.log = log
        self.bar = None
        self.t0 = time.time()
        self._last = 0.0
        self._last_bar = -1
        self._finished = []
        bpm = _parse_bpm(style) or 88.0
        lines = _count_lyric_lines(lyrics)
        self.seconds = max(15.0, lines * 330.0 / bpm)
        self.frames = self.seconds * 25.0
        has_external_abc = bool(str(abc_text or "").strip())
        # 每阶段预估耗时（秒）；为 0 表示该阶段会被跳过
        self.est = {
            "规划乐谱(ABC)": 0.0 if (has_external_abc or cot == "off") else
                             max(50.0, self.seconds * bpm * _ABC_TOKENS_PER_BPM_SECOND),
            "语义生成": max(50.0, self.frames),
            "流匹配(NAR)": float(max(1, int(ode_steps))),
            "VAE解码": float(max(1, -(-int(self.frames) // max(1, int(vae_core_frames))))),
        }
        # 预估耗时（秒）：整体权重 + 未开始阶段的 ETA；单位与总量分开存，别混用
        self.est_time = {
            "规划乐谱(ABC)": 0.0 if self.est["规划乐谱(ABC)"] <= 0
                             else self.est["规划乐谱(ABC)"] / _RATE_ABC,
            "语义生成": self.est["语义生成"] / _RATE_SEMANTIC,
            "流匹配(NAR)": _nar_seconds_estimate(self.frames),
            "VAE解码": self.est["VAE解码"],
        }
        self.state = {name: {"done": 0.0, "total": self.est[name], "start": None, "end": None}
                      for name in _STAGE_ORDER}
        self.skipped = {name for name, value in self.est.items() if value <= 0}
        self.log("预计：歌词 %d 行 × (330 ÷ %g BPM) ≈ %s 音频 ≈ %d 帧；"
                 "预估总耗时 %s（计划 %s / 语义 %s / 流匹配 %s / 解码 %s）" % (
                     lines, bpm, _fmt_duration(self.seconds), int(self.frames),
                     _fmt_duration(sum(self.est_time.values())),
                     _fmt_duration(self.est_time["规划乐谱(ABC)"]),
                     _fmt_duration(self.est_time["语义生成"]),
                     _fmt_duration(self.est_time["流匹配(NAR)"]),
                     _fmt_duration(self.est_time["VAE解码"])))

    # ── 阶段状态 ────────────────────────────────────────────────────────
    def _touch(self, name):
        """把 name 之前未开始的阶段（有回调说明它们在跑）标记为开始，返回当前阶段状态。"""
        if name in self.skipped:
            return None
        state = self.state[name]
        if state["start"] is None:
            state["start"] = time.time()
            for earlier in _STAGE_ORDER[:_STAGE_ORDER.index(name)]:
                if earlier not in self.skipped and self.state[earlier]["start"] is not None \
                        and self.state[earlier]["end"] is None:
                    self._finish_stage(earlier)
            self.log("▶ 阶段 %d/%d %s …" % (_STAGE_ORDER.index(name) + 1, len(_STAGE_ORDER), name))
        return state

    def _finish_stage(self, name, note=""):
        state = self.state[name]
        state["end"] = time.time()
        spent = state["end"] - (state["start"] or state["end"])
        unit = "步" if name == "流匹配(NAR)" else ("块" if name == "VAE解码" else "token")
        self._finished.append(name)
        self.log("✓ 阶段 %s 完成：%s%.0f %s | 用时 %s（预估值 %s）" % (
            name, note, state["done"], unit, _fmt_duration(spent),
            _fmt_duration(self.est_time[name])))

    def _pct(self, name):
        state = self.state[name]
        total = state["total"] or self.est[name]
        if total <= 0:
            return 1.0
        return min(1.0, state["done"] / total)

    def _overall(self):
        """整体百分比 = 按预估耗时加权的各阶段进度之和。

        用意：比“已用时间 / (已用 + 估算剩余)”稳定得多——后者会因实测速率重估而**倒退**
        （实测：70% → 66% → 64%）。加权求和由构造上保证单调不降。
        """
        total = sum(self.est_time.values())
        if total <= 0:
            return 100.0
        done = sum(self.est_time[name] * self._pct(name) for name in _STAGE_ORDER)
        return 100.0 * done / total

    def _remaining(self):
        """剩余秒数：已完成的阶段算 0；进行中的阶段用实测速率（未就绪则用预估比例）；未开始用预估。"""
        remaining = 0.0
        for name in _STAGE_ORDER:
            if name in self.skipped:
                continue
            state = self.state[name]
            if state["end"] is not None:
                continue
            if state["start"] is None:
                remaining += self.est_time[name]
                continue
            elapsed = max(1e-6, time.time() - state["start"])
            pct = self._pct(name)
            # 用实测速率外推；起步阶段（进度太少或时间太短）测得不准，先用预估
            if state["done"] > 0 and pct >= 0.02 and elapsed >= 3.0:
                remaining += elapsed * (1.0 - pct) / pct
            else:
                remaining += max(0.0, self.est_time[name] - elapsed)
        return remaining

    def _render(self, force=False):
        now = time.time()
        elapsed = now - self.t0
        remaining = self._remaining()
        all_done = all(self.state[n]["end"] is not None or n in self.skipped for n in _STAGE_ORDER)
        overall = 100.0 if all_done else min(99.0, self._overall())
        # 进度条：每次回调都更新（update_absolute 内部有节流），UI 上能看到百分比
        if self.bar is not None:
            value = int(overall)
            if value != self._last_bar:
                try:
                    self.bar.update_absolute(value, 100)
                    self._last_bar = value
                except Exception:
                    pass
        if not force and now - self._last < 5.0:
            return
        self._last = now
        running = [n for n in _STAGE_ORDER
                   if n not in self.skipped and self.state[n]["start"] is not None
                   and self.state[n]["end"] is None]
        detail = "准备中"
        if running:
            name = running[0]
            state = self.state[name]
            spent = max(1e-6, now - state["start"])
            total = state["total"] or self.est[name]
            if name == "流匹配(NAR)":
                unit, speed = "步", ("%.1fs/步" % (spent / state["done"]) if state["done"] else "")
            elif name == "VAE解码":
                unit, speed = "块", ("%.1fs/块" % (spent / state["done"]) if state["done"] else "")
            else:
                unit = "token"
                speed = ("%.1f token/s" % (state["done"] / spent)) if spent >= 1 else ""
            detail = "%s %.0f/%.0f %s (%.0f%%) %s%s" % (
                name, state["done"], total, unit, 100 * self._pct(name), speed,
                " 已超预估" if state["done"] > total else "")
        self.log("整体 %.0f%% | %s | 已用 %s | 预计剩余 %s" % (
            overall, detail, _fmt_duration(elapsed), _fmt_duration(remaining)))

    def _set(self, name, done, total=None):
        state = self._touch(name)
        if state is None:
            return
        if total and state["total"] != total:
            state["total"] = float(total)          # NAR/VAE 能拿到精确总量，改成精确百分比
        if done is not None:
            state["done"] = float(done)
        self._render()

    # ── 引擎回调 ────────────────────────────────────────────────────────
    def token(self, phase, token):
        try:
            self._set(_PHASE_STAGE.get(str(phase), "语义生成"),
                      self.state[_PHASE_STAGE.get(str(phase), "语义生成")]["done"] + 1)
        except Exception:
            pass

    def nar_step(self, completed, total):
        try:
            self._set("流匹配(NAR)", completed, total)
        except Exception:
            pass

    def vae_chunk(self, completed, total):
        try:
            self._set("VAE解码", completed, total)
        except Exception:
            pass

    def finish(self, audio_seconds=0.0):
        try:
            for name in _STAGE_ORDER:
                if name not in self.skipped and self.state[name]["start"] is not None \
                        and self.state[name]["end"] is None:
                    self._finish_stage(name)
            self._render(force=True)
            spent = time.time() - self.t0
            est_total = sum(self.est_time.values())
            ratio = spent / max(1e-6, est_total)
            self.log("全部完成：音频 %.1fs | 实际总耗时 %s（事前预估 %s，实际比预估%s %.0f%%）" % (
                float(audio_seconds), _fmt_duration(spent), _fmt_duration(est_total),
                "慢" if ratio > 1 else "快", abs(ratio - 1) * 100))
        except Exception:
            pass


# ═══════════════════════════ 引擎封装 ═══════════════════════════

def _yue2_modules():
    """惰性导入 yue2（避免拖慢 ComfyUI 启动）。"""
    import yue2.modeling_yue2 as modeling
    from yue2.modeling_yue2 import YuE2Config
    from bitsandbytes.nn import LinearNF4, Params4bit
    from safetensors.torch import safe_open
    # _install_stub 会把模块属性 YuE2ForCausalLM 换成桩（pipeline 靠它复用已建好的权重）。
    # 真类存在引擎模块上，重建（卸载后重载 / 换变体 / 插件热重载）时取它，
    # 否则从模块属性拿到的是桩，_from_config 直接报 AttributeError。
    cls = getattr(modeling, "_REAL_YuE2ForCausalLM", None) or modeling.YuE2ForCausalLM
    return YuE2Config, cls, LinearNF4, Params4bit, safe_open


def _is_nf4_dir(model_dir):
    """模型目录是否为 bnb NF4 打包格式（含 weight.absmax 类 key）。"""
    _, _, _, _, safe_open = _yue2_modules()
    with safe_open(os.path.join(model_dir, "model.safetensors"), framework="pt", device="cpu") as f:
        for k in f.keys():
            if k.endswith(".weight.absmax"):
                return True
    return False


def _swap_nf4_slots(net, LinearNF4, prefix=""):
    """递归把 decoder 层 nn.Linear 换成空 LinearNF4 槽位（不复制权重）。"""
    n = 0
    for name, child in list(net.named_children()):
        full = f"{prefix}{name}"
        if isinstance(child, torch.nn.Linear):
            if full.split(".")[0] in _SKIP_PREFIXES or not full.startswith(_QUANT_PREFIX):
                continue
            setattr(net, name, LinearNF4(child.in_features, child.out_features,
                                         bias=child.bias is not None,
                                         compute_dtype=torch.bfloat16))
            n += 1
        else:
            n += _swap_nf4_slots(child, LinearNF4, full + ".")
    return n


def _build_nf4_model(model_dir):
    """从 NF4 目录构建完整模型（骨架 + 全量权重注入，不读 models/ 原目录、不联网）。

    性能关键：transformers 的 `_from_config` 内部不含 `no_init_weights`（`from_pretrained` 才有），
    默认会对 34 亿参数做一次完整随机初始化 —— 实测 **153.8s**，而随后所有参数都会被
    safetensors 覆盖，属于纯浪费。改用 meta 设备构建（实测 0.07s）+ 全量赋值。
    """
    YuE2Config, YuE2ForCausalLM, LinearNF4, Params4bit, safe_open = _yue2_modules()

    config = YuE2Config.from_pretrained(model_dir)
    with torch.device("meta"):          # 不分配内存、不做随机初始化
        model = YuE2ForCausalLM._from_config(config)
    n = _swap_nf4_slots(model, LinearNF4)
    model.eval()
    print("[Luy-YuE2] skeleton: %d NF4 slots" % n, flush=True)

    consumed = set()
    path = os.path.join(model_dir, "model.safetensors")
    # device="cuda": mmap 直接拷入显存，省去 CPU 中转
    with safe_open(path, framework="pt", device="cuda") as f:
        keys = set(f.keys())
        for name, m in model.named_modules():
            if not isinstance(m, LinearNF4):
                continue
            p = f"{name}."
            wkey = p + "weight"
            if wkey not in keys:
                raise KeyError(f"missing packed weight: {wkey}")
            qs = {}
            for k in keys:
                if k.startswith(p):
                    rel = k[len(p):]
                    if rel not in ("weight", "bias"):
                        qs[rel] = f.get_tensor(k)
                        consumed.add(k)
            m.weight = Params4bit.from_prequantized(f.get_tensor(wkey), qs,
                                                    device="cuda", module=m)
            consumed.add(wkey)
            if p + "bias" in keys:
                m.bias = torch.nn.Parameter(f.get_tensor(p + "bias"), requires_grad=False)
                consumed.add(p + "bias")

        missing = []
        for pname, _param in list(model.named_parameters()):
            if pname in consumed or isinstance(_param, Params4bit):
                continue
            if pname not in keys:
                missing.append(pname)
                continue
            parent = model.get_submodule(pname.rsplit(".", 1)[0]) if "." in pname else model
            parent._parameters[pname.rsplit(".", 1)[-1]] = torch.nn.Parameter(
                f.get_tensor(pname), requires_grad=False)
            consumed.add(pname)
        if missing:
            raise KeyError("params not covered by safetensors: %s" % missing[:5])

        for bname, _buf in list(model.named_buffers()):
            if bname in keys and bname not in consumed:
                parent = model.get_submodule(bname.rsplit(".", 1)[0]) if "." in bname else model
                parent._buffers[bname.rsplit(".", 1)[-1]] = f.get_tensor(bname)
                consumed.add(bname)

    leftover = keys - consumed
    if leftover:
        raise ValueError("unexpected extra keys in %s: %s" % (path, sorted(leftover)[:5]))
    # meta 构建后必须全部被赋值覆盖，否则后续前向会静默产出垃圾
    meta_left = [n_ for n_, t in list(model.named_parameters()) + list(model.named_buffers())
                 if t.is_meta]
    if meta_left:
        raise RuntimeError("meta tensors not populated: %s" % meta_left[:5])
    model.to("cuda")
    print("[Luy-YuE2] weights injected: %d keys" % len(consumed), flush=True)
    return model


def _install_stub(YuE2ForCausalLM):
    """猴子补丁: pipeline._load_model 内部局部导入 YuE2ForCausalLM，
    运行时解析模块属性，替换为返回缓存模型的桩。"""
    import yue2.modeling_yue2 as modeling

    class _Stub:
        @staticmethod
        def from_pretrained(path, **kwargs):
            if _STATE["model"] is None:
                raise RuntimeError("YuE2 model cache is empty")
            return _STATE["model"]

    # 桩只接管 from_pretrained；真类必须留一份，否则重建时无从拿到 _from_config
    modeling._REAL_YuE2ForCausalLM = YuE2ForCausalLM
    modeling.YuE2ForCausalLM = _Stub


def unload_model():
    """卸载全部 YuE2 模型与管线，**真正**释放显存。

    注意：pipeline 自己也持有 `_model`/`_vae` 引用，只清 _STATE 是释放不掉的（模型仍在显存），
    所以必须先断开管线里的引用再清缓存。
    """
    n = len(_STATE["pipelines"])
    for pipe in list(_STATE["pipelines"].values()):
        try:
            pipe._model = None
            pipe._vae = None
        except Exception:
            pass
    _STATE["pipelines"].clear()
    _STATE["model"] = None
    _STATE["variant"] = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("[Luy-YuE2] unloaded (%d pipelines)" % n, flush=True)
    return n


def _pipeline_alive(pipe):
    """管线是否仍持有模型（被别节点腾显存后会是 None）。"""
    return pipe is not None and getattr(pipe, "_model", None) is not None


def get_pipeline(model_variant, vae_choice, log=lambda m: None):
    """获取（或构建并缓存）YuE2Pipeline。"""
    key = (model_variant, vae_choice)
    _STATE["last"] = key                       # 记下来：显存被回收后可据此重建
    cached = _STATE["pipelines"].get(key)
    if _pipeline_alive(cached):
        return cached

    model_dir = _resolve_model_dir(model_variant)
    vae_dir = _resolve_vae(vae_choice)

    # 加载前请扇谱节点让开（两侧互斥，避免 8GB 卡双模型 OOM）
    _free_sibling_models("cj_nodes_yue2_music_nodes", log)

    t0 = time.time()
    YuE2Config, YuE2ForCausalLM, LinearNF4, Params4bit, safe_open = _yue2_modules()

    # 1) 主模型：variant 未变则复用已注入的权重对象（省 160s）
    if _STATE["model"] is None or _STATE["variant"] != model_variant:
        log(f"加载主模型 {model_variant}（首次约 3 分钟）...")
        if _is_nf4_dir(model_dir):
            _STATE["model"] = _build_nf4_model(model_dir)
        else:
            # 原始 bf16 权重目录（未来变体），走 HF dtype 新参数名
            _STATE["model"] = YuE2ForCausalLM.from_pretrained(
                model_dir, local_files_only=True, dtype=torch.bfloat16,
                low_cpu_mem_usage=True).eval().to("cuda")
        _STATE["variant"] = model_variant
        _STATE["variant_dir"] = model_dir
        _install_stub(YuE2ForCausalLM)
        log(f"主模型就绪（{time.time() - t0:.0f}s）")

    # 2) 管线：轻量构建（权重已在缓存对象里）
    from yue2 import YuE2Pipeline
    pipe = YuE2Pipeline.from_pretrained(
        model_dir, vae=vae_dir, device="cuda",
        memory_budget_gib=8, quantization="none",
        backend="torch-eager", offload_ar=True,
    )
    _STATE["pipelines"][key] = pipe
    _guard_pipeline_stages(pipe)
    log(f"管线就绪（累计 {time.time() - t0:.0f}s）")
    return pipe


# ═══════════════════════════ 节点 1：加载模型 ═══════════════════════════

class CJYuE2ModelLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "模型变体": (scan_model_variants(), {
                    "tooltip": "models/YuE2/models 下的一级子目录名（需含 model.safetensors + config.json）；"
                               "新增模型后按 F5 刷新页面即可",
                }),
            },
            # 顺序闸门：ComfyUI 只按“数据依赖”决定先后，本节点与扒谱分支原本互不相干，
            # 而调度器 ux_friendly_pick_node 优先挑“2 跳内能到输出节点”的节点
            # （加载 → 生成 → 保存 = 2 跳，扒谱 → 拼接 → 生成 → 保存 = 3 跳），
            # 于是加载器总是先跑、YuE2 先占 2.1GB，扒谱再加载就撞 6GB 额度 OOM。
            # 把扒谱的任意输出连到这里，就形成强依赖，拓扑排序保证扒谱跑完（且已释放显存）才加载。
            "optional": {
                "前置依赖": ("*", {
                    "forceInput": True,
                    "tooltip": "把「Luy-SheetSage2扒谱」的任意输出（推荐「扒谱信息」）连到这里："
                               "强制本节点等扒谱跑完、显存释放后再加载 YuE2（8GB 卡防 OOM）。\n"
                               "不连则保持原行为（谁先跑由 ComfyUI 调度决定，可能 OOM）。",
                }),
            },
        }

    RETURN_TYPES = ("YUE2_MODEL",)
    RETURN_NAMES = ("音乐模型",)
    FUNCTION = "load"
    CATEGORY = "luy/音乐"
    DESCRIPTION = ("加载 YuE2 音乐生成模型（NF4）。首次加载约 3 分钟，之后进程内缓存复用。\n"
                   "模型放在 ComfyUI/models/YuE2/models/<变体>/，VAE 自动从 models/YuE2/vae/ 加载。\n"
                   "与扒谱同流时，请把扒谱节点的输出连到「前置依赖」，保证先扒谱（并释放显存）再加载模型。")

    def load(self, 模型变体, 前置依赖=None):
        # 界面参数名用中文；内部沿用原有英文局部名，保持逻辑不变
        model_variant = 模型变体
        vae = default_vae()
        if 前置依赖 is not None:
            # 有依赖线＝扒谱已跑完并释放显存，这里能打印出来就证明执行顺序对了
            print("[Luy-YuE2] 前置依赖已就绪（扒谱完成），开始加载模型", flush=True)
        pipe = get_pipeline(model_variant, vae, log=lambda m: print(f"[Luy-YuE2] {m}", flush=True))
        return (pipe,)


# ═══════════════════════════ 节点 2：生成音乐 ═══════════════════════════

class CJYuE2Generate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            # 必调参数（按使用频次排序）: 模型 → 风格 → 歌词
            "required": {
                "音乐模型": ("YUE2_MODEL", {
                    "tooltip": "接「Luy-YuE2音乐模型加载」的输出",
                }),
                "风格": ("STRING", {
                    "default": "English, warm piano pop, expressive female voice, acoustic piano, "
                               "rounded bass and light drums, lyrical memorable melody, unhurried phrasing, 88 BPM",
                    "multiline": False,
                    "placeholder": "风格标签（乐器/人声/节奏/BPM）",
                    "tooltip": "可直接接「Luy-音乐风格标签」的「风格」输出，或接「Luy-字符串拼接」的合并结果",
                }),
                "歌词": ("STRING", {
                    "default": "[Verse] ... [Chorus] ...",
                    "multiline": False,
                    "placeholder": "歌词，支持 [Verse]/[Chorus]/[Bridge]/[Outro] 等结构标签",
                    "tooltip": "歌词行数决定时长（≈ 行数 × 330 ÷ BPM 秒）",
                }),
            },
            # 可选参数（由常用到少用），随机种子固定在最后
            "optional": {
                "生成模式": (["full", "melody", "off"], {
                    "tooltip": "full=自动规划带和弦乐谱（默认，一般无需修改）；"
                               "melody=配合【乐谱ABC】使用（伴奏自由，翻唱推荐）；off=跳过乐谱规划、直接由风格+歌词生成",
                }),
                "CFG强度": ("FLOAT", {"default": -1.0, "min": -1.0, "max": 20.0, "step": 0.05,
                                        "tooltip": "一般无需修改：-1=自动（等效不做 CFG）；>1 启用符号 CFG 且耗时翻倍"}),
                "乐谱ABC": ("STRING", {"default": "", "multiline": False,
                                        "tooltip": "外部 ABC 乐谱（可选，可接扒谱节点的「旋律谱ABC」/「完整谱ABC」）；"
                                                   "非空时【生成模式】需为 melody/full"}),
                "ABC最大长度": ("INT", {"default": 4096, "min": 64, "max": 8192, "step": 64,
                                           "tooltip": "自动规划乐谱的长度上限；仅当状态栏出现 truncated.abc=true 时调大（对外部传入的乐谱不截断）"}),
                "语义最大长度": ("INT", {"default": 9000, "min": 64, "max": 16000, "step": 64,
                                                "tooltip": "语义 token 上限（≈歌曲时长保险丝，调大不会让歌变长）；仅当 truncated.semantic=true 时调大"}),
                "高级采样JSON": ("STRING", {"default": "", "multiline": False,
                                                      "tooltip": '（实验用）JSON 覆盖采样参数，如 {"abc":{"temperature":0.8},"semantic":{"top_k":80}}'}),
                "随机种子": ("INT", {"default": 831001, "min": 0, "max": 2**63 - 1,
                                 "tooltip": "同一套参数换种子可出不同版本（面板上的 randomize/fixed 即对应随机/固定）"}),
            },
        }

    RETURN_TYPES = ("AUDIO", "STRING",)
    RETURN_NAMES = ("音频", "生成信息",)
    FUNCTION = "generate"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = False
    DESCRIPTION = ("YuE2 音乐生成：风格+歌词 → ABC 乐谱 → 语义 token → 流匹配 → VAE → 48kHz 立体声。\n"
                   "单次生成约 3-6 分钟（8GB 卡）。接「Luy-音乐风格标签」的「风格」+ 自行撰写歌词即最简用法。")

    def generate(self, 音乐模型, 风格, 歌词, 生成模式="full", CFG强度=-1.0,
                 乐谱ABC="", ABC最大长度=4096, 语义最大长度=9000,
                 高级采样JSON="", 随机种子=831001):
        # 界面参数名用中文；内部沿用原有英文局部名，保持逻辑不变
        model, style, lyrics = 音乐模型, 风格, 歌词
        cot, cfg_scale, abc_text = 生成模式, CFG强度, 乐谱ABC
        abc_max_tokens, semantic_max_tokens = ABC最大长度, 语义最大长度
        advanced_sampling_json, seed = 高级采样JSON, 随机种子

        # 扇谱节点可能为了腾显存把模型卸了（见 _free_sibling_models）→ 按记下的参数重建
        if not _pipeline_alive(model):
            if _STATE.get("last") is None:
                raise RuntimeError("YuE2 模型已被显存回收且无可重建参数：请重新运行「Luy-YuE2音乐模型加载」节点")
            print("[Luy-YuE2] 模型已被显存回收，正在重新加载（约 25-30s）…", flush=True)
            model = get_pipeline(_STATE["last"][0], _STATE["last"][1],
                                 log=lambda m: print(f"[Luy-YuE2] {m}", flush=True))

        import numpy as np
        from comfy.utils import ProgressBar
        import comfy.model_management as comfy_mm

        if not style.strip() or not lyrics.strip():
            raise ValueError("style 与 lyrics 不能为空")

        # 采样覆盖：默认两阶段 max_tokens + 高级 JSON
        abc_over = {"max_tokens": int(abc_max_tokens)}
        sem_over = {"max_tokens": int(semantic_max_tokens)}
        if advanced_sampling_json.strip():
            extra = json.loads(advanced_sampling_json)
            abc_over.update(extra.get("abc", {}) or {})
            sem_over.update(extra.get("semantic", {}) or {})

        # song_id 不向用户暴露：仅影响 result.json 指纹，不影响音频（RNG 只由 seed 决定）
        req_kwargs = {"cot": cot, "seed": int(seed), "id": "song"}
        if cfg_scale is not None and cfg_scale >= 0:
            req_kwargs["cfg_scale"] = float(cfg_scale)
        if abc_text.strip():
            req_kwargs["abc"] = abc_text

        def _cancelled():
            try:
                comfy_mm.throw_exception_if_processing_interrupted()
            except Exception:
                return True
            return False

        # 进度：整体百分比 + 各阶段 ETA + ComfyUI 进度条（估算依据见 _JobProgress 注释）
        job = _JobProgress(style=style, lyrics=lyrics, abc_text=abc_text, cot=cot,
                           ode_steps=int(getattr(getattr(model, "generation_config", None),
                                                 "ode_steps", 32) or 32),
                           vae_core_frames=int(getattr(model, "vae_core_frames", 512) or 512),
                           log=lambda m: print(f"[Luy-YuE2] {m}", flush=True))
        job.bar = ProgressBar(100)

        def on_token(phase, token):
            job.token(phase, token)

        _ACTIVE_JOB["job"] = job
        t0 = time.time()
        try:
            song = model(style=style, lyrics=lyrics,
                         abc_sampling=abc_over, semantic_sampling=sem_over,
                         cancelled=_cancelled, on_token=on_token, **req_kwargs)
        except InterruptedError:
            import nodes as comfy_nodes
            raise comfy_nodes.InterruptProcessingException()
        finally:
            _ACTIVE_JOB["job"] = None

        arr = np.asarray(song.audio)
        if arr.ndim == 2 and arr.shape[1] <= 8:  # (T, C) 帧×声道 → (C, T)
            arr = arr.T
        waveform = torch.from_numpy(np.ascontiguousarray(arr)).float().unsqueeze(0)  # (1, C, T)
        audio = {"waveform": waveform, "sample_rate": int(song.sample_rate)}
        seconds = len(song.audio) / song.sample_rate
        job.finish(seconds)
        info = (f"时长 {seconds:.1f}s | 采样率 {song.sample_rate} | 截断 {dict(song.truncated)} | "
                f"耗时 {time.time() - t0:.0f}s | seed {seed}")
        print(f"[Luy-YuE2] {info}", flush=True)
        return (audio, info)


# ═══════════════════════════ 节点 3：卸载模型 ═══════════════════════════

class CJYuE2Unload:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("状态",)
    FUNCTION = "unload"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = True
    DESCRIPTION = "卸载 YuE2 模型并释放显存。请放在单独的工作流中单独运行（勿与生成节点同流）。"

    def unload(self):
        n = unload_model()
        return (f"YuE2 已卸载（清理 {n} 条管线）",)


NODE_CLASS_MAPPINGS = {
    "CJYuE2ModelLoader": CJYuE2ModelLoader,
    "CJYuE2Generate": CJYuE2Generate,
    "CJYuE2Unload": CJYuE2Unload,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CJYuE2ModelLoader": "Luy-YuE2模型加载",
    "CJYuE2Generate": "Luy-YuE2音乐生成",
    "CJYuE2Unload": "Luy-YuE2卸载模型",
}
