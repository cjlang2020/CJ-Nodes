# CJ-Nodes 项目指南

个人整合的 ComfyUI 自定义节点插件（"Luy-" 系列）。节点详情可查 `README.md`（含每个节点的参数表）。

## 目录结构

```
CJ-Nodes/
├── __init__.py            # 插件入口：WEB_DIRECTORY、前端扩展注册、/CJ-Nodes 路由（web 静态页 + API）
├── nodes.py               # 核心：自动扫描加载 service/ 下所有节点 + 显示名映射
├── README.md              # 节点详细文档（参数表、功能说明）
├── service/               # 所有后端节点代码（按功能域分子目录，也散落少量根目录文件）
│   ├── aitools/           # AI 推理节点（Qwen3 文本/视觉），aitools_base.py 共享基础，model_config.json 配置模型与提示词模板，T/ V/ 存提示词模板 txt
│   ├── llama-cpp/         # 本地 llama.cpp 推理（llamacpp*.py），support/ 辅助模块。依赖 llama-cpp-python；版本兼容与调试备忘见本目录 AGENTS.md
│   ├── llamacpplocal/     # llama.cpp 本地 HTTP API 方式调用
│   ├── stringtools/       # 字符处理
│   ├── prompttools/       # 提示词节点，prompt_options/ 等目录存词表 txt（每个 txt 生成一个下拉）
│   ├── loramodeltools/    # Lora 加载（带触发词系列）
│   ├── imagetools/        # 图片加载/裁剪/合成/遮罩/保存/视频旋转
│   ├── latenttools/       # Latent 与 Sigmas
│   ├── filetools/         # txt 读写
│   ├── princepainter/     # Painter 系列视频生成（首尾帧/长视频/多帧/音频裁剪/Flux2 图编辑）
│   ├── locateanything/    # 目标检测 + 裁剪
│   ├── music/             # 音乐：YuE2 生成（yue2_music_nodes.py，3 节点）+ SheetSage2 扒谱（sheetsage2_music_nodes.py，2 节点）；yue2 引擎在 libs/yue2，详见本目录 AGENTS.md
│   ├── pose/              # 姿态编辑
│   └── *.py               # 根目录散落节点：DualCLIPLoader、QwenMultiangleCameraNode、VisClipCopy、VramClean、QwenEditAddLlamaTemplate 等
├── web/                   # 独立功能页面（*.html，经 /CJ-Nodes/{path} 路由访问）
│   └── js/                # ComfyUI 前端扩展（自动加载）+ fabric.min.js / OrbitControls.js 第三方库；hot_reload.js 为菜单栏"重载插件"按钮
├── libs/                  # 内置/第三方库（如 libs/yue2 推理引擎）。必须在 service/ 之外，否则会被当作节点文件加载
└── doc/                   # 空
```

## 节点加载机制（nodes.py，改动的关键入口）

