# CJ-Nodes 项目指南

个人整合的 ComfyUI 自定义节点插件（"Luy-" 系列）。节点详情可查 `README.md`（含每个节点的参数表）。

## 目录结构

```
CJ-Nodes/
├── __init__.py            # 插件入口：WEB_DIRECTORY、前端扩展注册、/CJ-Nodes 路由（web 静态页 + API）
├── nodes.py               # 核心：自动扫描加载 service/ 下所有节点 + 显示名映射
├── plugin_manager.py      # custom_nodes 下插件的列举/开关（.disabled 后缀）/整体重载，服务 /CJ-Nodes/api/plugins*（必须放 service/ 之外，否则被当节点加载）
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
│   ├── music/             # 音乐：YuE2 生成（yue2_music_nodes.py，3 节点）+ SheetSage2 扒谱（sheetsage2_music_nodes.py，2 节点）+ 风格标签 / 风格标签替换（music_style_nodes.py + style_tags/ 词表，2 节点）；yue2 引擎在 libs/yue2，详见本目录 AGENTS.md
│   ├── pose/              # 姿态编辑
│   └── *.py               # 根目录散落节点：DualCLIPLoader、QwenMultiangleCameraNode、VisClipCopy、VramClean、QwenEditAddLlamaTemplate 等
├── web/                   # 独立功能页面（*.html，经 /CJ-Nodes/{path} 路由访问）
│   └── js/                # 前端扩展（自动加载）+ 第三方库（three.min.js / OrbitControls.js / fabric.min.js）。
│                          #   顶栏按钮：hot_reload.js(重载插件) / local_resources.js(Output图片) / workflow_manager.js(Workflows目录) / plugin_manager.js(插件管理)，样式统一在 cj_menu_style.js
│                          #   画布落盘共享模块：canvas_upload.js（ImageEditNode/DrawPhotoNode/ImageDesign 三个面板复用）
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
7. **调试/临时脚本绝不能放在 service/ 下**：加载器只排除 `__` 开头的文件，`_check_xxx.py` 这种单下划线开头的**也会被 import**（模块级代码会真的执行，例如加载模型）。临时脚本写到 ComfyUI 根目录，用完即删。

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
| CJMusicStyleTags | 音乐风格标签：分类多选（356 选项，中英对照、输出英文）→ 接生成的 style | music_style_nodes.py（词表 style_tags/） |
| CJMusicStyleReplacer | 风格标签替换：扒谱 style 拆成一行一个标签，前端面板逐行换（下拉/点选/手输）后拼回；状态存隐藏 widget，过期则原样透传 | music_style_nodes.py + web/js/music_style_editor.js（路由 /CJ-Nodes/api/music-style/*） |

## 设计约定（新增/修改节点必读）

1. **新节点三步**：① 在 service/ 对应功能域子目录建 `.py`，类写标准节点四件套（`INPUT_TYPES`/`RETURN_TYPES`/`FUNCTION`/`CATEGORY`）；② 在 nodes.py 的 `CUSTOM_DISPLAY_NAMES` 登记中文名；③ 重启 ComfyUI 验证。
2. **CATEGORY 命名**：`luy/<分类>`（如 `luy/字符处理`、`luy/提示词`、`luy/图片处理`）。Painter 系列部分用 `Painter/*`，属历史遗留，新节点统一用 `luy/`。
3. **文件头兼容写法**：现有文件都有 `try: from comfy.nodes import BaseNode except ImportError: class BaseNode: pass` 头，新节点沿用（即使当前未用到 BaseNode）。
4. **数组输出模式**：输出"数组 + 长度"时用 `RETURN_TYPES = ("STRING", "INT")` + `RETURN_NAMES = ("array", "count")` + `OUTPUT_IS_LIST = (True, False)`，数组项逐条驱动下游（参考 `StringSplitDeal` / `ForItemByIndex`）。数组需兜底非空（空时给 `[""]`），否则下游执行 0 次。
5. **可选输入**：非必填输入放 `"optional"` 段并给 default；执行函数用 `**kwargs` 接收并对 None/空值做忽略，保证未连接也能跑（参考 `StringMergeDeal`）。
6. **分隔符约定**：字符串节点的分隔符参数统一支持字面量 `\n`/`\t` 转真实换行/制表符（`delimiter.replace("\\n", "\n")`）。
7. **词表驱动**：提示词类节点从 service/*/ 下的 txt 目录（如 prompttools/prompt_options/）动态读文件生成下拉，改词表只需加 txt，不用改代码；模板键名映射在 `aitools/model_config.json`。
8. **共享逻辑**：同域公共函数放该域的 base 文件（如 `aitools/aitools_base.py`、`llama-cpp/base.py`），通过 sys.path 顶层导入；注意 base 文件不要定义带节点三件套的类，否则会被误注册。
9. **界面字段名用中文（llama-cpp 域已全量完成，可作参考）**；但**内部 API 键必须保持英文**：`create_chat_completion(...)` 的关键字（`max_tokens`/`seed`/`presence_penalty`…）、`custom_config` 的配置键（`model`/`mmproj`/`n_ctx`…）、`hidden` 里的 `unique_id` —— 混用会直接报 `TypeError: unexpected keyword argument`。
10. **改字段名/顺序会破坏旧工作流**：ComfyUI 的 `widgets_values` **按位置**存，连线按输入名匹配 → 重命名会让旧流程的值回落默认、连线断开；重排序会让值错位（如 `上下文长度` 的值跑到 `最大生成长度`）。要改就先提醒用户或备份工作流。
11. **批量改名的正确做法**：用 `tokenize` 词法级替换（只改 NAME，自动跳过 STRING/COMMENT），并额外跳过“函数调用处的关键字参数名”（`seed=seed` 的左值不能改）与属性访问；**不要用正则** —— 会把 `"model": model`、`"max_tokens": 最大生成长度` 这类字符串键一起改坏。详见 `service/llama-cpp/AGENTS.md`。
12. **节点自检配方（不用启 UI/浏览器）**：把 ComfyUI 根目录加进 `sys.path` 后 import 节点模块，对每个类比对 `INPUT_TYPES()` 的 required+optional 键集与 `inspect.signature(getattr(cls, cls.FUNCTION))` 的参数名（允许只多出 hidden 的 `unique_id`），并校验 `len(RETURN_TYPES)==len(RETURN_NAMES)==len(OUTPUT_IS_LIST)`。
13. **参数顺序惯例**：按**使用频次**排（模型/提示词最上 → 常用行为 → 抽样微调 → 调试/加速项最下）；新字段要插进对应档，不要一律追加在末尾。

