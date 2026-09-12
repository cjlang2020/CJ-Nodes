# CJ-Nodes 音乐服务（service/music）

两个节点文件、5 个节点：YuE2 音乐生成（3 个）+ SheetSage2 音频扒谱（2 个）。

## 文件职责

- `yue2_music_nodes.py` —— YuE2 生成（引擎封装 + 3 个节点类）。
  - 引擎位置：`CJ-Nodes/libs/yue2/` —— **内置引擎快照**（从 `D:\AI\Yue3B\src\yue2` 复制的 yue2 包，v0.1.6，14 个 .py）。
  - 节点默认 `_YUE2_SRC = <CJ-Nodes>/libs`，可用环境变量 `YUE2_SRC` 覆盖。
  - 升级引擎：`cp D:/AI/Yue3B/src/yue2/*.py <CJ-Nodes>/libs/yue2/` 后重启 ComfyUI（先清 `__pycache__`）。
  - **引擎不能放在 service/ 下**：nodes.py 递归加载 service/ 内所有 .py（不识别包），包内模块会被当节点文件执行并报 `attempted relative import with no known parent package`。
- `sheetsage2_music_nodes.py` —— SheetSage2 扒谱（2 个节点类）。**无需内置引擎**：推理代码由 transformers 的
  `trust_remote_code` 从模型目录（`models/YuE2/models/SheetSage2/`）动态加载，节点本体只依赖 torch/numpy/folder_paths。
- 显示名注册在 `CJ-Nodes/nodes.py` 的 `CUSTOM_DISPLAY_NAMES`（模块内的 `NODE_DISPLAY_NAME_MAPPINGS` 会被节点加载器忽略）。
- 5 个节点的 `CATEGORY` 统一为 `luy/音乐`（本项目惯例：`luy/中文分类`，如 `luy/模型加载`、`luy/图片处理`）。

## 模型目录（全部相对路径，无硬编码绝对路径）

- 通过 `folder_paths.add_model_folder_path` 注册三个类型：
  - `YuE2` → `ComfyUI/models/YuE2/models`（一级子目录 = 变体名，如 `nf4`）
  - `YuE2_VAE` → `ComfyUI/models/YuE2/vae`（根目录或子目录均可）
  - `SheetSage2` → 同一路径 `ComfyUI/models/YuE2/models`（只用于**独立**枚举扒谱模型，互不干扰）
- 枚举走 `folder_paths.get_filename_list`，解析走 `folder_paths.get_full_path`；下拉值与缓存键都是相对名（如 `nf4`、`(根目录)`）。
- **`models/YuE2/models` 下同时住着三种模型**，必须靠专属文件区分（踩坑记录）：

  | 目录 | 用途 | 专属文件 |
  |---|---|---|
  | `nf4/` | YuE2 生成模型 | `modeling_yue2.py`、`qwen.tiktoken` |
  | `SheetSage2/` | 扒谱适配器 + 推理代码 | `modeling_sheetsage2.py` |
  | `MERT-v2-FullSong/` | 扒谱编码器 backbone | `modeling_mert2.py`、`configuration_mert2.py` |

  `scan_model_variants()` 要求同时满足「有 YuE2 专属文件」且「无扒谱专属文件」，否则
  SheetSage2 / MERT 会出现在 YuE2 生成节点的模型下拉里（旧逻辑实测会返回
  `['MERT-v2-FullSong', 'SheetSage2', 'nf4']`，修复后为 `['nf4']`）。
- **新增模型/VAE 后必须重启 ComfyUI（或点“重载插件”）**（folder_paths 列表启动时构建）。
- VAE 不向用户暴露，`default_vae()` 自动取第一个合法项（优先根目录）。

## 节点

| 类名 | 显示名 | 说明 |
|---|---|---|
| `CJYuE2ModelLoader` | Luy-YuE2音乐模型加载 | 输出 `YUE2_MODEL`；首次约 160-200s，之后进程级缓存 |
| `CJYuE2Generate` | Luy-YuE2音乐生成 | 输出 `AUDIO`（48kHz 立体声）+ `STRING` 状态；接 SaveAudio |
| `CJYuE2Unload` | Luy-YuE2卸载模型 | 释放显存；**必须在独立工作流单独运行**（与生成节点同流会先卸载再生成的顺序不确定） |
| `CJSheetSage2Transcribe` | Luy-SheetSage2扒谱 | 音频 → 两版 ABC + style_hint + 调性/和弦/结构/MIDI；8GB 卡约 2.7GB 显存、5 分钟歌约 26s |
| `CJSheetSage2Unload` | Luy-SheetSage2卸载模型 | 释放扒谱模型显存（扒谱节点默认 `release_after=True`，一般用不到） |

