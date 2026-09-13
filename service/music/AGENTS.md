# CJ-Nodes 音乐服务（service/music）

两个节点文件、5 个节点：YuE2 音乐生成（3 个）+ SheetSage2 音频扒谱（2 个）+ 音乐风格标签（1 个）。

## 文件职责

- `music_style_nodes.py` —— 风格标签选择器（1 个节点类 + `style_tags/` 词表目录）。
  纯 os/re 实现，**不依赖 torch/folder_paths**，可脱离 ComfyUI 单测（`python -c` 直接调 `build()`）。
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
- **新增模型/VAE 后不需要重启**：实测 `folder_paths.get_filename_list` 带 **mtime 失效检查**
  （见 `folder_paths.py: cached_filename_list_`）：同目录新增文件、新增/删除子目录都会立刻反映，
  只需按 F5 刷新页面（重新拉 `/object_info`）。以前写的“必须重启”过于保守（重启当然也行）。
- VAE 不向用户暴露，`default_vae()` 自动取第一个合法项（优先根目录）。

## 节点

| 类名 | 显示名 | 说明 |
|---|---|---|
| `CJYuE2ModelLoader` | Luy-YuE2音乐模型加载 | 输出 `YUE2_MODEL`；首次约 160-200s，之后进程级缓存。**新增可选输入「前置依赖」(*)：把扒谱节点的输出接进来可强制“先扒谱、后加载”**（见下文“执行顺序”一节） |
| `CJYuE2Generate` | Luy-YuE2音乐生成 | 输出 `AUDIO`（48kHz 立体声）+ `STRING` 状态；接 SaveAudio |
| `CJYuE2Unload` | Luy-YuE2卸载模型 | 释放显存；**必须在独立工作流单独运行**（与生成节点同流会先卸载再生成的顺序不确定） |
| `CJSheetSage2Transcribe` | Luy-SheetSage2扒谱 | 音频 → 两版 ABC + style_hint + 调性/和弦/结构/MIDI；8GB 卡约 2.7GB 显存、5 分钟歌约 26s |
| `CJSheetSage2Unload` | Luy-SheetSage2卸载模型 | 释放扒谱模型显存（扒谱节点默认 【转写完释放显存】=开，一般用不到） |
| `CJMusicStyleTags` | Luy-音乐风格标签 | 15 个分类下拉共 356 选项，中英对照、输出纯英文；接生成节点的 style |

生成节点参数（控件顺序 = 必调在前，seed 固定在最后）:

- required: `model` → `style` → `lyrics`
- optional: `cot` → `cfg_scale` → `abc_text` → `abc_max_tokens` → `semantic_max_tokens` → `advanced_sampling_json` → `seed`
- ComfyUI 界面控件顺序 = required 全部在前 + optional 按声明顺序，所以“seed 排最后”必须把 seed 放进 optional 末尾（实测可行：前端仅按控件名 `seed`/`noise_seed` 决定是否加“随机/固定/递增”按钮，与 required/optional 无关）。
- 生成节点的 `风格` / `歌词` / `乐谱ABC` 全部 **`multiline: False`**（单行）：多行 textarea 在界面上**不显示字段名**，两个大文本框分不清哪个是风格哪个是歌词；单行才能看到标签。歌词默认值也由多行改成单行 `[Verse] ... [Chorus] ...`。不要再改回多行；若日后既要长歌词又要标签，只能走前端 JS 覆盖 label，不要动 `multiline`。
- `song_id` 已从节点移除（内部固定 `id="song"`）：它只影响 `result.json` 的 identity 指纹，**不影响音频**（RNG 只由 `seed` 决定），属永不需要用户调整的参数。
- `advanced_sampling_json` 可覆盖 temperature/top_p/top_k/repetition_penalty/penalty_window/min_tokens。
- **时长控制**：节点没有时长参数；时长 ≈ 歌词行数 × (330 ÷ BPM) 秒（1 语义 token = 40ms，25 帧/秒）。`semantic_max_tokens` 只是 360 秒上限的保险丝（调大不会让歌变长），`seed` 会带来 ±6% 长度波动。

