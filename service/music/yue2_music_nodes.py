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
- 新增模型变体/VAE 后需重启 ComfyUI（folder_paths 列表在启动时构建）。
- 严禁在 ComfyUI 的 python_embeded 环境升级/降级 torch/transformers/numpy（会破坏 ComfyUI）。
"""
import os
import sys
import gc
import json
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
_STATE = {"model": None, "variant": None, "variant_dir": None, "pipelines": {}}

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
        print("[Luy-YuE2] nar prefill 分块 attention (query_chunk_size=%d)" % kw["query_chunk_size"],
              flush=True)
        return orig(model, prefix, codec, seed, **kw)

    nar_mod.synthesize = guarded
    nar_mod._luy_guarded = True


def _guard_pipeline_stages(pipe):
    """在重显存阶段前清缓存（pipeline.__call__ 内部会调用这两个方法）。"""
    if getattr(pipe, "_luy_guarded", False):
        return pipe
    _install_nar_guard()
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


# ═══════════════════════════ 引擎封装 ═══════════════════════════

def _yue2_modules():
    """惰性导入 yue2（避免拖慢 ComfyUI 启动）。"""
    from yue2.modeling_yue2 import YuE2Config, YuE2ForCausalLM
    from bitsandbytes.nn import LinearNF4, Params4bit
    from safetensors.torch import safe_open
    return YuE2Config, YuE2ForCausalLM, LinearNF4, Params4bit, safe_open


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

    modeling.YuE2ForCausalLM = _Stub
    _STATE["stub_installed"] = True


def unload_model():
    """卸载全部 YuE2 模型与管线，释放显存。"""
    n = len(_STATE["pipelines"])
    _STATE["pipelines"].clear()
    _STATE["model"] = None
    _STATE["variant"] = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("[Luy-YuE2] unloaded (%d pipelines)" % n, flush=True)
    return n


def get_pipeline(model_variant, vae_choice, log=lambda m: None):
    """获取（或构建并缓存）YuE2Pipeline。"""
    key = (model_variant, vae_choice)
    cached = _STATE["pipelines"].get(key)
    if cached is not None:
        return cached

    model_dir = _resolve_model_dir(model_variant)
    vae_dir = _resolve_vae(vae_choice)

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
                "model_variant": (scan_model_variants(),),
            }
        }

    RETURN_TYPES = ("YUE2_MODEL",)
    RETURN_NAMES = ("yue2_model",)
    FUNCTION = "load"
    CATEGORY = "luy/音乐"
    DESCRIPTION = ("加载 YuE2 音乐生成模型（NF4）。首次加载约 3 分钟，之后进程内缓存复用。\n"
                   "模型放在 ComfyUI/models/YuE2/models/<变体>/，VAE 自动从 models/YuE2/vae/ 加载。")

    def load(self, model_variant):
        vae = default_vae()
        pipe = get_pipeline(model_variant, vae, log=lambda m: print(f"[Luy-YuE2] {m}", flush=True))
        return (pipe,)


# ═══════════════════════════ 节点 2：生成音乐 ═══════════════════════════

class CJYuE2Generate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            # 必调参数（按使用频次排序）: 模型 → 风格 → 歌词
            "required": {
                "model": ("YUE2_MODEL",),
                "style": ("STRING", {
                    "default": "English, warm piano pop, expressive female voice, acoustic piano, "
                               "rounded bass and light drums, lyrical memorable melody, unhurried phrasing, 88 BPM",
                    "multiline": True,
                    "placeholder": "风格标签（乐器/人声/节奏/BPM）",
                }),
                "lyrics": ("STRING", {
                    "default": "[Verse]\n...\n\n[Chorus]\n...",
                    "multiline": True,
                    "placeholder": "歌词，支持 [Verse]/[Chorus]/[Bridge]/[Outro] 等结构标签",
                }),
            },
            # 可选参数（由常用到少用），seed 固定在最后
            "optional": {
                "cot": (["full", "melody", "off"], {
                    "tooltip": "生成模式：full=自动规划乐谱（默认，一般无需修改）；melody=配合 abc_text 用；off=跳过乐谱规划",
                }),
                "cfg_scale": ("FLOAT", {"default": -1.0, "min": -1.0, "max": 20.0, "step": 0.05,
                                        "tooltip": "一般无需修改：-1=自动（等效不做 CFG）；>1 启用符号 CFG 且耗时翻倍"}),
                "abc_text": ("STRING", {"default": "", "multiline": True,
                                        "tooltip": "外部 ABC 乐谱（可选）；非空时需 cot=melody/full"}),
                "abc_max_tokens": ("INT", {"default": 4096, "min": 64, "max": 8192, "step": 64,
                                           "tooltip": "ABC 规划长度上限；仅当状态栏出现 truncated.abc=true 时调大"}),
                "semantic_max_tokens": ("INT", {"default": 9000, "min": 64, "max": 16000, "step": 64,
                                                "tooltip": "语义 token 上限（≈歌曲时长）；仅当 truncated.semantic=true 时调大"}),
                "advanced_sampling_json": ("STRING", {"default": "", "multiline": False,
                                                      "tooltip": '（实验用）JSON 覆盖采样参数，如 {"abc":{"temperature":0.8},"semantic":{"top_k":80}}'}),
                "seed": ("INT", {"default": 831001, "min": 0, "max": 2**63 - 1,
                                 "tooltip": "同一套参数换种子可出不同版本"}),
            },
        }

    RETURN_TYPES = ("AUDIO", "STRING",)
    RETURN_NAMES = ("audio", "info",)
    FUNCTION = "generate"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = False
    DESCRIPTION = ("YuE2 音乐生成：风格+歌词 → ABC 乐谱 → 语义 token → 流匹配 → VAE → 48kHz 立体声。\n"
                   "单次生成约 3-6 分钟（8GB 卡）。")

    def generate(self, model, style, lyrics, cot="full", cfg_scale=-1.0,
                 abc_text="", abc_max_tokens=4096, semantic_max_tokens=9000,
                 advanced_sampling_json="", seed=831001):
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

        pbars = {}
        total_by_phase = {"abc": int(abc_max_tokens), "semantic": int(semantic_max_tokens)}

        def on_token(phase, token):
            if phase not in pbars:
                pbars[phase] = ProgressBar(total_by_phase.get(phase, 4096))
            pbars[phase].update(1)

        t0 = time.time()
        try:
            song = model(style=style, lyrics=lyrics,
                         abc_sampling=abc_over, semantic_sampling=sem_over,
                         cancelled=_cancelled, on_token=on_token, **req_kwargs)
        except InterruptedError:
            import nodes as comfy_nodes
            raise comfy_nodes.InterruptProcessingException()

        arr = np.asarray(song.audio)
        if arr.ndim == 2 and arr.shape[1] <= 8:  # (T, C) 帧×声道 → (C, T)
            arr = arr.T
        waveform = torch.from_numpy(np.ascontiguousarray(arr)).float().unsqueeze(0)  # (1, C, T)
        audio = {"waveform": waveform, "sample_rate": int(song.sample_rate)}
        seconds = len(song.audio) / song.sample_rate
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
    RETURN_NAMES = ("status",)
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