生成节点参数（控件顺序 = 必调在前，seed 固定在最后）:

- required: `model` → `style` → `lyrics`
- optional: `cot` → `cfg_scale` → `abc_text` → `abc_max_tokens` → `semantic_max_tokens` → `advanced_sampling_json` → `seed`
- ComfyUI 界面控件顺序 = required 全部在前 + optional 按声明顺序，所以“seed 排最后”必须把 seed 放进 optional 末尾（实测可行：前端仅按控件名 `seed`/`noise_seed` 决定是否加“随机/固定/递增”按钮，与 required/optional 无关）。
- `song_id` 已从节点移除（内部固定 `id="song"`）：它只影响 `result.json` 的 identity 指纹，**不影响音频**（RNG 只由 `seed` 决定），属永不需要用户调整的参数。
- `advanced_sampling_json` 可覆盖 temperature/top_p/top_k/repetition_penalty/penalty_window/min_tokens。
- **时长控制**：节点没有时长参数；时长 ≈ 歌词行数 × (330 ÷ BPM) 秒（1 语义 token = 40ms，25 帧/秒）。`semantic_max_tokens` 只是 360 秒上限的保险丝（调大不会让歌变长），`seed` 会带来 ±6% 长度波动。

## 加载耗时剖析（2025-09 实测，已优化）

- **根因**：transformers 的 `_from_config` 内部**不含** `no_init_weights()`（只有 `from_pretrained` 有），因此默认构造会对 34 亿参数做一次完整 `nn.init.normal_` 随机初始化 —— 实测 **153.8s**，而这些权重随后会被 safetensors 全部覆盖，纯属浪费。
- **修法**：`with torch.device("meta"): model = YuE2ForCausalLM._from_config(config)`（实测 0.07s，627 参数 + 1 buffer 全为 meta，无内存分配、无初始化）；再用 `safe_open(..., device="cuda")` 让 mmap 直接拷入显存（省 CPU 中转）；最后断言无残留 meta 张量（有则前向会静默输出垃圾）。
- **效果**：首次加载 160-200s → **30.2s**（其中模型构建 9s、管线构建含 3GB 文件 sha256 校验 2.6s）。
- **权重正确性验证**（必做）：`embed_tokens` / `lm_head` 与 safetensors **位精确相等**，NF4 层打包 uint8 位精确相等且可反量化，无残留 meta。
- 平台事实：`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` **在 Windows 不被支持**（仅告警并被忽略），不要据此解释显存行为。

## 时长 → 总耗时估算（实测参数，2025-09）

各阶段实测标度（把此当基准，不要凭直觉猜）：

| 阶段 | 实测 |
| ---- | ---- |
| 加载 | 21s（一次性） |
| 计划 (ABC) | 17.6 tok/s；abc token 数 ≈ 22.5 × 小节数 ≈ 8.25 × 目标秒数（88 BPM） |
| 语义 (AR) | 17.6 tok/s（前缀 2600 下实测，长序列未见明显衰减）；帧数 = 秒数 × 25 |
| **NAR 流匹配** | 每 midpoint 步：4000 帧 17.0s、6000 帧 31.0s、8000 帧 72.2s；默认 32 步 |
| VAE 解码 | 每 512 帧一个 chunk，均 ~1s |

估算结果（空闲基线，88 BPM）：

| 目标时长 | 帧数 | 计划 | 语义 | NAR | 合计 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| 1 分钟 | 1500 | 28s | 85s | ~150s | **~5 分钟** |
| 2 分钟 | 3000 | 56s | 170s | ~336s | **~10 分钟** |
| 3 分钟 | 4500 | 84s | 255s | ~670s | **~17 分钟** |
| 4 分钟 | 6000 | 113s | 360s | **~992s** | **~25 分钟** |
| 6 分钟（上限） | 9000 | 170s | 540s | ~1900s+ | **~45 分钟+** |

- 桌面 GPU 重负载时 AR 阶段降到 7.5-9.3 tok/s，上表整体 ×1.6-2.0。
- **前提：必须保持 `offload_ar=True`**。实测 `offload_ar=False` 时 6000 帧单步从 31.0s 暴涨到 **235.8s**（13 倍）—— AR 模块常驻导致触碰到 WDDM 分页（峰值 1984MB）。`_offload_ar` 会把 AR 模块（`embed_tokens/lm_head/self_attn/mlp/...`）搬 CPU，NAR 用的是独立 `nar_self_attn/nar_mlp`，互不干扰。
- 加速手段：减小 `generation_config.ode_steps`（默认 32，与 NAR 耗时成正比；节点未暴露）、缩短时长、关桌面应用。