## 桩（stub）与真类缓存（2026-09 修复 `_Stub` has no attribute `_from_config`）

- 背景：`_install_stub()` 把 `yue2.modeling_yue2.YuE2ForCausalLM` 换成 `_Stub`，目的是让
  `YuE2Pipeline._load_model()`（内部 `from .modeling_yue2 import YuE2ForCausalLM`，运行时解析模块属性）
  复用已建好的 NF4 权重，而不是重读一遍。
- **坑**：旧的 `_yue2_modules()` 写的是 `from yue2.modeling_yue2 import YuE2ForCausalLM`，
  读的也是模块属性 → 首次加载成功后拿到的是 `_Stub` → **第二次**建模型（换 `模型变体`、
  被同级节点请让显存后自动重建、或插件热重载后 `_STATE` 清空）直接报
  `type object '_Stub' has no attribute '_from_config'`。
- **修法**：`_install_stub()` 把真类存到 `modeling._REAL_YuE2ForCausalLM`，`_yue2_modules()` 优先取它。
  存在**引擎模块**上（不是 `_STATE`）是故意的：插件热重载会重建本节点模块与 `_STATE`，
  而引擎模块留在 `sys.modules` 里，这样重建路径仍然拿得到真类。
- 因此：**桩只接管 `from_pretrained`，必须保持它是桩**（pipeline 那条路径靠它）；
  任何新建模型/`_from_config` 的地方都要用 `_yue2_modules()` 返回的类，不要直接 `from yue2.modeling_yue2 import`。
- 升级运行中修好这段代码后**必须重启 ComfyUI**（热重载不够）：老进程里引擎模块已被旧版 `_install_stub`
  打过补丁且没有 `_REAL_` 属性，只能重启才能拿回真类。

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

## 界面参数名（已全部中文化，2026-09）

三个节点文件的**界面参数名/输出名都是中文**（`INPUT_TYPES` 的键就是中文），函数签名同步用中文参数，
函数体开头用一行别名映回英文局部名（保持原有逻辑不动）。**内部 API / 模型层仍用英文**：
`transcribe()` 的 `melody_only`/`dtype`、`SongRequest` 的 `cot`/`abc`/`seed`、`extra_tags` 等。

| 界面名（中文） | 内部名 | 说明 |
|---|---|---|
| 扒谱模型 / 音频 | `sheetsage2_model` / `audio` | 扒谱节点必填 |
| 去和弦存档 | `melody_only` | 只影响落盘产物 |
| 计算精度 / 处理时长上限 / 提示词预设 | `dtype` / `max_seconds` / `preset` | |
| 窗口重叠秒数 / 窗口前瞻秒数 | `overlap_seconds` / `lookahead_seconds` | -1=模型默认 |
| 转写完释放显存 | `release_after` | 默认开 |
| 旋律谱ABC / 完整谱ABC / 风格底稿 | `abc_melody` / `abc_full` / `style_hint` | 扒谱节点输出 |
| 调性 / 速度BPM / 和弦 / 曲式结构 | `key` / `tempo` / `chords` / `structure` | |
| 产物目录 / 扒谱信息 | `midi_dir` / `info` | |
| 音乐模型 / 模型变体 | `model` / `model_variant` | YuE2 加载与生成 |
| 风格 / 歌词 | `style` / `lyrics` | |
| 生成模式 / CFG强度 / 乐谱ABC | `cot` / `cfg_scale` / `abc_text` | cot 与 ABC 版本要配对 |
| ABC最大长度 / 语义最大长度 / 高级采样JSON / 随机种子 | `abc_max_tokens` / `semantic_max_tokens` / `advanced_sampling_json` / `seed` | |
| 音频 / 生成信息 / 状态 | `audio` / `info` / `status` | |
| 语种…年代制作 / BPM / 补充标签 / 分隔符 | 词表文件名中文部分 / `BPM` / `extra_tags` / `delimiter` | 风格标签节点 |

