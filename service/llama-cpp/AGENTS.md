# llama-cpp 模块备忘（版本兼容 / 调试 / 隐藏依赖）

## 版本兼容（llama-cpp-python，JamePeng fork）

- 0.3.49 实测可用（支持 qwen35/qwen35moe 架构与 Qwen35ChatHandler）。升级包后 `llama_speculative.py` 删除了 `LlamaPromptLookupDecoding`（旧滑窗投机解码），只剩 `LlamaNGramMapDecoding`（构造签名 ngram_size/num_pred_tokens 兼容不变）。
- `base.py` 是本目录全部 6 个 py 的公共依赖（其余文件 `from base import ...`）。**base.py 顶层 import 一失败，整个 llama-cpp 域所有节点连锁加载失败**（受 nodes.py 自动加载机制影响，见上级 AGENTS.md）。
- 改投机解码相关代码必须同步改的文件：`base.py`（import + `draft_model_types` 列表 + 构造分支）+ `llamacpp.py` / `llamacpp_image.py` / `llamacpp_text.py` / `nodes.py` 中 `draft_model_type` 的 tooltip 文案（`llamacpp_lite.py` 复用列表变量无需改文案）。
- `draft_model_types` 现为 `["None", "ngram-map"]`；旧工作流里存了 `prompt-lookup` 的节点重新打开会提示值无效，需手动改为 `ngram-map`。

## 思考模式（关闭思考 / reasoning budget）

- `thinking_modes = ["auto", "off"]` 定义在 `base.py`，由 5 个推理节点复用（`llama_run` / `llama_run_simple` / `llama_run_lite` / `llama_text_simple` / `llama_cpp_instruct_adv`），新节点要加同一开关只需从 `base.py` 导入 `thinking_modes` + `output_text`。
- 关闭原理是 fork 自带、与模型无关的 `ReasoningBudgetSampler`（`create_chat_completion(reasoning_budget=0, ...)`）：一旦生成出 `<think>` 就立即强制补 `</think>`，MiniCPM5 实测 104→9 token、0.87s→0.14s。模型不用 `<think>` 标签时采样器空转（`start_max_tokens` 安全窗口）不注入任何东西，`Qwen3.5` 文本模型实测输出不变。
- 局限：handler 模板在**提示词里预插** `<think>` 的模型（如 `MiniCPM-v4.6-Thinking`），采样器处于 IDLE 计不到数，此时开关不生效，要用非 Thinking 的 handler 变体（`base.py` 会传 `enable_thinking=False`）。
- 输出侧统一走 `base.py` 的 `output_text(output, thinking)`，`off` 时清掉完整块、未闭合块以及模板预插模式留下的 `... </think>` 前缀。
- VLM 路径也支持：`llama_multimodal.py` 的 handler `__call__` 里有 `reasoning_budget` 等参数并转发给 `create_completion`，所以带 mmproj 的模型同样能用；`MiniCPM-v4.5/v4.6` 这类“模板预插 `<think>`”的仍属例外（见上）。

## 系统提示词拼接（行为约定）

- `llama_run_simple`（`系统角色提示词`）与 `llama_run`（`系统提示词`）：填写则优先使用，留空用节点内置默认角色/空，语言要求**始终**按 `中文回复` 追加。旧行为是“填写后不再追加语言指令”，会让 `中文回复` 静默失效，已修正。
- 副作用：`llama_run` 留空时现在也会生成一条只含语言要求的 system 消息（原来完全没有 system 消息）；`llama_run_simple` 拼接改用 `\n`，修掉了默认角色尾部 `。,\n` 的怪写法。
- `llama_text_simple` 与 `llama_run_lite` 没有系统角色输入（硬编码固定 system），要统一需先给它们加输入项。

## 调试："Failed to load model from file" 是误导性错误