## 长歌 OOM：NAR attention 必须分块（2025-09 实测修复）

- **根因**：本机 torch 2.10+cu130 (Windows) 的 `torch.backends.cuda.is_flash_attention_available() == False` → SDPA 回退 **math 后端并物化注意力矩阵**。`nar.py:75` 默认 `block = len(q)`（CUDA 下整块），于是：
  - AR 前缀 ~2000 token 的预填充：单层就要 **654 MiB**
  - 长歌（前缀 1900 + 3800 帧）NAR 单步：全进程峰值 **5979 MiB / 391s** → 撞 6GiB 上限 OOM（用户真实报错）
- **修法**：`nar.synthesize` 本就有 `query_chunk_size` 参数（作者为 math 回退预留），只是 pipeline 不传。节点用 `_install_nar_guard()` 包装 `yue2.nar.synthesize` 注入 `query_chunk_size=256`（pipeline 内部是 `from .nar import synthesize` 的调用时局部导入，所以改模块属性生效），并在 `_guard_pipeline_stages()` 里用实例属性覆盖 `pipe.synthesize` / `pipe.decode` 以在重显存阶段前 `gc.collect()+empty_cache()`（pipeline 无 `__slots__`，可挂实例属性）。
- **效果（实测）**：1200 帧 5320→**1126 MiB**、191→**11.4s**；3800 帧 5979→**1309 MiB**、391→**13.6s**（快 28.8 倍，对所有歌生效，不限长歌）。
- **数值影响**：因果预填充路径分块与整块**逐位相同**（max|diff|=0）；NAR 非因果路径 max|diff|≈0.73（不同 SDPA kernel 的舍入差异）。注意：未分块路径在本机本就是 math 回退，**不是权威参考**（有 flash 的机器上数值也不同），无分块会直接 OOM。
- 推论：8GB 卡上长歌（>2.5 分钟音频）在修复前必崩；修复后 3800 帧只需额外 ~1.3GB。

## 非显而易见的强制约束

- **NF4 加载必须手动注入**：`_from_config` 骨架 → 换 `LinearNF4` 槽位 → `Params4bit.from_prequantized` 注入 safetensors 全部 keys（当前 2588 个，缺 key 直接报错）；跳过 `lm_head/llm2vae/vae2llm/time_embedder/latent_pos_embed`（保持 bf16）。transformers 5.5.4 不会凭 config.quantization_config 自动重建手工量化模型。
- **主模型必须走 stub 猴子补丁**：`pipeline._load_model` 用旧 kwarg `torch_dtype=` 调 HF `from_pretrained`（transformers 5.x 已改名 `dtype`）。补丁替换 `yue2.modeling_yue2.YuE2ForCausalLM` 返回缓存模型对象，绕过该调用。VAE 侧 yue2 自带双 kwarg 防御，无需处理。
- **必须 `backend="torch-eager"`**（CUDA Graph 不能 capture bnb 内核）+ `quantization="none"`（权重已是 NF4）+ `offload_ar=True`。
- **音频轴向**：`SongResult.audio` 是 `(T, C)` 帧×声道，ComfyUI AUDIO 需 `(B, C, T)`；节点按 `arr.shape[1] <= 8` 自适应转置（写死 transpose 会得到 2972096 通道的坏波形）。
- **显存**：模型常驻约 2.1GB，ComfyUI 显存管理不感知它 → 与其它大模型工作流混用可能 OOM；出歌建议独立工作流。
- **环境**：ComfyUI 的 `python_embeded` 为 torch 2.10.0+cu130 / transformers 5.5.4 / bnb 0.49.2，**严禁升级或降级 torch/transformers/numpy**（会破坏 ComfyUI 本体）。
- 实测：加载 160-200s；生成 165-230s（约 61s 音频）；空闲 17.9 tok/s，桌面 GPU 重负载时降到 7.5 tok/s。

---

# SheetSage2 扒谱节点（service/music/sheetsage2_music_nodes.py）

音频 → 两版 ABC 乐谱 + MIDI + 调性/和弦/曲式/节拍标注，供 YuE2 做旋律复刻。

## 模型部署（已就位，均在同一 `models/YuE2/models` 下）