> 改界面名时会同时影响**已有工作流**：ComfyUI 按名字对位参数，改了名旧工作流的控件值可能回退默认。

> 反向症状：插件若已改成中文名（如 `abc_text` → `乐谱ABC`）但用户“看不到字段”，几乎总是**进程未重启 / 浏览器未硬刷新**（画布上还是旧定义，显示英文旧键名或旧字段数）。先重启 + Ctrl+F5，再怀疑代码。
> 已同步重建 `D:/AI/Yue3B/Yue2音乐生成-翻唱-4.json`（可用 `verify_workflow_names.py` 校验一致性）。

## 参数与输出

- required：`扒谱模型`（下拉，取自 `models/YuE2/models/SheetSage2`）→ `音频`（ComfyUI AUDIO，核心 LoadAudio 即可）。
- optional：`去和弦存档`(F) → `计算精度`(bf16/fp32) → `处理时长上限`(0=整首) → `提示词预设`(default/paper) →
  `窗口重叠秒数`(-1=自动,200s) → `窗口前瞻秒数`(-1=自动,100s) → `转写完释放显存`(默认 True)。
- 输出：`abc_melody` `abc_full` `style_hint` `key` `tempo`(FLOAT) `chords` `structure` `midi_dir` `info`。
- **翻唱到底用哪个输出**（用户反复问过）：主线是 `abc_melody` + `cot=melody`（官方推荐，伴奏自由）；`abc_full` + `cot=full` 是“保留原曲和声”的备选；`cot=off` 而传了 ABC 会 **抛 ValueError**（`protocol.py:99`，不是静默忽略）。辅助输出里真正影响成曲的是 `style_hint`（接 style）+ `tempo`（算歌词行数）；`chords` 只给人看 —— YuE2 **没有独立和弦输入口**，和弦只能随 `abc_full` 进去；`midi_dir`/`info` 供人工查阅。
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

---

# 音乐风格标签节点（service/music/music_style_nodes.py）

给 YuE2 拼 `style` 的点选式多选器：**显示中英对照、输出纯英文**。

## 为什么是"分类 + 槽位下拉"而不是真正的多选控件

ComfyUI 原生 COMBO 是单选，多点选只有三条路：① N 个槽位下拉；② 自定义前端标签云面板；
③ 纯文本框手打。选 ① 的理由：真实 style 写法里每个类别的标签数是有规律的（乐器 3、情绪 3、
流派 2、音色质地 2、其余 1），槽位化正好贴合；而且**零前端依赖**（前端 JS 挂了节点仍可用）。
② 的接口已预留：前端面板将来把结果写进 `extra_tags` 即可，后端不用改。

## 词表（词表驱动，加文件即加类别）

- 目录：`service/music/style_tags/`，文件名 `NN-key-中文名.txt`（可加 ` x3` 指定槽位数）。
- 一行一条，`#` 开头为注释；格式 `中文 | English`（分隔符也支持 `##`、`｜`）。
- 当前 9 类共 355 条：语种21 / 流派68 / 人声类型31 / 音色质地38 / 唱法30 / 乐器66 / 情绪45 / 节奏31 / 年代25。
- 槽位：`instruments` 3、`mood` 3、`genre` 2、`timbre` 2，其余 1（改 `_SLOTS` 或文件名尾 ` xN`）。
- **界面控件名 = 文件名的中文部分**（`_slot_labels()` 统一生成，`INPUT_TYPES` 与 `build()` 共用）：
  `3-vocal_type-人声类型.txt` → 控件名「人声类型」；多槽位自动加序号 →「乐器1/乐器2/乐器3」。
  所以**改文件名就能改界面标签**，加文件就多一个中文下拉，不用改代码。重名时自动补 key 以区分。