## Web 前端

- `web/js/*.js`：ComfyUI 前端扩展，`app.registerExtension` 注册，随插件自动加载（经 `EXTENSION_WEB_DIRS["CJ-Nodes"]`）。负责菜单按钮（本地资源/流程管理/重载插件/插件管理）及节点内嵌 UI。
- **前端会把该目录下递归所有 `.js` 当扩展模块 import**（`server.py` 的 `get_extensions` 用 `glob('**/*.js')`）→ 库/共享模块必须**零副作用**。已踩过的两个坑：`OrbitControls.js` 顶层引用全局 `THREE` 在模块求值时抛错（已加 `typeof THREE === 'undefined'` 护栏）；被误删的 `viewer_inline.js` 仍被 `qwen_multiangle_light.js` import → “Failed to fetch dynamically imported module”。两者都会中断 `app.setup()`，现象是**顶栏所有插件按钮消失**。
- **`window.app` 在这个前端构建里不是就绪标志**（`await app.setup()` 成功后才赋值；上面那种 import 失败就永远没有）。拿 app 用 `const { app } = await import('/scripts/app.js')`；查扩展是否加载看 `app.extensions` / `app.menu.settingsGroup.buttons`；单文件体检 `await import('/extensions/CJ-Nodes/js/xxx.js')`（重复导入报 "already registered" 说明它已加载）。
- 顶栏按钮样式统一在 `web/js/cj_menu_style.js`（跟随 `--p-*` 主题变量、中性底色 + 主色图标，**别再写死的红/绿 `!important` 色块**）。ComfyButton 的图标渲染成 `<i class="mdi mdi-<icon>">`，给图标上色要用 `.mdi` 选择器。
- **面板页缓存**：`/CJ-Nodes/*.html` 由插件自己的路由服务（不是 ComfyUI 的 `/extensions`，后者带 `no-store`）。已在 `__init__.py` 加 `_REVALIDATE_HEADERS`；同时 iframe `src` 必须带 `?v=${PANEL_VERSION}`（每次页面加载一个时间戳，见三个 `image_*.js`）——否则浏览器会沿用旧缓存条目（**服务端后来加 `no-cache` 对已缓存的旧响应无效**），现象是“改了 HTML 却不生效 / 画布恢复代码不存在”。
- `web/*.html`：独立功能页（图片绘画/编辑、风格选择、镜头控制、姿态编辑等），节点通过 iframe/浏览器打开 `http://<host>:<port>/CJ-Nodes/<page>.html` 访问；`__init__.py` 的 `/CJ-Nodes/{path}` 路由做了路径穿越安全检查（`_is_safe_child`），新页面放 web/ 根目录即可被访问。
- 后端 API 挂在 `__init__.py`（如 `POST /CJ-Nodes/api/open-directory`），新 API 同样加在该文件。