```
models/YuE2/models/SheetSage2/         适配器(228MB) + 全部推理代码（已打 transformers 5.x 兼容补丁）
models/YuE2/models/MERT-v2-FullSong/   编码器 backbone(2.53GB model.safetensors)，modeling_mert2.py 已打 rope 修复
```

- **backbone 路径由节点运行时解析并传入**：`AutoModel.from_pretrained(ss2_dir, base_model_path=<MERT目录>)`。
  模型代码里有 `base_path = kwargs.pop("base_model_path", None)`，所以**不用改 config.json**、完全离线。
  （SheetSage2 的 config.json 里 `base_model_name_or_path` 仍是 HF 仓库名 `m-a-p/MERT-v2-FullSong`，
  如果谁直接跑官方 CLI 会去联网找；节点路径不受影响。）
  解析顺序：环境变量 `SHEETSAGE2_MERT_DIR` → config 里仓库名的 basename 作为兄弟目录 → 兄弟目录里
  含 `modeling_mert2.py`+`model.safetensors` 的目录。
- SheetSage2 自检父目录两个代码文件 + model.safetensors 的 sha256（`BASE_CODE_HASHES` / `base_model_sha256`）。
  **改过 MERT 的 modeling_mert2.py 就必须同步更新 SheetSage2 的 `BASE_CODE_HASHES`**，否则加载直接报
  `MERT-v2 parent integrity check failed`；当前已同步（654c2b6a…）。
- 缺失依赖：本节点需要 `pretty_midi` / `mido` / `mir_eval`（模型代码顶层 import）。
  embeded 环境已装（2026-09）；`pretty_midi` 依赖 `pkg_resources`，因此 `setuptools` 必须是 78.1.1（82 已移除该模块）。

## 为什么必须打补丁：transformers 5.x 的两个坑（踩坑记录，勿删）

**坑 1：三处 API 变更（改 `modeling_sheetsage2.py`）**

| 原代码（tf 4.45） | transformers 5.x |
|---|---|
| `BartDecoder(dc, embed_tokens=...)` | 签名只剩 `(config)` → 改成构造后赋 `decoder.embed_tokens` |
| `_tied_weights_keys = ["a", "b"]` | 要求 `{target: source}` dict |
| `def tie_weights(self)` | 5.x 传 `missing_keys`/`recompute_mapping` → 改 `*args, **kwargs` 透传（两版本通用） |

**坑 2（核心、极隐蔽）：非持久 buffer `inv_freq` 被 meta 加载清空**

- `RotaryEmbedding.inv_freq` 是 `persistent=False` 的旋转位置编码频率，**不在 checkpoint 里**，
  靠 `with torch.device("cpu")` 在 `__init__` 算出来。tf 4.45 用「meta 默认设备上下文建模块」，内层 CPU 上下文生效，值是对的。
- transformers 5.x **移除了 `low_cpu_mem_usage`**（已在废弃参数列表里），改为 meta 初始化 + `to_empty()` 物化，
  且权重加载器**直接写 `module._buffers[name]`、绕过 `nn.Module._apply`** → 原代码 `_apply` 里的
  `original.to(device=…)` 对 meta 张量会丢数据 → buffer 里是**未初始化内存**（实测 sum=214651.6，正确值应为 3.9979；
  垃圾值长得像 4431/10229 这种随机字节，极易误判为“版本不兼容”）。
- 后果链：位置编码 ↔ 正确值 cosine≈0 → 编码器 24 层特征全部错位 → 长音频解码在 1500+ 步处崩坏。
  **短片段（≤30s）可能完全正常，长歌必崩**，这就是当初误判“embeded 不满足运行”的原因。
- 两层防御：① MERT 目录下的 `modeling_mert2.py` 已打补丁（`_inv_freq_cpu` 保留 Python 侧副本，
  `_apply` 与 `forward` 双重恢复并清 cos/sin 缓存）；② 节点加载后仍会跑 `_ensure_rotary_buffers()` 自检，
  发现异常就按公式重算并打印 `⚠ 已自动修复…`。**即使模型目录换成原版文件，节点也能正常出谱。**
- 排查手法（换模型/升级 transformers 后仍适用）：把同一段音频在两个环境各跑一次，比 `inv_freq.sum()`、
  memory 的 cosine/abssum；再逐层注入 h0/positions 做二分（本次就是这么定位到唯一分歧点在 `embed_positions`）。

## 一次推理 → 两版 ABC（与 YuE2 的 cot 严格配对）

YuE2 的 `protocol.py` 里 cot 语义是：`melody` = 无和弦旋律谱，`full` = 带和弦标注谱。SheetSage2 正好对应两版：