- **输出只取英文**：先按"中文占比最低"取段，再 `_CJK` 正则兜底剥离 —— 即使词表写错、
  或用户往「补充标签」里粘中文，输出也不会残留中文（有单测覆盖）。

## 关键设计

- **顺序由类别决定，不受点击/槽位顺序影响** → 同一组选择永远得到同一串文本，A/B 可复现。
- 跨类别去重（保留首次出现）；空项/"（不选）"忽略。
- 界面全中文：15 个分类下拉（语种 / 流派1-2 / 人声类型 / 音色质地1-2 / 唱法技巧 / 乐器1-3 /
  情绪氛围1-3 / 节奏编曲 / 年代制作）+ 「BPM」「补充标签」「分隔符」。
- 7 路输出（名为中文，括号内为内部标识）：`风格 (style)`（完整，含 BPM）+ `人声 (voice)`
  （人声三要素）+ `乐器 (instruments)` + `情绪 (mood)` + `其他 (backing)`（语种/流派/节奏/年代
  + 用户新增类别）+ `补充 (extra)`（手写补充，**不混进任何类别分组**）+ `速度 (bpm_text)`。
  分组输出用于"只换人声"这类对照实验。
- **BPM 冲突警告**（与扒谱节点合用必读）：`style_hint` 已含准确 BPM，若本节点「BPM」也填了值，
  合并后会出现两个 BPM。所以「BPM」默认 **0**（不输出）；要自己定速才填，或断掉 style_hint。
- 预置在 `翻唱-4.json` 里的接法：`style_hint → 合并.text1`、`本节点.风格(style) → 合并.text2`
  （BPM 保持 0），合并 → 生成.style。进阶：把「人声/乐器/情绪/其他/补充」分别接 StringMergeDeal
  的 5 个槽（共 8 槽），就能单独替换任一组。

---

# 生成进度显示（百分比 / 预计剩余时间）

yue2 引擎自带的 `Progress`（`yue2/progress.py`）在「总量未知」时**刻意不给百分比**——`Planning score`
与 `Generating song` 两阶段都是如此（其设计文档说"a generation limit is not a progress target"），
所以控制台只能看到 token 数与 tokens/s。节点补了一层估算：

- 位置：`yue2_music_nodes.py` 的 `_JobProgress` 类 + `_ACTIVE_JOB` 全局槽
- **估算依据**（项目内实测标度；改了要同步这张表）：

  | 阶段 | 总量估算 | 预估耗时 |
  |---|---|---|
  | 规划乐谱(ABC) | 音频秒数 × BPM × 0.13（经验值） | 总量 ÷ 8 token/s |
  | 语义生成 | 音频秒数 × 25（1 token = 40ms） | 总量 ÷ 10 token/s |
  | 流匹配(NAR) | `ode_steps`（**精确**，默认 32） | 幂律 `0.00475 × 帧数^1.417`（实测点 1500/3000/6000/9000 帧 → 150/336/992/1900 s） |
  | VAE 解码 | `ceil(帧数 ÷ vae_core_frames)`（**精确**） | 每块 1 s |

  - 音频秒数 ≈ 歌词有效行数 × 330 ÷ BPM；BPM 从风格文本里解析（缺省 88）
  - `ode_steps` / `vae_core_frames` 由节点从 pipe 上读取后传入
- **整体百分比 = 按预估耗时加权的各阶段进度之和**。刻意**不用** `已用 ÷ (已用 + 估算剩余)`：后者会因
  实测速率重估而**倒退**（实测出现 70% → 66% → 64%）。加权求和由构造上保证单调不降。
- ETA（预计剩余）：某阶段一开始就改用**该阶段的实测速率**外推；起步 3 秒内或进度 <2% 时仍用预估，
  避免"322638 token/s"这种瞬间速率失真。