1. **自动递归加载**：`os.walk(service/)` 加载所有非 `__` 开头的 `.py`，模块名为 `cj_nodes_<文件名>`（唯一化避免冲突）。**新建节点文件放进 service/ 任意子目录即被加载，无需手动 import**。
2. **注册条件**：类同时具有 `INPUT_TYPES` + `RETURN_TYPES` + `FUNCTION` 三个属性才会注册为节点（共享工具类如 `aitools_base.py`、`base.py` 不会被误注册）。
3. **显示名**：`CUSTOM_DISPLAY_NAMES` 字典（nodes.py 顶部）维护 `类名 -> "Luy-中文名"`；未登记的显示为 `Luy-类名`。**新增节点必须在此登记中文名**。
4. **导入方式**：文件所在目录及其父目录（service/）会插入 `sys.path`，所以跨文件用 `from aitools_base import ...` 这类顶层导入，**不要用相对导入**。
5. 加载异常只 print 不中断，排查节点没注册时看 ComfyUI 启动日志的 "❌ 加载文件" 输出。
6. **包目录不能放进 service/**：递归遍历不区分包与普通目录，包内的 `.py` 会被逐个当节点模块执行（`__package__=None`），带相对导入的包必定报 `attempted relative import with no known parent package`。内置库/引擎请放 `CJ-Nodes/libs/`。（已存在例外：`service/llama-cpp/__init__.py`，其内部模块均用顶层导入所以无害。）

## 节点清单（按功能域）

显示名均为 `Luy-*`，此处省略前缀。完整参数见 README.md。

| 类名 | 功能 | 文件 |
|---|---|---|
| **字符处理** service/stringtools/ | | |
| Any2String / Any2Number | 任意类型转字符串/数字 | Any2Any.py |
| ForItemByIndex | 按数量循环输出行文本（数组） | ForItemByIndex.py |
| StringJoinDeal | 双字符串拼接/替换/透传 | StringJoinDeal.py |
| StringSplitDeal | 字符串按分隔符拆分为数组+长度 | StringSplitDeal.py |
| StringMergeDeal | 8 路可选输入拼接（空项忽略） | StringMergeDeal.py |
| StringArrayIndexer | 从字符串数组按索引取单个字符串（负索引支持，越界返空） | StringArrayIndexer.py |
| **提示词** service/prompttools/ | | |
| PromptGenerator / EditPromptNode / AnimaPromptNode | 词表下拉组合提示词（中/英/混合 4 输出） | PromptSelectorNode.py / EditPromptNode.py / AnimaPromptNode.py |
| MetaTokenNode / Wan22PromptSelector | MetaToken / Wan2.2 提示词 | MetaTokenNode.py / PromptSelectorNode.py |
| SDXLPromptPickerNode / AnimaStylePickerNode / CharacterPickerNode | SDXL 角色/画师风格/角色 Tag 选择（web UI 联动） | PromptManagerNode.py |
| PromptBuilderNode | Ideogram4 提示词 JSON | PromptBuilderNode.py |
| EditRegionNode | 图片区域编辑提示词 | EditRegionNode.py |
| ShowAnything | 任意类型显示 | ShowAnythingNode.py |
| **AI 大模型** | | |
| MultiFunAINode / Qwen3Deal / ImageDeal | AI 多功能 / Qwen3 文本 / Qwen3-VL 图片反推（本地 llama-cpp） | aitools/MultiFunAINode.py, Qwen3Chat.py, Qwen3VlImage.py |
| LlamaCppAPINode / LlamaCppAPIRefreshPrompts | llama.cpp HTTP API 调用/刷新模板 | llamacpplocal/llamacpp_api_node.py |
| llama_cpp_model_loader / _parameters / _instruct_adv | llama.cpp 本地推理三件套 | llama-cpp/nodes.py |
| llama_run_lite / llama_run_simple | 反推 Lite / 简化版 | llama-cpp/llamacpp_lite.py / llamacpp_image.py |
| **Lora / 模型加载** service/loramodeltools/ | | |
| LuySdxlLoraLoader + LuyLoraLoaderModelOnly{ALL,FLUX,QWEN,QWENEDIT,ByDir} / UpdateLoraMetaData | SDXL 及各基座 Lora 加载（输出内置触发词） | LuySdxlLoraLoader.py |
| CJPowerLoraLoader / LoraLoaderWithTrigger | 多 Lora + 触发词（web UI） | CJPowerLoraLoader.py / LoraLoaderWithTrigger.py |
| LuyDualCLIPLoader | 双 CLIP | ../DualCLIPLoader.py（service 根） |
| **图片处理** service/imagetools/ | | |
| LoadImageUtils / ShowCanvasImage / LuyLoadImageBatch / FolderSelectNode | 加载图片/画布显示/批量加载/选文件夹 | LoadImageUtils.py |
| MaskedImage2Png / ExtractMaskRegion / CompositeRepaintedImage / MaskColorFill / DrawImageBbox | 遮罩转 PNG/区域提取/合成/填充/Bbox 绘制 | MaskedImage2Png.py |
| ImageCropSquare / ImageMerge / ImageGridCrop / VR360Crop | 方形裁剪/合并/网格裁切/全景裁剪 | 同名文件 |
| ImageEditNode / DrawPhotoNode / ImageDesign | AI 图片编辑/绘画/设计（web UI 联动） | ImageEditNode.py |
| LuySaveImage / SavePNGZIP_and_Preview_RGBA_AnimatedWEBP | 保存图片 / RGBA 图层转视频 | SaveImage.py / RGBA_save_tools.py |
| VideoRotate90 / VideoRotate90Alt | 视频旋转 90°（PIL / 张量两版） | VideoRotate90.py |
| **Latent** service/latenttools/ | | |
| LuyEmptyLatentImage / LuyLoadLatent / LuySaveLatent | 空 Latent / 加载 / 保存 | LatentUtils.py |
| SigmasDefinition | 自定义 Sigmas | SigmasNode.py |
| Krea2StyleSemanticConditioningImproved | Krea2 风格语义条件 | Krea2StyleUtils.py |
| **镜头控制 / 视频生成** | | |
| QwenPlus/QwenLora/Flux2Lora MultiangleCameraNode / QwenMultiangleLightningNode | 千问/Flux2 镜头视角与光照 prompt 生成（web UI 联动） | QwenMultiangleCameraNode.py |
| QwenEditAddLlamaTemplate | 千问编码器（Llama 模板） | QwenEditAddLlamaTemplate.py |
| PainterFLF2V / PainterI2V(+Advanced) / PainterLongVideo / PainterMultiF2V / PainterCombineFromBatch / PainterPrompt / PainterAudioCut / PainterFluxImageEdit | Painter 系列视频生成与编辑 | princepainter/ 对应文件 |
| **其他工具** | | |
| FileReadDeal / FileSaveDeal | 读 txt（数组输出）/ 写 txt | filetools/FileDeal.py |
| LocateAnythingNode / LocateAnythingCropNode | 目标检测 / 检测后裁剪 | locateanything/ |
| CJOpenPoseEditor | 姿态编辑（web UI 联动） | pose/CJOpenPoseEditor.py |
| VisClipCopyImageReference | 视觉参考条件 | VisClipCopy.py |
| VRAMClean | 清显存 | VramClean.py |
| **音乐** service/music/ | | |
| CJYuE2ModelLoader / CJYuE2Generate / CJYuE2Unload | YuE2 音乐生成：加载 / 生成（风格+歌词→48kHz 音频）/ 卸载 | yue2_music_nodes.py |
| CJSheetSage2Transcribe / CJSheetSage2Unload | SheetSage2 音频扒谱：音频→两版 ABC/MIDI/调性/和弦/曲式+风格底稿；卸载 | sheetsage2_music_nodes.py |

## 设计约定（新增/修改节点必读）

1. **新节点三步**：① 在 service/ 对应功能域子目录建 `.py`，类写标准节点四件套（`INPUT_TYPES`/`RETURN_TYPES`/`FUNCTION`/`CATEGORY`）；② 在 nodes.py 的 `CUSTOM_DISPLAY_NAMES` 登记中文名；③ 重启 ComfyUI 验证。
2. **CATEGORY 命名**：`luy/<分类>`（如 `luy/字符处理`、`luy/提示词`、`luy/图片处理`）。Painter 系列部分用 `Painter/*`，属历史遗留，新节点统一用 `luy/`。
3. **文件头兼容写法**：现有文件都有 `try: from comfy.nodes import BaseNode except ImportError: class BaseNode: pass` 头，新节点沿用（即使当前未用到 BaseNode）。
4. **数组输出模式**：输出"数组 + 长度"时用 `RETURN_TYPES = ("STRING", "INT")` + `RETURN_NAMES = ("array", "count")` + `OUTPUT_IS_LIST = (True, False)`，数组项逐条驱动下游（参考 `StringSplitDeal` / `ForItemByIndex`）。数组需兜底非空（空时给 `[""]`），否则下游执行 0 次。
5. **可选输入**：非必填输入放 `"optional"` 段并给 default；执行函数用 `**kwargs` 接收并对 None/空值做忽略，保证未连接也能跑（参考 `StringMergeDeal`）。
6. **分隔符约定**：字符串节点的分隔符参数统一支持字面量 `\n`/`\t` 转真实换行/制表符（`delimiter.replace("\\n", "\n")`）。
7. **词表驱动**：提示词类节点从 service/*/ 下的 txt 目录（如 prompttools/prompt_options/）动态读文件生成下拉，改词表只需加 txt，不用改代码；模板键名映射在 `aitools/model_config.json`。
8. **共享逻辑**：同域公共函数放该域的 base 文件（如 `aitools/aitools_base.py`、`llama-cpp/base.py`），通过 sys.path 顶层导入；注意 base 文件不要定义带节点三件套的类，否则会被误注册。