- `Llama()` 抛出的这个错误无信息量，真实原因（显存不足 / 架构不支持 / 文件损坏）全部被 `verbose=False` 吞掉。base.py 已包装为带 Free VRAM 与修复建议的 RuntimeError；需深入排查时写独立脚本以 `verbose=True` 加载看 ggml 日志。
- 显存需求实测（8GB 卡 / RTX 4060 Laptop）：9B Q4_K_XL 全量 offload ≈ 权重 5679MB + CUDA buffer 501MB(n_ctx 8192) + mmproj 900MB ≈ **7.1GB**。ComfyUI 同跑 SD 模型时必然失败；用户侧解法：节点 `vram_limit` 设 5~6 让代码按层拆分 GPU/CPU，或先卸载已加载的 SD 模型。
- `llama_run_simple` 的 `上下文长度` 默认 **12800**，KV cache 开销按模型差异大：`2×层数×kv头数×head_dim×n_ctx×2B`（末项是 f16 的 2 字节）。MiniCPM5-2B（42层/2头/128）≈ **0.5GB**，gemma-4-E4B（42层/2头/**512**）≈ **2.0GB**；同样模型在 32720 下分别是 1.3GB / 5.2GB。含 SWA 的模型（如 gemma）实际会小一些，上面是全局注意力上界。显存吃紧时先降这个值，而不是只调 `显存限制`。
- 判断模型文件是否损坏：用 `from gguf import GGUFReader` 读元数据（注意 llama_cpp 包内没有 gguf 子模块，gguf 是独立包）。**本机 gguf 版本 API**：`reader.fields["general.architecture"].contents()` 直接返回 `str`/`int`（列表类字段才是 list），没有 `reader.get()` / `get_string()`（调用报 AttributeError），旧的“取 `[0]` 只会拿到首字符”说法已不适用。

## 节点参数/输出接线约定（llama-cpp）

- `llama_run_simple` 有 **3 个 return 路径**（`启用推理=False` 直传 / 缓存命中 / 正常推理），改返回值个数时必须三处同步（缓存里仍存 5 元组，分隔数组在返回时现算 → 改 `分隔符` 能立即生效，不被缓存卡住）。
- 采样参数 12 项属**推理期**（进 `parameters`，改它不重载模型）；`图片最小token`/`图片最大token` 属**加载期**（进 `custom_config`，改动会触发模型重载）；`上下文长度`/`显存限制` 同理。
- **`存在惩罚` 在本机是空设**：`if _MTMD: parameters.pop("presence_penalty", None)`，而本机 `_MTMD=True`（装了 MTMDChatHandler），该值永远被丢弃（完整版/简化版行为一致）。
- 参数排序规矩：按**使用频次**（模型/视觉模块/对话模板 → 提示词 → 常用行为 → 抽样微调 → 调试/加速项）；新加字段要插进对应档，不要一律追加到末尾。改顺序前先想清楚 `widgets_values` 位置化后果（见上级 AGENTS.md）。
- **用户指定、不要再改回去的默认值/位置**（`llama_run_simple`）：`思考模式=off`、`启用推理=True`、`最大生成长度=4096`、`上下文长度=12800`；`使用缓存` 紧跟在 `中文回复` 下方、`上下文长度` 紧跟在 `最大生成长度` 上方。

## 模型模板坑（实测）

- **MiniCPM-5 系列不支持列表式 content**：节点一律传 `[{"type":"text","text":…}]`，而 MiniCPM5 的 GGUF 模板把列表渲染成空 → 提示词静默丢失（现象：模型胡答/反问）。逐模型实测只有 MiniCPM-5 系列受影响（GLM-OCR/Hy-MT2/MiniCPM-V-4.6/Qwen3-VL/gemma-4/omnicoder 均正常）。验证方法：`Jinja2ChatFormatter(template="<从 GGUF 读的 tokenizer.chat_template>").render` 后看 prompt 里还有没有用户文本。
- **MiniCPM-V-4.6 handler 重复推理必崩**：同一 Llama 实例上第二次 `create_chat_completion` 报 `RuntimeError: sampling index is outside the most recent decode output batch: token_index=173`；对照实验证明与 `reasoning_budget` 无关（不传也崩）→ 是 fork 层面的 bug。`nodes.py` 里已有的 Qwen3.5 专用重置（`n_tokens=0` + `_ctx.memory_clear(True)` + is_hybrid 时清 `_hybrid_cache_mgr`）能绕过（实测两次均成功），但 hack 的 handler 名单目前只列了 Qwen3.5。

## 测试配方（无需启 ComfyUI UI）

- 把 `D:\AI\ComfyUI-Dev\ComfyUI` 加进 `sys.path` 后 `import` 节点模块（可拿到 `NODE_CLASS_MAPPINGS`），依次 `cls.INPUT_TYPES()`，再与 `inspect.signature(getattr(cls, cls.FUNCTION))` 比对键集（排除 hidden 的 `unique_id`）——能直接拓出改名/改签名后的错。
- 想验证参数到底有没有传进推理：`Llama.create_chat_completion` 打猴子补丁抓 kwargs（`def spy(self,*a,**kw): captured.update(kw); return orig(self,*a,**kw)`），比看输出猜靠谱。
- 快速确认内核是否支持某架构：在 `python_embeded/Lib/site-packages/llama_cpp/lib/*.dll` 二进制里搜架构名字符串（如 `qwen35`、`minicpm5`）。Python 一行即可：`re.findall(rb'qwen3[0-9a-zA-Z_]*', open(dll,'rb').read())`，llama.dll 命中即支持。

## 隐藏依赖：CUDA 后端靠 torch 的 DLL

- `ggml-cuda.dll` 依赖 `python_embeded/Lib/site-packages/torch/lib/` 下的 `cudart64_13.dll` / `cublas64_13.dll`（CUDA 13）。独立 Python 进程中它**静默**加载失败（backend registry 只有 CPU，`n_gpu_layers=-1` 也全跑 CPU，不报错）；只有进程内已 import torch 后 CUDA 后端才注册成功。
- 独立测试 GPU 加载必须先 `import torch` 或 `os.add_dll_directory(.../torch/lib)`。后端加载机制源码在 `site-packages/llama_cpp/llama.py` 的 `Llama.__init__`（`ggml_backend_load_all_from_path`），日志看 "Loaded ggml backend registry count"。

## 模型资产与本机环境

- 本机模型：`models/LLM/Qwen3.5/{0.8B,4B,9B}/`（9B 为 `Qwen3.5-9B-UD-Q4_K_XL.gguf` + `mmproj-BF16.gguf`）、`models/LLM/MiniCPM-5/`（1B/2B 文本 + 思维模型，GGUF `general.architecture=llama`，模板不认列表 content，见上）、`models/LLM/MiniCPM-V-4.6/`（+`mmproj-F16.gguf`，handler 重复推理会崩）、`models/LLM/gemma-4-E4B-it/`（head_dim=512，同样上下文 KV 比同类大4倍）；`LLM` 目录由 base.py 经 `folder_paths.folder_names_and_paths["LLM"]` 动态注册。
- 显卡 RTX 4060 Laptop 8GB；ComfyUI python 环境在 `D:\AI\ComfyUI-Dev\python_embeded`（Python 3.13），测试脚本直接用它跑。
- base.py 的 `Llama()` 现带 try/except 诊断包装（抛出 Free VRAM + 模型大小 + 修复建议），别再改回裸调用 `verbose=False`。