| 节点输出 | ABC 内容 | 接生成节点 |
|---|---|---|
| `abc_melody` | 无和弦符号，保留 Vocal+Ins 两条旋律 | `abc_text` + **cot=melody**（官方推荐，翻唱/复刻） |
| `abc_full` | 含和弦标注（`"Bsus2"` 等） | `abc_text` + **cot=full** |

- `melody_only` 参数只决定**落盘产物**（score.abc / MIDI 伴奏）用哪版；**两版 ABC 字符串始终同时输出**。
- 实现：主产物由 transcribe 按 `melody_only` 生成，另一版用
  `notation_sheetsage2.build_rebuilt_abc_score(<run_dir>/notation/song_*.txt|.mid, melody_only=另行指定)` 重建，
  再 `score_to_abc()` 取文本 —— 只有一次模型推理（省一半时间）。
- YuE2 对外部 ABC **不做语法校验**，只 `tokenizer.encode(abc)` 当作前缀（`pipeline.plan` 里 `request.abc` 分支），
  并要求 `cot != "off"`。约 2547 字符全曲 ABC ≈ 2000+ token 前缀，`abc_max_tokens` 对**外部 ABC 不截断**。

## 参数与输出

- required：`sheetsage2_model`（下拉，取自 `models/YuE2/models/SheetSage2`）→ `audio`（ComfyUI AUDIO，核心 LoadAudio 即可）。
- optional：`melody_only`(F) → `dtype`(bf16/fp32) → `max_seconds`(0=整首) → `preset`(default/paper) →
  `overlap_seconds`(-1=自动,200s) → `lookahead_seconds`(-1=自动,100s) → `release_after`(默认 True)。
- 输出：`abc_melody` `abc_full` `style_hint` `key` `tempo`(FLOAT) `chords` `structure` `midi_dir` `info`。
- **无 seed**：SheetSage2 是贪心解码，实测同输入逐位一致（两个独立的 venv/embeded 环境 token 级一致率 99.95%，
  唯一差异是尾奏 2 小节的等音和弦 `D:maj6` vs `B:min7/b7`，音高集合完全相同）。
- `style_hint` 是**事实型**底稿（调性/速度/拍号/和声骨架/曲式），不含流派与人声性别（模型无法推断），
  用户再补 `English, warm piano pop, expressive female voice, …` 这类标签。歌词 SheetSage2 不产出，需自行提供。
- 落盘目录：`<ComfyUI output>/SheetSage2/<时间戳>/`，含 `score.abc` `score_melody.abc` `transcription.mid`
  `melody_vocal.mid` `melody_instrumental.mid` `chords.mid` `events.json/tsv` `*.lab` `notation/` `summary.txt` `result.json`。
- **不暴露的功能**：`render_audio`/`render_score`（钢琴试听/五线谱 PDF）需要 playwright + render_assets，与 torch 无关地依赖浏览器，
  节点不掺；`export_logits/scores/embeddings`、`output_hidden_states` 是诊断用张量，扒谱→生成链路用不到；
  `prompts`（多任务提示词列表）固定用默认 6 项（timestamp/downbeat_meter/structure/key/chord_full/melody_full）。

## 实测性能（RTX 4060 Laptop 8GB，2026-09）

- 加载 6.3-8.8s（比 YuE2 快得多）；305s 全曲转写 **26s**，峰值显存 **3.24GB**；30s 片段 26s（首窗固定成本）。
- 显存足够与 YuE2 同流吗？YuE2 常驻 2.1GB + NAR 阶段再要 1.3GB；扒谱 2.7GB —— 合计接近 8GB 上限，
  所以 `release_after` 默认 True（转写完就还显存，重载仅十几秒）。

## 推荐工作流（扒谱 → 生成）

```
LoadAudio ──► Luy-SheetSage2扒谱 ──┬─ abc_melody ──► Luy-YuE2音乐生成.abc_text  （cot 设 melody）
                                   ├─ style_hint ──► Luy-YuE2音乐生成.style     （再补流派/人声/乐器标签）
                                   └─ info（看调性/结构/和弦，人工写 lyrics）
Luy-YuE2音乐模型加载 ──► Luy-YuE2音乐生成 ──► SaveAudio
```

- 歌词必须自己写（扒谱不给歌词）；`cot` 与选用的 ABC 版本要配对（melody/full）。
- 长歌提示：ABC 前缀约 2000+ token，语义阶段长度由歌词行数决定（≈ 歌词行数 × 330 ÷ BPM 秒），与扒谱时长无关。