## 内嵌 DOM 面板高度跟随节点（通用做法，前端 1.52 实测）

给节点加内嵌面板（`node.addDOMWidget(...)`，如 `web/js/music_style_editor.js`）时，想让它**随节点高度伸缩、内部滚动**，必须按下面做，否则会出现“面板高度写死、节点拉高面板不动”。

框架行为（1.52 的 `_arrangeWidgets` / `computeLayoutSize`）：widget 分两类——

| widget | 高度来源 | 结果 |
|---|---|---|
| 有 `computeSize` 的 | `computeSize(width)[1]` | **固定高度**，直接从可用空间扣掉，不参与弹性分配 |
| 有 `computeLayoutSize` 的（DOM/component widget 自带） | CSS 变量 `--comfy-widget-min-height`（min）、`--comfy-widget-max-height`（max，不设=∞）、`--comfy-widget-height`（可为 `%`=节点高度百分比） | **弹性**，`distributeSpace` 把节点剩余空间全分给它 |

1. **绝对不要**给 DOM widget 写 `widget.computeSize = () => [w, h]` —— 那会把它降级成固定高度（本坑踩过一次）。
2. 高度交给弹性布局：`wrap.style.setProperty("--comfy-widget-min-height", "200px")`（给下限，别让它塌掉）。
3. CSS 三件事：容器填满、中间列表滚动、头/尾固定——
   ```css
   .my-panel{display:flex;flex-direction:column;height:100%;min-height:0;box-sizing:border-box}
   .my-panel-head,.my-panel-foot{flex:0 0 auto}
   .my-panel-list{flex:1 1 auto;min-height:36px;overflow-y:auto}
   ```
4. “行变多自动把节点补高”另用 JS 补一层（**只补缺口，不跟用户手动缩小抢**）：
   ```js
   function fitNodeHeight(node){                        // 每次渲染后调用
     const wrap = node._panelWrap;
     if (!wrap || !wrap.clientHeight) return;           // 还没布局完：下一帧重试（限次数）
     const need = naturalContentHeight(node);           // 头/脚 offsetHeight + 列表 scrollHeight
     const have = wrap.clientHeight;                    // 当前真正分到的高度
     if (need <= have + 4) return;
     if (need <= (node._panelFitted ?? 0) + 4) return;  // 之前按更大内容调过 → 用户自己缩的，不抢
     node.setSize([node.size[0], Math.min(1200, node.size[1] + (need - have))]);
     node._panelFitted = need;
   }
   ```
   - 算缺口要用 `wrap.clientHeight`（弹性分配后的真实高度）；用 `wrap.scrollHeight` 量不出缺口（容器被压缩后它等于容器高度）。
   - `scrollHeight` 只在**列表内部**用（溢出时它仍是内容高度）。

参考实现：`web/js/music_style_editor.js`（`fitNodeHeight` / `naturalContentHeight` / `--comfy-widget-min-height`）。

已按此改造的面板（2026-09 一次性清掉写死的 `computeSize`；改这些文件时别再加回去）：

| 面板 | 元素 | 最小高度 |
|---|---|---|
| `anima_style_picker.js` / `character_picker.js` / `sdxl_role_prompt_choice.js` | iframe | 380px |
| `image_draw.js` / `image_edit.js` / `image_design.js` | iframe | 420px |
| `vr360_crop.js` / `qwen_multiangle_{lora,plus,light}.js` / `flux2_multiangle_lora.js` | iframe | 380 / 300px |
| `edit_region.js` / `prompt_builder.js` | wrap div（本来就没写 computeSize，补了 `height:100%` + 最小高度） | 260 / 300px |
| `openpose_editor.js` | wrap div（3D 视口从 `aspect-ratio:1/1 + max-height:400px` 改成 `flex:1 1 auto`，跟着节点长） | 380px |
| `music_style_editor.js` | wrap div（带 `fitNodeHeight` 自动补高） | 200px |