## Web 前端

- `web/js/*.js`：ComfyUI 前端扩展，`app.registerExtension` 注册，随插件自动加载（经 `EXTENSION_WEB_DIRS["CJ-Nodes"]`）。负责菜单按钮（本地资源/流程管理/重载插件）及节点内嵌 UI。
- `web/*.html`：独立功能页（图片绘画/编辑、风格选择、镜头控制、姿态编辑等），节点通过 iframe/浏览器打开 `http://<host>:<port>/CJ-Nodes/<page>.html` 访问；`__init__.py` 的 `/CJ-Nodes/{path}` 路由做了路径穿越安全检查（`_is_safe_child`），新页面放 web/ 根目录即可被访问。
- 后端 API 挂在 `__init__.py`（如 `POST /CJ-Nodes/api/open-directory`），新 API 同样加在该文件。

## 注意事项与已知坑

- **必须安装 llama-cpp-python**（JamePeng 预编译版，按 Python 版本选），否则 aitools/llama-cpp 节点导入失败。已验证 0.3.49；**升级包后若顶层 import 失效，整个域节点连锁消失**，版本兼容/调试/显存细节见 `service/llama-cpp/AGENTS.md`。
- `aitools_base.py` 顶层 `from llama_cpp import Llama`，该目录下任何文件被加载都会触发此导入——环境缺依赖时该域节点全部加载失败但不影响其他节点。
- LLM 模型放 `models/LLM/`（代码通过 `folder_paths.folder_names_and_paths["LLM"]` 动态注册目录），支持 gguf。
- 同一功能常有"双版本"（如 VideoRotate90 PIL 版 / Alt 张量版），修改时确认改的是哪一个，两者在 nodes.py 显示名已区分。
- nodes.py 加载失败仅打印日志，节点"消失"先查启动日志，再查 CUSTOM_DISPLAY_NAMES 是否漏登记；若只挂一个功能域，优先怀疑该域 base 文件（如 llama-cpp/base.py、aitools/aitools_base.py）的顶层 import 被依赖升级破坏。
- 前端 JS 引用 ComfyUI 内部模块用相对路径 `../../../../scripts/app.js`，目录层级不能变。

## 热重载（"重载插件"按钮）

- **用法**：修改 `service/` 下任意 .py 后，点 ComfyUI 菜单栏"重载插件"按钮（web/js/hot_reload.js）→ POST `/CJ-Nodes/api/reload-nodes` → `nodes.py` 的 `reload_all_nodes()` 重建全部节点并同步进 ComfyUI 全局 `nodes.NODE_CLASS_MAPPINGS` → 刷新浏览器（F5）加载新 /object_info。**新增/修改/删除节点文件均支持**。
- **原理**：ComfyUI 启动时把插件映射逐项复制进全局字典且 /object_info 实时生成，所以热重载只需更新全局字典；重载前会清理 sys.modules 中本插件 service/ 下的缓存模块，保证 `from base import` 拿到新代码。
- **局限**：`__init__.py`（路由）、`nodes.py` 本身、web/ 前端 JS 的改动不在热重载范围（JS 改动刷新页面即生效；路由改动需重启）。正在执行的工作流用旧类对象跑完，不受影响。
- 调试 API：`curl -X POST http://<host>:<port>/CJ-Nodes/api/reload-nodes`
