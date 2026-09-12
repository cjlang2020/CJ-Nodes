# llama-cpp 模块备忘（版本兼容 / 调试 / 隐藏依赖）

## 版本兼容（llama-cpp-python，JamePeng fork）

- 0.3.49 实测可用（支持 qwen35/qwen35moe 架构与 Qwen35ChatHandler）。升级包后 `llama_speculative.py` 删除了 `LlamaPromptLookupDecoding`（旧滑窗投机解码），只剩 `LlamaNGramMapDecoding`（构造签名 ngram_size/num_pred_tokens 兼容不变）。
- `base.py` 是本目录全部 6 个 py 的公共依赖（其余文件 `from base import ...`）。**base.py 顶层 import 一失败，整个 llama-cpp 域所有节点连锁加载失败**（受 nodes.py 自动加载机制影响，见上级 AGENTS.md）。
- 改投机解码相关代码必须同步改的文件：`base.py`（import + `draft_model_types` 列表 + 构造分支）+ `llamacpp.py` / `llamacpp_image.py` / `llamacpp_text.py` / `nodes.py` 中 `draft_model_type` 的 tooltip 文案（`llamacpp_lite.py` 复用列表变量无需改文案）。
- `draft_model_types` 现为 `["None", "ngram-map"]`；旧工作流里存了 `prompt-lookup` 的节点重新打开会提示值无效，需手动改为 `ngram-map`。

## 调试："Failed to load model from file" 是误导性错误

- `Llama()` 抛出的这个错误无信息量，真实原因（显存不足 / 架构不支持 / 文件损坏）全部被 `verbose=False` 吞掉。base.py 已包装为带 Free VRAM 与修复建议的 RuntimeError；需深入排查时写独立脚本以 `verbose=True` 加载看 ggml 日志。
- 显存需求实测（8GB 卡 / RTX 4060 Laptop）：9B Q4_K_XL 全量 offload ≈ 权重 5679MB + CUDA buffer 501MB(n_ctx 8192) + mmproj 900MB ≈ **7.1GB**。ComfyUI 同跑 SD 模型时必然失败；用户侧解法：节点 `vram_limit` 设 5~6 让代码按层拆分 GPU/CPU，或先卸载已加载的 SD 模型。
- 判断模型文件是否损坏：用 `from gguf import GGUFReader` 读元数据（注意 llama_cpp 包内没有 gguf 子模块，gguf 是独立包）。字符串字段要直接 `field.contents()`，取 `[0]` 只会拿到首字符。
- 快速确认内核是否支持某架构：在 `python_embeded/Lib/site-packages/llama_cpp/lib/*.dll` 二进制里搜架构名字符串（如 `qwen35`）。Python 一行即可：`re.findall(rb'qwen3[0-9a-zA-Z_]*', open(dll,'rb').read())`，llama.dll 命中即支持。

## 隐藏依赖：CUDA 后端靠 torch 的 DLL

- `ggml-cuda.dll` 依赖 `python_embeded/Lib/site-packages/torch/lib/` 下的 `cudart64_13.dll` / `cublas64_13.dll`（CUDA 13）。独立 Python 进程中它**静默**加载失败（backend registry 只有 CPU，`n_gpu_layers=-1` 也全跑 CPU，不报错）；只有进程内已 import torch 后 CUDA 后端才注册成功。
- 独立测试 GPU 加载必须先 `import torch` 或 `os.add_dll_directory(.../torch/lib)`。后端加载机制源码在 `site-packages/llama_cpp/llama.py` 的 `Llama.__init__`（`ggml_backend_load_all_from_path`），日志看 "Loaded ggml backend registry count"。

## 模型资产与本机环境

- 本机模型：`models/LLM/Qwen3.5/{0.8B,4B,9B}/`（9B 为 `Qwen3.5-9B-UD-Q4_K_XL.gguf` + `mmproj-BF16.gguf`）；`LLM` 目录由 base.py 经 `folder_paths.folder_names_and_paths["LLM"]` 动态注册。
- 显卡 RTX 4060 Laptop 8GB；ComfyUI python 环境在 `D:\AI\ComfyUI-Dev\python_embeded`（Python 3.13），测试脚本直接用它跑。
- base.py 的 `Llama()` 现带 try/except 诊断包装（抛出 Free VRAM + 模型大小 + 修复建议），别再改回裸调用 `verbose=False`。