- 输出渠道：
  - 控制台每 **5 秒**一行：`整体 42% | 语义生成 640/3300 token (19%) 7.6 token/s | 已用 3分12秒 | 预计剩余 14分45秒`
  - ComfyUI 进度条：`ProgressBar.update_absolute(整体百分比, 100)`（内部自带节流，百分比变化才发）
  - 阶段切换打印 `▶ 阶段 n/4 …` / `✓ 阶段 … 完成：… | 用时 …（预估值 …）`
  - 结束打印：`全部完成：音频 …s | 实际总耗时 …（事前预估 …，实际比预估快/慢 …%）`
  - 产物对比行：`NAR/VAE` 的速率显示为「秒/步、秒/块」，token 阶段显示「token/s」
- **钩子（改引擎时注意）**：
  - ABC / 语义：直接用节点已有的 `on_token(phase, token)`（phase = `"abc"` / `"semantic"`）
  - NAR：`_install_nar_guard()` 包装 `yue2.nar.synthesize` 时**链式**挂 `on_progress`
    （引擎自己的回调照旧先调用，互不干扰）
  - VAE：`_install_vae_progress()` 包装 `YuE2VAE.decode_tiled`
  - 两者都是**进程级一次性打桩**（`_luy_guarded` / `_luy_vae_hooked` 标记），
    当前任务通过 `_ACTIVE_JOB["job"]` 传递，生成结束（finally）即清空
- **校准**：若实测速率与经验值（8 / 10 token/s）偏离大，改 `_RATE_ABC` / `_RATE_SEMANTIC`；
  ABC 总量系数改 `_ABC_TOKENS_PER_BPM_SECOND`；NAR 曲线改 `_nar_seconds_estimate()`

---

# 显存互斥：8GB 卡上 YuE2 与扒谱不能同时常驻（2026-09 OOM 修复）

**症状**（用户实测）：加载器先跑（YuE2 NF4 常驻 2.1GB），再跑扒谱节点 → 转写中途炸：

```
[ERROR] CUDA out of memory. Tried to allocate 236.00 MiB.
        GPU has 8.00 GiB of which 507.75 MiB is free. 6.00 GiB allowed
挂栈: generation_sheetsage2.py:188 model.encode(audio)
      → modeling_mert2.py:66  spectrum = self.spectrogram(waveform.float())
```

**根因**：ComfyUI 给本进程的额度是 **6GB**（日志里的「6.00 GiB allowed」= 8GB 卡留约 2GB 给显示）；
而 YuE2(2.1GB) + 扒谱(峰值 ~3.4GB) ≈ 5.5GB，再要 236MB 的 STFT 缓冲就撞顶。
扒谱节点的 `release_after` 只在转写**之后**释放，救不了转写过程本身。
（另外：`_STATE` 里的旧 `unload_model()` 只清缓存，**pipeline 自己还持有 `_model`/`_vae` 引用**，
模型其实没被释放 —— 这个坑也一并修了。）

**修法：两侧无条件互斥**

- `sheetsage2_music_nodes.get_model()` 加载前调 `_free_sibling_models(keep, log)` → 卸掉 YuE2 的模型
- `yue2_music_nodes.get_pipeline()` 加载前同理 → 卸掉扒谱的模型
- 对方模块通过 `sys.modules["cj_nodes_yue2_music_nodes" / "cj_nodes_sheetsage2_music_nodes"]` 查找
  （模块名由 CJ-Nodes 的 loader 规则 `cj_nodes_<文件名>` 决定），再调其 `unload_model()`
- ⚠️ **2026-09 复查发现上面这条一直是死代码**：CJ-Nodes 的 `load_nodes_from_file` 用
  `module_from_spec + exec_module` 加载节点文件，而这条路径**不会**把模块写进 `sys.modules`
  （只有 `import` 语句才会），所以 `sys.modules.get(...)` 永远拿到 `None` → 互斥静默失效 →
  加载器先跑时 OOM 依旧。`test_vram_guard.py` 之所以通过，是因为它自己手动
  `sys.modules[spec.name] = module` 并造了假模块，绕过了真实运行时。