不需要改的：`lora_loader_ui.js`（两行选择框的内容型小面板）、`CJPowerLoraLoader.js`（画布自绘 widget，`computeSize` 在这里是正确用法）、
`prompt_manage.js`（**文件本身解析不过**：第 4 行起是一整段 HTML，浏览器加载它会 SyntaxError）→ 已改名 `web/js/prompt_manage.js.disabled` 归档（内容保留；要修需拆成独立 HTML 页面 + 正常扩展 JS）。

### 面板状态同步：连线上游时 widget 值恒为空

内嵌面板常用一个隐藏 widget 存面板状态（`prompt_builder.js` 的 `prompt_data`、`music_style_editor.js` 的 `替换状态`）。注意：

- 输入 widget 一旦连线上游，**widget 自身的 value 恒为空**（真实值只在执行时到后端）；同步逻辑里不能把“空值”当成“用户清空了输入”，否则 undo/重载会把面板抹掉。判断用 `node.inputs.find(i => i.name === 'xxx')?.link != null`。
- 前端拿真实输入值的唯一可靠通道是节点返回的 `ui` 载荷 + `onExecuted(output)`（1.52 在 `addApiUpdateHandlers` 里调用，`app.nodeOutputs[nodeId]` 也会存一份）；`widget.linkedUpstream` 只认“上游同名 widget/唯一非空 widget”，对纯 STRING 输出无效。

## 画布数据落盘（图片类节点：ImageEditNode / DrawPhotoNode / ImageDesign）

- **不要把画布 base64 塞进 widget**：工作流/草稿会把整份 JSON 存进前端 `localStorage`（实测可写上限 ~4MB），超限后 `saveDraft` 失败并 `markStorageUnavailable()` **锁死整个页面会话的草稿保存** → 反复弹“保存工作流草稿失败”，此后连小工作流也存不上（诊断特征：弹窗期间 draft 相关 `localStorage.setItem` 调用数为 **0**）。
- **正确做法**（与核心 LoadImage / Painter 同款）：`POST /api/upload/image`（`type=input`、`subfolder=cj_canvas`、`overwrite=true`）先落盘，widget 只存 `cj_canvas/cj_canvas_<token>.png` 引用。共享实现 `web/js/canvas_upload.js` 的 `createCanvasStore()`；文件在 `ComfyUI/input/cj_canvas/`，每实例一个、改动原地覆盖（删节点不自动删文件）。
- 后端读回：`ImageEditNode.py` 的 `_resolve_canvas_file()`（`folder_paths.get_directory_by_type('input')` + `commonpath` 包含校验，`..` 直接拒）+ `_payload_image()`（优先文件名，旧 `*_base64` 仍兼容）。
- **DOM widget 会重复序列化**：`addDOMWidget` 的 value 同样进 `widgets_values`（面板数据常与隐藏 widget 重复一份，白白翻倍）→ 加 `widget.serialize = false; widget.options.serialize = false;`。LiteGraph 存取两侧都跳过 `serialize === false`（旧工作流安全），但**该 widget 必须是最后一个**，否则位置会错位。另：DOM widget 的 `setValue` 会回写隐藏 widget（`drawDataWidget.value = v`），所以父窗口别给 DOM widget 赋 base64（会瞬间写进工作流，草稿仍有配额风险）。
- **两个前端时序**：`graphToPrompt` 会 `await widget.serializeValue`（排队执行前强制落盘），而工作流保存/草稿走**同步** `widget.value` → base64 必须在 `push()` 里同步剔除，不能等异步上传完成；`DRAW_CANVAS_READY` 可能早于 `widgets_values` 应用 → 父窗口在 `onConfigure` 也要下发 INIT（新建节点用 500ms 兜底）。
- iframe 用 `state.readyForPush` 门控回写；**首次 INIT 必须不保留内容**（`initCanvas(w, h, true, false)`），否则 `initCanvas` 保留分支里的异步回写会晚于“从服务器恢复”，把空白画布推上去并**覆盖服务器上的图**。

## 插件管理（顶栏“插件管理”按钮）

