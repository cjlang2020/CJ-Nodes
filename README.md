# CJ-Nodes ComfyUI 插件

个人整合的 ComfyUI 自定义节点插件，包含提示词管理、AI 模型调用、图片/视频处理、镜头控制等实用功能，以及便捷的文件管理面板。

---

## 目录

- [功能面板](#功能面板)
- [节点列表](#节点列表)
  - [提示词类](#提示词类)
  - [AI 模型类](#ai-模型类)
  - [模型加载类](#模型加载类)
  - [图片处理类](#图片处理类)
  - [字符/文件处理类](#字符文件处理类)
  - [Latent 类](#latent-类)
  - [镜头控制类](#镜头控制类)
  - [视频生成类](#视频生成类)
  - [其他工具](#其他工具)
- [安装](#安装)
- [注意事项](#注意事项)

---

## 功能面板

插件在主界面顶部工具栏添加了两个便捷按钮：

### 📂 本地资源（绿色背景）
浏览 ComfyUI 的 `output` 目录，支持：
- 图片/音频/视频文件的网格浏览
- 右键菜单：重命名、移动、删除
- 双击图片可直接加载到工作流

### ⚡ 流程管理（红色背景）
浏览和管理工作流文件（`user/{user}/workflows/`），支持：
- 文件夹分层浏览、面包屑导航
- 右键菜单：重命名、移动、删除
- 双击直接打开工作流
- **Ctrl+S 直接保存回原文件**（打开后标题下方显示文件名）

---

## 节点列表

### 提示词类

#### Luy-画图提示词
**类别:** `luy/提示词`

从 `prompt_options/` 目录读取 txt 文件，每个文件生成一个下拉菜单，组合输出多格式提示词。

| 参数 | 类型 | 说明 |
|------|------|------|
| 各分类下拉菜单 | STRING | 自动读取提示词文件，可选"忽略"或"随机" |
| 启用选择节点 | BOOLEAN | 是否启用分类选择 |
| txt_str（可选） | STRING | 自定义追加提示词 |
| seed（可选） | INT | 随机种子 |

**输出:** `中文标签` / `英文标签` / `中英混合标签` / `包含主题内容`

---

#### Luy-动漫Tag提示词
**类别:** `luy/提示词`

可自定义提示词文件路径的增强版选择器，支持 `##` 分隔格式（显示文本##实际值）。

| 参数 | 类型 | 说明 |
|------|------|------|
| 自定义文件路径 | STRING | 指定 txt 文件存放目录 |
| 各分类下拉菜单 | STRING | 同上，但路径可自定义 |
| 启用选择节点 | BOOLEAN | 是否启用分类选择 |
| txt_str（可选） | STRING | 自定义追加提示词 |
| seed（可选） | INT | 随机种子 |

**输出:** `中文标签` / `英文标签` / `中英混合标签` / `包含主题内容`

---

#### Luy-MetaToken提示词
**类别:** `luy/提示词`

Token 级别的随机组合选择器。选择"随机"时从可选值中抽取 N 个 token。

| 参数 | 类型 | 说明 |
|------|------|------|
| 自定义文件路径 | STRING | txt 文件存放目录 |
| 随机数量 | INT | 随机选取的 token 数量 |
| 启用选择节点 | BOOLEAN | 是否启用 |
| txt_str（可选） | STRING | 自定义追加提示词 |
| seed（可选） | INT | 随机种子 |

**输出:** `提示词` / `选择摘要` / `随机token列表`

---

#### Luy-Wan2.2提示词
**类别:** `luy/提示词`

专为 Wan2.2 视频模型设计的提示词构建器。包含 11 个分类下拉，组合生成视频描述。

| 参数 | 类型 | 说明 |
|------|------|------|
| 场景类型 | DROPDOWN | 自然/城市/虚构场景 |
| 运动场景 | DROPDOWN | 跑步/走路/飞行/空翻等 |
| 人物情绪 | DROPDOWN | 15 种情绪选项 |
| 运镜方式 | DROPDOWN | 46 种镜头运动方式 |
| 光源/光线类型 | DROPDOWN | 光源 + 光线效果 |
| 镜头类型/焦距 | DROPDOWN | 远景/中景/特写等 |
| 色调/视觉风格 | DROPDOWN | 色调和艺术风格 |
| 特效镜头 | DROPDOWN | 慢动作/景深等 |

**输出:** `提示词` — 组合后的完整视频提示词

---

#### Luy-自定义提示词
**类别:** `luy/提示词`

与 AnimaPromptNode 结构相同，默认读取 `prompt/E/` 目录。

**输出:** `中文标签` / `英文标签` / `中英混合标签` / `包含主题内容`

---

#### Luy-SDXL角色提示词
**类别:** `luy/提示词`

前端标签选择器的最终输出节点。输入多行文本，输出完整提示词和纯英文提示词（过滤中文字符）。

| 参数 | 类型 | 说明 |
|------|------|------|
| final_prompt | STRING | 前端标签选择器生成的文本 |

**输出:** `prompt` / `english_prompt`

---

### AI 模型类

#### Luy-Qwen3语言大模型
**类别:** `luy/AI`

基于 llama.cpp 的纯文本 LLM 推理节点。

| 参数 | 类型 | 说明 |
|------|------|------|
| model | DROPDOWN | 选择 GGUF 模型文件（LLM 目录） |
| keep_model_loaded | BOOLEAN | 是否保持模型加载在内存 |
| max_tokens | INT | 最大生成长度 |
| prompt | STRING | 用户输入提示词 |
| seed | INT | 随机种子 |

**输出:** `output` — 模型生成的文本

---

#### Luy-Qwen3-VL图片反推
**类别:** `luy/AI`

视觉语言模型节点，可分析图片或视频帧并输出文字描述。

| 参数 | 类型 | 说明 |
|------|------|------|
| model | DROPDOWN | 选择 VL 模型（如 Qwen3-VL） |
| mmproj_model | DROPDOWN | 多模态投影模型 |
| keep_model_loaded | BOOLEAN | 保持模型加载 |
| max_tokens | INT | 最大生成长度 |
| preset_prompt | DROPDOWN | 预设提示词模板 |
| custom_prompt | STRING | 自定义提示词 |
| system_prompt | STRING | 系统提示词 |
| video_input | BOOLEAN | 是否视频模式 |
| max_frames / video_size | INT | 视频帧采样参数 |
| images（可选） | IMAGE | 输入图片 |

**输出:** `推理文本`

---

#### Luy-AI多功能语言大模型
**类别:** `luy/AI`

多功能文本处理节点，支持预设模板（从 `T/` 目录读取）。

| 参数 | 类型 | 说明 |
|------|------|------|
| model | DROPDOWN | 选择文本模型 |
| keep_model_loaded | BOOLEAN | 保持模型加载 |
| max_tokens | INT | 最大生成长度 |
| choice_type | DROPDOWN | 从 T/ 目录选择功能模板 |
| prompt | STRING | 用户输入 |
| seed | INT | 随机种子 |

**输出:** `输出提示词`

---

#### Luy-LlamaCpp本地API
**类别:** `luy/AI`

连接本地 llama.cpp HTTP 服务（OpenAI 兼容接口），支持图片分析。

| 参数 | 类型 | 说明 |
|------|------|------|
| url | STRING | API 服务器地址 |
| preset_prompt | DROPDOWN | 预设模板 |
| custom_prompt | STRING | 自定义提示词 |
| max_tokens | INT | 最大生成长度 |
| temperature | FLOAT | 温度参数 |
| images（可选） | IMAGE | 输入图片 |
| system_prompt（可选） | STRING | 系统提示词 |

**输出:** `output` / `system_prompt` / `user_prompt`

---

#### Luy-LlamaCpp反推（完整版）
**类别:** `llama-cpp-vlm`

全功能 llama.cpp VLM 节点，支持图片/视频分析、推测解码、MTP、状态保存。

| 主要参数 | 类型 | 说明 |
|---------|------|------|
| model / mmproj | DROPDOWN | 模型文件和投影文件 |
| chat_handler | DROPDOWN | 对话处理器 |
| n_ctx | INT | 上下文长度（默认 8192） |
| inference_mode | DROPDOWN | one by one / images / video |
| preset_prompt | DROPDOWN | 预设提示词 |
| max_tokens / temperature | INT/FLOAT | 生成参数 |
| draft_model_type | DROPDOWN | 推测解码类型 |
| enable_mtp | BOOLEAN | 多 Token 预测 |
| images（可选） | IMAGE | 输入图像 |

**输出:** `output` / `output_list` / `state_uid`

---

#### Luy-LlamaCpp反推（简化版）
**类别:** `llama-cpp-vlm`

简化版 VLM 节点，参数更少，适合快速使用。

**输出:** `output` / `output_list` / `state_uid`

---

### 模型加载类

#### Luy-加载lora模型(SDXL)
**类别:** `luy/模型加载`

SDXL 专用 LoRA 加载器，从 `loras/SDXL/` 子目录读取，支持标签频率筛选。

| 参数 | 类型 | 说明 |
|------|------|------|
| model | MODEL | 输入基础模型 |
| clip | CLIP | 输入 CLIP |
| lora_name | DROPDOWN | 选择 LoRA 文件 |
| strength_model / strength_clip | FLOAT | 权重 |
| selection_mode | DROPDOWN | 随机/最高/最低/中间频率 |
| tag_count | INT | 输出标签数量 |

**输出:** `模型` / `CLIP` / `内置触发词`

---

#### Luy-加载lora模型(FLUX|QWEN|QWEN-EDIT)
**类别:** `luy/模型加载`

仅模型（不含 CLIP）的 LoRA 加载器，从标准 loras 目录加载。

| 参数 | 类型 | 说明 |
|------|------|------|
| model | MODEL | 输入模型 |
| lora_name | DROPDOWN | LoRA 文件 |
| strength_model | FLOAT | 权重 |

**输出:** `模型` / `内置触发词`

---

#### Luy-通过目录加载lora模型
**类别:** `luy/模型加载`

支持按子目录浏览 LoRA 文件的动态加载器。先选目录，再选文件。

| 参数 | 类型 | 说明 |
|------|------|------|
| lora_dir | DROPDOWN | 选择 LoRA 子目录 |
| lora_name | DROPDOWN | 动态列出选中目录的文件 |

**输出:** 占位节点（功能待完善）

---

#### Luy-千问编码器
**类别:** `luy/Edit`

Qwen-Edit 图像编辑条件节点，支持最多 3 张参考图片。

| 参数 | 类型 | 说明 |
|------|------|------|
| clip | CLIP | 输入 CLIP |
| vae | VAE | 输入 VAE |
| image1/2/3（可选） | IMAGE | 参考图片 |
| funcType | STRING | 功能类型 |
| prompt | STRING | 提示词 |
| llama_template | STRING | 模板文本 |

**输出:** `positive` conditioning

---

### 图片处理类

#### Luy-Qwen3-VL图片反推
**类别:** `luy/AI`

见上方 AI 模型类。支持图片/视频帧分析和文字反推。

---

#### Luy-加载图片
**类别:** `luy/图片处理`

支持多图上传、EXIF 方向校正、RGBA 透明蒙版、多帧图片。

| 参数 | 类型 | 说明 |
|------|------|------|
| image | DROPDOWN | 选择输入目录的图片 |
| folder | FOLDER | 图片所在文件夹 |

**输出:** `IMAGE` / `MASK`

---

#### Luy-批量加载
**类别:** `luy/图片处理`

从 `input/batch/` 子目录加载批量图片。

| 参数 | 类型 | 说明 |
|------|------|------|
| batch | DROPDOWN | 选择批量子目录 |

**输出:** `image_batch` / `count`

---

#### Luy-图片绘画节点
**类别:** `luy/图片处理`

前端绘画板的结果处理节点，将绘制内容转为图片和颜色语义提示词。

| 参数 | 类型 | 说明 |
|------|------|------|
| canvas_width / canvas_height | INT | 画布大小 |
| edit_data | STRING | 前端传入的绘制数据 JSON |

**输出:** `edited_image` / `prompt`（颜色区域描述）

---

#### Luy-图片编辑节点
**类别:** `luy/图片处理`

前端图片编辑器的结果处理节点。

| 参数 | 类型 | 说明 |
|------|------|------|
| canvas_width / canvas_height | INT | 画布大小 |
| edit_data | STRING | 前端传入的编辑数据 JSON |

**输出:** `edited_image`

---

### 字符/文件处理类

#### Luy-字符串处理
**类别:** `luy/字符处理`

字符串拼接工具。

| 参数 | 类型 | 说明 |
|------|------|------|
| text1 | STRING | 文本 1 |
| join_type | DROPDOWN | 拼接方式：t1->t2 / t2->t1 / t2 / t1 |
| text2 | STRING | 文本 2 |

**输出:** `response`

---

#### Luy-循环取行文本
**类别:** `luy/字符处理`

将多行文本按行分割输出列表，支持随机计数。

| 参数 | 类型 | 说明 |
|------|------|------|
| text | STRING | 多行文本 |
| count | INT | 输出行数 |
| isRandom | BOOLEAN | 是否随机行数 |
| min / max | INT | 随机范围 |

**输出:** `array`（列表）/ `count`

---

#### Luy-读取txt文件
**类别:** `luy/文件处理`

读取指定目录中的 txt 文件内容。

| 参数 | 类型 | 说明 |
|------|------|------|
| dirPath | STRING | 目录路径 |
| count | INT | 输出文件数 |
| isRandom | BOOLEAN | 是否随机选择文件 |
| min_count / max_count | INT | 随机范围 |

**输出:** `array`（列表）/ `count`

---

#### Luy-写入txt到文件夹
**类别:** `luy/文件处理`

保存字符串到 txt 文件，自动生成时间戳文件名。

| 参数 | 类型 | 说明 |
|------|------|------|
| fileContent | STRING | 文件内容 |
| savePath | STRING | 保存目录 |

**输出:** `path` — 保存路径

---

### Latent 类

#### Luy-空Latent
**类别:** `luy/latent`

生成空白 Latent 张量。

| 参数 | 类型 | 说明 |
|------|------|------|
| width / height | INT | 尺寸（步长 16） |
| 宽高反转 | BOOLEAN | 是否交换宽高 |
| batch_size | INT | 批次大小 |

**输出:** `LATENT`

---

#### Luy-加载Latent
**类别:** `luy/latent`

从 `.latent` 文件加载 Latent 张量。

**输出:** `LATENT`

---

#### Luy-保存Latent
**类别:** `luy/latent`

将 Latent 保存为 `.latent` 文件。

| 参数 | 类型 | 说明 |
|------|------|------|
| samples | LATENT | 输入 Latent |
| filename_prefix | STRING | 文件名前缀 |

---

### 镜头控制类

#### Luy-镜头视角控制
**类别:** `luy/镜头控制`

3D 相机视角控制，将角度/缩放转为自然语言描述。

| 参数 | 类型 | 说明 |
|------|------|------|
| horizontal_angle | INT（滑块） | 水平角度 0-360° |
| vertical_angle | INT（滑块） | 垂直角度 -30°~90° |
| zoom | FLOAT（滑块） | 缩放 0~10 |

**输出:** `prompt` — 如"front-right view, high angle, medium shot"

**变体：**
- **Luy-镜头视角控制（魔改版）** — 标准方向命名
- **Luy-镜头视角控制（Lora标准版）** — 含 `<sks>` 前缀，含 1/4 视角方向

---

#### Luy-多角度光照控制节点
**类别:** `luy/镜头控制`

3D 光照控制节点，将方位角/仰角/强度/颜色转为自然语言光照描述。

| 参数 | 类型 | 说明 |
|------|------|------|
| light_azimuth | INT（滑块） | 光源水平方位 0-360° |
| light_elevation | INT（滑块） | 光源仰角 -90°~90° |
| light_intensity | FLOAT（滑块） | 光照强度 0~10 |
| light_color_hex | COLOR | 光源颜色 |
| cinematic_mode | BOOLEAN | 电影级光照描述 |
| image（可选） | IMAGE | 预览用图片 |

**输出:** `lighting_prompt`

---

### 视频生成类

#### Luy-PainterI2V图片转视频
**类别:** `luy/视频生成`

Wan2.2 图片转视频增强节点，解决 4 步 LoRA 慢动作问题。

| 参数 | 类型 | 说明 |
|------|------|------|
| positive / negative | CONDITIONING | 正向/负向条件 |
| vae | VAE | VAE 编码器 |
| width / height / length | INT | 视频尺寸和帧数 |
| batch_size | INT | 批次大小 |
| motion_amplitude | FLOAT | 运动幅度 1.0~2.0 |
| start_image / clip_vision（可选） | IMAGE | 起始帧参考 |

**输出:** `positive` / `negative` / `latent`

---

#### Luy-PainterI2V图片转视频高级版
**类别:** `luy/视频生成`

双采样器工作流的高级 I2V 节点，含色彩偏移修复。

| 额外参数 | 类型 | 说明 |
|---------|------|------|
| color_protect | BOOLEAN | 色彩保护 |
| correct_strength | FLOAT | 每通道色彩校正强度 |

**输出:** `high_positive` / `high_negative` / `low_positive` / `low_negative` / `latent`

---

#### Luy-Painter首尾帧
**类别:** `luy/视频生成`

首尾帧运动增强节点。使用"逆结构排斥"算法增强首帧到尾帧的运动幅度。

| 参数 | 类型 | 说明 |
|------|------|------|
| motion_amplitude | FLOAT | 运动幅度 1.0（原速）~2.0（高速） |
| start_image / end_image（可选） | IMAGE | 首帧/尾帧参考 |
| clip_vision_start/end（可选） | IMAGE | CLIP 视觉参考 |

**输出:** `positive` / `negative` / `latent`

---

#### Luy-Painter长视频增强
**类别:** `luy/视频生成`

长视频生成节点，支持分段链接、首尾帧锚定。

| 主要参数 | 类型 | 说明 |
|---------|------|------|
| motion_frames | INT | 运动帧数 |
| previous_video（可选） | LATENT | 上一段视频 Latent |
| initial_reference_image（可选） | IMAGE | 初始参考帧 |
| start/end images（可选） | IMAGE | 首尾帧图片 |

**输出:** `positive` / `negative` / `latent`

---

#### Luy-Painter首尾帧（多段）
**类别:** `Painter/Wan`

多关键帧视频生成器。支持最多 4 张关键帧图片，自动生成中间过渡段。

**输出:** `positive`（列表）/ `negative`（列表）/ `latent`（列表）/ `segment_count`

---

#### Luy-Flux2图像编辑
**类别:** `luy`

Flux 图像编辑节点，支持最多 3 张参考图和蒙版。

| 参数 | 类型 | 说明 |
|------|------|------|
| clip | CLIP | 输入 CLIP |
| prompt | STRING | 提示词 |
| width / height | INT | 输出尺寸 |
| vae（可选） | VAE | VAE |
| image1/2/3（可选） | IMAGE | 参考图片 |
| image1_mask（可选） | MASK | 蒙版 |

**输出:** `positive` / `negative` / `latent`

---

#### Luy-Flux2图像编辑（音频裁剪）
**类别:** `luy`

根据视频帧位置裁剪音频。

| 参数 | 类型 | 说明 |
|------|------|------|
| audio | AUDIO | 输入音频 |
| frame_rate | FLOAT | 帧率 |
| start_frame / end_frame | INT | 起止帧 |
| tail_silence_frames | INT | 末尾静音帧数 |

**输出:** `trimmed_audio` / `aligned_frames`

---

### 其他工具

#### Luy-清除显存占用
**类别:** `luy`

VRAM 管理节点。控制 ComfyUI 预留显存，可强制清理 GPU 模型缓存。

| 参数 | 类型 | 说明 |
|------|------|------|
| reserved | FLOAT | 预留显存(GB) |
| mode | DROPDOWN | manual / auto |
| auto_max_reserved | FLOAT | 自动模式最大预留 |
| clean_gpu_before | BOOLEAN | 执行前清理 |
| anything（可选） | ANY | 透传输入 |

**输出:** `output`（透传）/ `SEED` / `已释放(GB)`

---

#### Luy-视觉参考
**类别:** `conditioning/image_reference`

图片参考条件节点。将参考图编码为 Latent，注入到 Conditioning 中。

| 参数 | 类型 | 说明 |
|------|------|------|
| positive / negative | CONDITIONING | 条件输入 |
| vae | VAE | VAE |
| ref_image | IMAGE | 参考图片 |
| width / height | INT | 输出尺寸 |
| reference_strength | FLOAT | 参考强度 |
| latent_blend | FLOAT | Latent 混合比例 |

**输出:** `positive` / `negative` / `latent`

---

#### Luy-双CLIP加载器
**类别:** `luy`

加载两个文本编码器并组合。

| 参数 | 类型 | 说明 |
|------|------|------|
| clip_name1 / clip_name2 | DROPDOWN | 两个文本编码器 |
| type | DROPDOWN | 模型类型：sdxl/sd3/flux/hunyuan 等 |
| device（可选） | DROPDOWN | 设备：default/cpu/gpu |

**输出:** `CLIP`

---

#### Luy-视频旋转90度
**类别:** `luy`

PIL 和 Tensor 两种实现方式的视频 90° 旋转节点。

---

#### Luy-多帧视频处理
**类别:** `luy`

视频多帧处理工具。

---

#### Luy-跳过分支
**类别:** `luy`

条件分支跳过节点。

#### Luy-选择文件夹
**类别:** `luy`

文件夹路径选择节点。

---

#### Anima画师风格选择 / 角色Tag选择
**类别:** `luy/提示词`

风格和角色标签选择节点，从 `anima_style/` 和 `characters/` 目录读取数据。

---

## 安装

1. 将 `CJ-Nodes` 文件夹放入 ComfyUI 的 `custom_nodes/` 目录
2. 安装依赖（如 `llama-cpp-python` 等根据使用的节点按需安装）
3. 重启 ComfyUI
4. 在节点菜单中即可找到以 `Luy-` 开头的节点

---

## 注意事项

- LLM 节点（Qwen3、LlamaCpp 等）需要自行下载 GGUF 模型文件，放入 ComfyUI 的 `models/LLM` 目录
- 提示词节点需要准备对应的 txt 文件（参考 `prompt_options/` 等目录结构）
- "通过目录加载lora模型" 节点需在 `loras/` 下建立子目录分类存放 LoRA 文件
- 视频生成节点（Painter系列）需配合 Wan2.2 模型使用
- 插件的前端面板（本地资源、流程管理）显示在 ComfyUI 顶部工具栏

---

> 如有问题或建议，请联系作者。