- **修法（已在 `CJ-Nodes/nodes.py` 落地）**：`load_nodes_from_file` 在 `exec_module` 前
  `sys.modules[module_name] = module`（失败则 pop），与标准 import 行为一致。
  回归测试：`D:/AI/Yue3B/test_node_module_registry.py`（未注册→失效 / 注册→双向真卸载 / 静态守护注册先于 exec）。
- **为什么不做“显存够不够”的判断**：`torch.cuda.mem_get_info()` 返回的是**设备**空闲量，看不出
  **进程额度**快满（本次 OOM 就是额度问题，设备当时还有 507MB 但额度已用完）。与其猜，不如直接互换：
  重载 25-30s ≪ 一次 OOM 白跑 20 分钟。对方本来没加载模型时 `unload_model()` 是空操作，
  所以单独跑任一节点完全不受影响。

**配套：可自动重建**

- `yue2_music_nodes.unload_model()` 现在会先断开 `pipe._model` / `pipe._vae` 再清缓存（真正释放显存）
- `_STATE["last"]` 保留 `(variant, vae)`；生成节点发现 `_pipeline_alive(model)` 为假时按它自动重建，
  日志会打印 `模型已被显存回收，正在重新加载（约 25-30s）…`
- 因此「一条工作流跑完 扒谱 → 生成」仍然可行，代价是切换到生成时多 25-30s 重载

**回归测试**：`D:/AI/Yue3B/test_vram_guard.py`
（互斥方向、未加载时的空操作、真释放、`_pipeline_alive` 判定、重建参数保留）

**给用户的备选做法**：把「Luy-YuE2音乐模型加载」+「生成」分支临时 Mute（Ctrl+M）单独跑一次扒谱，
再取消 Mute 跑生成 —— ComfyUI 会复用已缓存的 ABC/style，不重跑扒谱，也完全不占双份显存。

---

# 执行顺序：为什么加载器总是抢在扒谱前面（2026-09 追加）

**症状**：同一条流里，YuE2 加载（2.1GB）先跑，扒谱随后加载 → 撞 6GB 额度 OOM；用户观感是“顺序随机”。

**其实不是随机，是调度器的启发式（`comfy_execution/graph.py: ux_friendly_pick_node`）**：

1. 两个分支之间没有任何数据依赖（加载器的唯一输入是 widget），都可执行；
2. 选先后的规则是“优先跑 2 跳内能到 `OUTPUT_NODE` 的节点”：
   加载 → 生成 → SaveAudio = **2 跳（被优先）**；扒谱 → 拼接 → 生成 → SaveAudio = **3 跳（不被优先）**；
3. 于是只要两者同时就绪，**加载器必赢**（`test`/实测模拟：`D:/AI/Yue3B/sim_order.py`）。
   初始 pendingNodes 顺序受 `execute_outputs` 这个 **set** 的迭代顺序影响（随 `PYTHONHASHSEED` 变化），
   但两跳优先级足以覆盖该差异 → 结论稳定。

**修法：给加载器加一条真实依赖边（顺序闸门）**

- `CJYuE2ModelLoader` 新增可选输入 **`前置依赖` (`"*"` + `forceInput`)**，接线后
  `blockCount[加载器] ≥ 1`，拓扑排序**保证**扒谱（含 `release_after` 释放显存）跑完才加载 YuE2。
- 不接线时行为与原来一致（老工作流不受影响，`load(..., 前置依赖=None)` 有默认值）。
- 实测（`sim_order.py`）：接线后 4 种组合（两种 `execute_outputs` 顺序 × 两种输入键序）全部
  `扒谱 → 拼接 → 加载 → 生成`。
- Mute 扒谱不会报错：前端 `graphToPrompt` 末尾会主动删掉指向不在 prompt 里的节点的连线
  （`!a[n[0]] && delete e[t]`，已在前端 1.52.7 打包产物中确认）。
- 接线后控制台会打印 `[Luy-YuE2] 前置依赖已就绪（扒谱完成），开始加载模型`，可作为顺序验证点。