- 前端 `web/js/plugin_manager.js`（点卡片即切换，绿=启用/灰=关闭，无“选中后确认”），后端 `plugin_manager.py` + 三个接口：`GET /CJ-Nodes/api/plugins`、`POST /CJ-Nodes/api/plugins/set-enabled`、`POST /CJ-Nodes/api/plugins/reload`。
- 开关就是给 `custom_nodes/<包名>` 加/去 **`.disabled`**（`nodes.py:2369` 只看后缀、**大小写敏感**；`__pycache__`、`.` 开头、CJ-Nodes 自身都不进列表）。另可用启动参数 `--disable-all-custom-nodes --whitelist-custom-nodes`。
- `/plugins/reload` 重扫并重导 custom_nodes 下除 CJ-Nodes 外的所有包（按 `cls.RELATIVE_PYTHON_MODULE` 归属卸载、`sys.modules` 键是“路径把点换成 `_x_`”），并补注册它们的 `/extensions` 静态目录；**带自定义 HTTP 路由/后台线程的包仍需重启**（重导只重建节点映射，不重跑 aiohttp 路由注册）。
- 实测收益：2578 节点时 `/object_info` 约 10s，给不用的包加 `.disabled` 是最有效的降耗手段（按包节点数见 ComfyUI 根 AGENTS.md）。
- **插件功能描述**存 `user/default/plugin_summaries.json`（键=目录名去 `.disabled`，值=≤100 字描述）；命中显示、未命中显示“未分析功能”。**用户自行维护此文件**（外部更新后刷新页面即生效，无需重启）；面板不做自动分析。
- **`plugin_manager.py` 在 CJ-Nodes 根目录（不在 `service/`）→ 不在“重载插件”热重载范围**，改它必须整体重启 ComfyUI。

## 注意事项与已知坑

- **视觉 handler 属性改名（0.3.49）**：`clip_model_path` → `mmproj_path`（旧名只作构造别名），`hasattr(h, "clip_model_path")` 恒为 False → 带图必报 "not configured with a mmproj module"，但 mtmd 其实已加载；判断统一走 `base.chat_handler_mmproj()`。同版本 `use_think_prompt` 已删除（改 `force_reasoning`）。详见 `service/llama-cpp/AGENTS.md`。
- **必须安装 llama-cpp-python**（JamePeng 预编译版，按 Python 版本选），否则 aitools/llama-cpp 节点导入失败。已验证 0.3.49；**升级包后若顶层 import 失效，整个域节点连锁消失**，版本兼容/调试/显存细节见 `service/llama-cpp/AGENTS.md`。
- `aitools_base.py` 顶层 `from llama_cpp import Llama`，该目录下任何文件被加载都会触发此导入——环境缺依赖时该域节点全部加载失败但不影响其他节点。
- LLM 模型放 `models/LLM/`（代码通过 `folder_paths.folder_names_and_paths["LLM"]` 动态注册目录），支持 gguf。
- 同一功能常有"双版本"（如 VideoRotate90 PIL 版 / Alt 张量版），修改时确认改的是哪一个，两者在 nodes.py 显示名已区分。
- nodes.py 加载失败仅打印日志，节点"消失"先查启动日志，再查 CUSTOM_DISPLAY_NAMES 是否漏登记；若只挂一个功能域，优先怀疑该域 base 文件（如 llama-cpp/base.py、aitools/aitools_base.py）的顶层 import 被依赖升级破坏。
- 前端 JS 引用 ComfyUI 内部模块用相对路径 `../../../../scripts/app.js`，目录层级不能变。
- **内嵌 DOM 面板高度**：`addDOMWidget` 的 widget **千万别加 `computeSize`**（会被当固定高度、拿不到弹性空间，表现为“节点拉高面板不动”）→ 见「内嵌 DOM 面板高度跟随节点」。

## 热重载（"重载插件"按钮）

- **用法**：修改 `service/` 下任意 .py 后，点 ComfyUI 菜单栏"重载插件"按钮（web/js/hot_reload.js）→ POST `/CJ-Nodes/api/reload-nodes` → `nodes.py` 的 `reload_all_nodes()` 重建全部节点并同步进 ComfyUI 全局 `nodes.NODE_CLASS_MAPPINGS` → 刷新浏览器（F5）加载新 /object_info。**新增/修改/删除节点文件均支持**。
- **F5 是必须的**：重载只更新后端映射，画布上的节点定义还是旧的 —— 表现为“新增的中文字段看不到 / 还是英文旧键名 / 改了默认值没变”。排查字段类问题先怀疑这里。
- **原理**：ComfyUI 启动时把插件映射逐项复制进全局字典且 /object_info 实时生成，所以热重载只需更新全局字典；重载前会清理 sys.modules 中本插件 service/ 下的缓存模块，保证 `from base import` 拿到新代码。
- **局限**：`__init__.py`（路由）、`nodes.py` 本身、web/ 前端 JS 的改动不在热重载范围（JS 改动刷新页面即生效；路由改动需重启）。正在执行的工作流用旧类对象跑完，不受影响。
- 调试 API：`curl -X POST http://<host>:<port>/CJ-Nodes/api/reload-nodes`
