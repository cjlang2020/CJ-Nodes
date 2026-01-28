# CJ-Nodes Service 节点说明文档

## 概述

CJ-Nodes 是一个功能丰富的 ComfyUI 自定义节点集，涵盖了 AI 工具、图像处理、视频生成、提示词管理等多个领域。本文档详细介绍了 service 目录下所有节点的功能和使用方法。

---

## 🤖 AI 工具 (aitools)

### MultiFunAINode - 多功能 AI 节点
**功能**: 基于本地 LLM 模型的多功能文本处理节点
- **输入参数**:
  - `model`: LLM 模型选择
  - `keep_model_loaded`: 是否保持模型加载
  - `max_tokens`: 最大生成 token 数 (0-4096)
  - `choice_type`: 预设提示词类型 (从 T 目录读取)
  - `prompt`: 自定义提示词
  - `seed`: 随机种子
- **输出**: 输出提示词 (STRING)
- **特点**: 自动读取 T 目录下的提示词文件，支持多种文本处理任务

### Qwen3Chat - Qwen3 文本对话
**功能**: 专用于 Qwen3 模型的文本对话节点
- **输入参数**:
  - `model`: Qwen3 模型选择
  - `keep_model_loaded`: 是否保持模型加载
  - `max_tokens`: 最大生成 token 数
  - `prompt`: 对话提示词
  - `seed`: 随机种子
- **输出**: 对话输出 (STRING)
- **特点**: 针对 Qwen3 优化，禁用 think 模式

### Qwen3VlImage - Qwen3-VL 视觉理解
**功能**: Qwen3-VL 多模态模型的图像理解节点
- **输入参数**:
  - `model`: 视觉模型选择
  - `mmproj_model`: 多模态投影模型
  - `keep_model_loaded`: 是否保持模型加载
  - `max_tokens`: 最大生成 token 数
  - `preset_prompt`: 预设提示词 (从 V 目录读取)
  - `custom_prompt`: 自定义提示词
  - `system_prompt`: 系统提示词
  - `video_input`: 是否为视频输入
  - `max_frames`: 最大帧数
  - `video_size`: 视频尺寸
  - `images`: 输入图像 (可选)
- **输出**: 推理文本 (STRING)
- **特点**: 支持图像和视频理解，自动读取 V 目录预设

---

## 📁 文件处理 (filetools)

### FileReadDeal - 文件读取处理
**功能**: 批量读取目录下的文本文件
- **输入参数**:
  - `dirPath`: 目录路径
  - `count`: 读取文件数量
  - `isRandom`: 是否随机选择
  - `min_count`: 随机模式最小数量
  - `max_count`: 随机模式最大数量
- **输出**: 
  - 文件内容数组 (STRING LIST)
  - 实际读取数量 (INT)
- **特点**: 支持 .txt 文件批量读取，可随机或顺序选择

### FileSaveDeal - 文件保存处理
**功能**: 将文本内容保存到指定目录
- **输入参数**:
  - `fileContent`: 文件内容
  - `savePath`: 保存路径
- **输出**: 保存路径 (STRING)
- **特点**: 自动生成时间戳文件名

---

## 🖼️ 图像处理 (imagetools)

### BatchImageLoader - 批量图像加载
**功能**: 从文件夹批量加载图像
- **输入参数**:
  - `image_folder`: 图像文件夹路径
  - `max_images`: 最大加载图像数量
  - `resize`: 是否调整尺寸
  - `target_width`: 目标宽度
  - `target_height`: 目标高度
- **输出**: 
  - 图片批量数据 (IMAGE LIST)
  - 图片路径列表 (STRING LIST)
- **特点**: 支持多种图像格式，可批量调整尺寸

### ImagePathScanner - 图像路径扫描
**功能**: 扫描文件夹返回图像路径列表
- **输入参数**:
  - `image_folder`: 图像文件夹路径
- **输出**: 
  - 路径列表 (JSON 字符串)
  - 图片数量 (INT)
- **特点**: 返回 JSON 格式的路径列表

### SingleImageLoader - 单张图像加载
**功能**: 加载单张指定路径的图像
- **输入参数**:
  - `image_path`: 图像文件路径
  - `resize`: 是否调整尺寸
  - `target_width`: 目标宽度
  - `target_height`: 目标高度
- **输出**: 图片数据 (IMAGE)
- **特点**: 支持绝对路径和相对路径

### StringArrayIndexer - 字符串数组索引
**功能**: 从 JSON 路径列表中按索引获取路径
- **输入参数**:
  - `path_list_json`: JSON 格式的路径列表
  - `index`: 数组索引
- **输出**: 索引对应值 (STRING)
- **特点**: 解析 JSON 字符串，支持负索引

### DrawPhotoNode - 手绘照片节点
**功能**: 基于鼠标绘制数据生成图像
- **输入参数**:
  - `canvas_width`: 画布宽度
  - `canvas_height`: 画布高度
  - `draw_data`: 绘制数据 (JSON)
- **输出**: 绘制图像 (IMAGE)
- **特点**: 支持画笔、橡皮擦、背景色等绘制功能

### ImageCropNode - 图像裁剪
**功能**: 基于前端裁剪数据裁剪图像
- **输入参数**:
  - `canvas_width`: 画布宽度
  - `canvas_height`: 画布高度
  - `crop_data`: 裁剪数据 (JSON)
- **输出**: 裁剪图像 (IMAGE)
- **特点**: 支持可视化裁剪区域

### ImageDrawNode - Base64 图像转换
**功能**: 将 Base64 字符串转换为 ComfyUI 图像
- **输入参数**:
  - `base64_string`: Base64 编码的图像字符串
- **输出**: 输出图片 (IMAGE)
- **特点**: 支持各种图像格式的 Base64 解码

### ImageMaskNode - 图像蒙版生成
**功能**: 在图像指定区域生成蒙版
- **输入参数**:
  - `images`: 输入图像
  - `x`: 区域起点 X
  - `y`: 区域起点 Y
  - `width`: 区域宽度
  - `height`: 区域高度
- **输出**: 
  - 输出图片 (IMAGE)
  - 输出蒙版 (MASK)
- **特点**: 将指定区域涂黑并生成对应蒙版

### ImageEditNode - 图像编辑
**功能**: 基于前端编辑数据处理图像
- **输入参数**:
  - `canvas_width`: 画布宽度
  - `canvas_height`: 画布高度
  - `edit_data`: 编辑数据 (JSON)
- **输出**: 编辑图像 (IMAGE)
- **特点**: 支持画笔、液化、橡皮擦等编辑功能

### LoadImageUtils - 图像加载工具
**功能**: 多功能图像加载节点
- **输入参数**:
  - `image`: 图像文件 (支持多选)
  - `folder`: 文件夹路径
- **输出**: 
  - 图像数据 (IMAGE)
  - 图像蒙版 (MASK)
- **特点**: 支持单张/多张图像加载，自动处理蒙版

---

## 🎭 Latent 工具 (latenttools)

### LuyEmptyLatentImage - 空 Latent 生成
**功能**: 创建指定尺寸的空 Latent 张量
- **输入参数**:
  - `width`: 宽度
  - `height`: 高度
  - `swap_dimensions`: 宽高反转
  - `batch_size`: 批次大小
- **输出**: LATENT
- **特点**: 生成用于扩散模型的初始 Latent

### LuySaveLatent - Latent 保存
**功能**: 将 Latent 保存为文件
- **输入参数**:
  - `samples`: Latent 数据
  - `filename_prefix`: 文件名前缀
- **输出**: 无 (输出节点)
- **特点**: 保存 Latent 供后续使用

### LuyLoadLatent - Latent 加载
**功能**: 从文件加载 Latent
- **输入参数**:
  - `latent_name`: Latent 文件选择
- **输出**: LATENT
- **特点**: 加载之前保存的 Latent

---

## 🎨 LoRA 模型工具 (loramodeltools)

### LuySdxlLoraLoader - SDXL LoRA 加载器
**功能**: 专门为 SDXL 模型设计的 LoRA 加载器
- **输入参数**:
  - `model`: 基础模型
  - `clip`: CLIP 模型
  - `lora_name`: LoRA 名称
  - `strength_model`: 模型强度
  - `strength_clip`: CLIP 强度
  - `select_mode`: 选择模式
  - `label_count`: 标签数量
- **输出**: 
  - 模型 (MODEL)
  - CLIP (CLIP)
  - 内置触发词 (STRING)
- **特点**: 自动提取 LoRA 标签，支持 SDXL

### LuyLoraLoaderModelOnlyALL - 通用 LoRA 加载器
**功能**: 仅加载模型的通用 LoRA 加载器
- **输入参数**:
  - `model`: 基础模型
  - `lora_name`: LoRA 名称
  - `strength`: 强度
- **输出**: 
  - 模型 (MODEL)
  - 内置触发词 (STRING)
- **特点**: 适用于各种模型类型

### 专用 LoRA 加载器
- **LuyLoraLoaderModelOnlyFLUX**: FLUX 模型专用
- **LuyLoraLoaderModelOnlyQWEN**: Qwen 模型专用
- **LuyLoraLoaderModelOnlyQWENEDIT**: Qwen-Edit 模型专用

### UpdateLoraMetaData - LoRA 元数据更新
**功能**: 为 LoRA 添加关键词元数据
- **输入参数**:
  - `lora_name`: LoRA 名称
  - `keywords`: 关键词
- **输出**: 字符串 (STRING)
- **特点**: 便于 LoRA 管理和检索

### LuyLoraLoaderModelOnlyByDir - 按目录 LoRA 加载
**功能**: 动态选择文件夹中的 LoRA
- **输入参数**:
  - `folder`: 文件夹选择
  - `lora_name`: LoRA 名称
- **输出**: 无 (输出节点)
- **特点**: 支持动态文件夹选择

---

## 📝 字符串工具 (stringtools)

### Any2String / Any2Number - 类型转换
**功能**: 将任意输入转换为字符串或数字
- **输入参数**:
  - `any`: 任意类型输入
- **输出**: 字符串 (STRING)
- **特点**: 类型安全转换

### ForItemByIndex - 按索引处理文本
**功能**: 按行分割文本并重复指定次数
- **输入参数**:
  - `text`: 输入文本
  - `count`: 重复次数
  - `isRandom`: 是否随机
  - `min_count`: 最小数量
  - `max_count`: 最大数量
- **输出**: 
  - 字符串数组 (STRING LIST)
  - 数量 (INT)
- **特点**: 支持随机和顺序处理

### StringJoinDeal - 字符串连接
**功能**: 按不同方式连接两个字符串
- **输入参数**:
  - `text1`: 文本1
  - `join_type`: 连接方式
  - `text2`: 文本2
- **输出**: 字符串 (STRING)
- **特点**: 支持多种连接模式

---

## 💬 提示词工具 (prompttools)

### EditPromptNode - 动态提示词编辑器
**功能**: 动态读取文件生成提示词
- **输入参数**:
  - `custom_file_path`: 自定义文件路径
  - `enable_selection`: 启用选择
  - 各种提示词选项文件
- **输出**: 
  - 中文标签 (STRING)
  - 英文标签 (STRING)
  - 中英混合标签 (STRING)
  - 包含主题内容 (STRING)
- **特点**: 支持多种提示词格式

### PromptSelectorNode - 提示词选择器
**功能**: 选择和处理提示词
- **输入参数**:
  - `prompt`: 输入提示词
  - 各种处理选项
- **输出**: 输出提示词 (STRING)
- **特点**: 灵活的提示词处理

### PromptGenerator - 提示词生成器
**功能**: 基于文件生成多种格式提示词
- **输入参数**:
  - 各种文件选项
- **输出**: 
  - 中文标签 (STRING)
  - 英文标签 (STRING)
  - 中英混合标签 (STRING)
  - 包含主题内容 (STRING)
- **特点**: 批量生成提示词

### Wan22PromptSelector - Wan2.2 提示词选择器
**功能**: 为视频生成生成专业提示词
- **输入参数**:
  - `scene_type`: 场景类型
  - `motion_scene`: 运动场景
  - `emotion`: 情绪
  - `camera_movement`: 运镜
  - 其他视频参数
- **输出**: 提示词 (STRING)
- **特点**: 专为视频生成优化

---

## 🎬 PrincePainter 视频生成工具 (princepainter)

### 音频处理节点

#### PainterAudioCut - 音频裁剪
**功能**: 按帧裁剪音频并自动对齐
- **输入参数**:
  - `audio`: 输入音频
  - `fps`: 帧率
  - `start_frame`: 起始帧
  - `end_frame`: 结束帧
  - `tail_silence_frames`: 尾部静音帧
- **输出**: 
  - 裁剪后音频 (AUDIO)
  - 对齐帧数 (INT)
- **特点**: 精确的音频时间轴对齐

### 图像编辑节点

#### PainterFluxImageEdit - Flux 图像编辑
**功能**: 支持多图像的 Flux 编辑
- **输入参数**:
  - `clip`: CLIP 模型
  - `prompt`: 提示词
  - `width`: 宽度
  - `height`: 高度
  - `image1-3`: 最多3张图像
  - `mask1-3`: 对应掩码
- **输出**: 
  - 正向条件 (CONDITIONING)
  - 负向条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 支持多图像编辑

### 视频生成节点

#### PainterFLF2V - 首尾帧视频生成
**功能**: 基于首尾帧生成视频
- **输入参数**:
  - `positive`: 正向条件
  - `negative`: 负向条件
  - `vae`: VAE 模型
  - `width`: 宽度
  - `height`: 高度
  - `length`: 视频长度
  - `motion`: 运动幅度
  - `start_image`: 起始图像
  - `end_image`: 结束图像
- **输出**: 
  - 正向条件 (CONDITIONING)
  - 负向条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 支持动态增强

#### PainterAI2V - AI 音频驱动视频
**功能**: 音频驱动的口型同步视频生成
- **输入参数**:
  - `dual_model`: 双模型
  - `audio`: 音频输入
  - `positive`: 正向条件
  - `negative`: 负向条件
  - `vae`: VAE 模型
  - `image`: 参考图像
- **输出**: 
  - 高噪声模型 (MODEL)
  - 低噪声模型 (MODEL)
  - 条件 (CONDITIONING)
  - Latent (LATENT)
  - 裁剪图像 (IMAGE)
- **特点**: 精确的口型同步

#### PainterAV2V - 音频视频转视频
**功能**: 基于现有视频和音频生成新视频
- **输入参数**:
  - `model`: 模型
  - `audio`: 音频
  - `video`: 视频
  - `positive`: 正向条件
  - `negative`: 负向条件
  - `vae`: VAE 模型
- **输出**: 
  - 模型 (MODEL)
  - 条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 视频风格迁移

#### PainterI2V - 图像转视频
**功能**: 修复慢动作问题的图像转视频
- **输入参数**:
  - `positive`: 正向条件
  - `negative`: 负向条件
  - `vae`: VAE 模型
  - `width`: 宽度
  - `height`: 高度
  - `length`: 视频长度
  - `motion`: 运动幅度
  - `start_image`: 起始图像
- **输出**: 
  - 条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 优化慢动作生成

#### PainterI2VAdvanced - 高级图像转视频
**功能**: 双采样器工作流的防色偏 I2V
- **输入参数**:
  - 基础 I2V 参数 +
  - `color_protect`: 颜色保护
  - `correction_strength`: 校正强度
- **输出**: 
  - 高正向条件 (CONDITIONING)
  - 低正向条件 (CONDITIONING)
  - 高负向条件 (CONDITIONING)
  - 低负向条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 防止颜色偏移

#### PainterLongVideo - 长视频生成
**功能**: 支持多种约束的长视频生成
- **输入参数**:
  - `positive`: 正向条件
  - `negative`: 负向条件
  - `vae`: VAE 模型
  - `width`: 宽度
  - `height`: 高度
  - `length`: 视频长度
  - `motion_frames`: 运动帧
  - 各种图像输入
- **输出**: 
  - 条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 支持长视频生成

#### PainterMultiF2V - 多首尾帧视频
**功能**: 生成多个视频段
- **输入参数**:
  - `clip`: CLIP 模型
  - `vae`: VAE 模型
  - `images`: 图像列表
  - `prompts`: 提示词列表
- **输出**: 
  - 条件列表 (CONDITIONING LIST)
  - Latent 列表 (LATENT LIST)
  - 段数 (INT)
- **特点**: 批量视频段生成

### 工具节点

#### PainterCombineFromBatch - 批次视频合并
**功能**: 将多个视频段平滑合并
- **输入参数**:
  - `images`: 图像列表
  - `overlap_frames`: 重叠帧
  - `crop_frames`: 裁剪帧
- **输出**: 合并后图像 (IMAGE)
- **特点**: 无缝视频合并

#### PainterPrompt - Painter 提示词工具
**功能**: 组合和管理多个提示词
- **输入参数**:
  - 多个提示词输入
- **输出**: 提示词列表 (STRING LIST)
- **特点**: 提示词批量管理

---

## 🔧 根目录工具节点

### LuyWanImageToVideoSVIPro - SVI 专业图像转视频
**功能**: 基于多重约束的专业级 I2V
- **输入参数**:
  - `positive`: 正向条件
  - `reference_image`: 参考图片
  - `prev_segment_latent`: 上一段 Latent
  - `tail_frame`: 尾帧
  - 各种专业参数
- **输出**: 
  - 条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 专业级视频生成

### QwenEditAddLlamaTemplate - Qwen 编辑模板
**功能**: 为 Qwen 模型添加 Llama 模板支持
- **输入参数**:
  - `clip`: CLIP 模型
  - `vae`: VAE 模型
  - `image`: 图像
  - `prompt`: 提示词
  - `llama_template`: Llama 模板
- **输出**: 条件 (CONDITIONING)
- **特点**: 模板兼容性增强

### QwenMultiangleCameraNode - 多角度相机控制
**功能**: 3D 相机角度控制和提示词生成
- **输入参数**:
  - `horizontal_angle`: 水平角度
  - `vertical_angle`: 垂直角度
  - `zoom`: 缩放
  - `image`: 参考图像
- **输出**: 提示词 (STRING)
- **特点**: 3D 空间控制

### VisClipCopy - 纯图片参考
**功能**: 图片参考控制
- **输入参数**:
  - `positive`: 正向条件
  - `negative`: 负向条件
  - `vae`: VAE 模型
  - `reference_image`: 参考图像
  - 各种控制参数
- **输出**: 
  - 条件 (CONDITIONING)
  - Latent (LATENT)
- **特点**: 兼容 4/16 通道 VAE

### VramClean - 显存清理
**功能**: 智能显存管理和清理
- **输入参数**:
  - `reserve_vram`: 预留显存
  - `mode`: 清理模式
  - `seed`: 随机种子
  - 各种清理选项
- **输出**: 
  - 输出 (STRING)
  - 种子 (INT)
  - 已释放显存 (STRING)
- **特点**: 智能显存优化

---

## 📂 目录结构说明

### 预设文件目录
- **`aitools/T/`**: 文本处理预设提示词文件
- **`aitools/V/`**: 视觉理解预设提示词文件
- **`prompttools/prompt_options/`**: 提示词选项文件 (30个分类)

### 支持的文件格式
- **图像**: .jpg, .jpeg, .png, .bmp, .gif, .webp
- **文本**: .txt
- **模型**: .gguf (LLM), .safetensors (LoRA)

---

## 🎯 使用建议

### 工作流组合
1. **AI 文本处理**: MultiFunAINode → StringJoinDeal → EditPromptNode
2. **图像处理**: BatchImageLoader → ImageEditNode → PainterI2V
3. **视频生成**: Qwen3VlImage → PainterFLF2V → PainterCombineFromBatch
4. **LoRA 管理**: LuySdxlLoraLoader → UpdateLoraMetaData → 生成工作流

### 性能优化
- 使用 VramClean 节点管理显存
- 合理设置 `keep_model_loaded` 参数
- 批量处理时使用 BatchImageLoader

### 兼容性说明
- 支持 ComfyUI 最新版本
- 兼容 SDXL, FLUX, Qwen 等主流模型
- 跨平台支持 (Windows/Linux/macOS)

---

## 📝 更新日志

本文档基于 CJ-Nodes 当前版本生成，涵盖了 service 目录下所有节点的详细说明。如有更新或疑问，请参考项目 README 或提交 Issue。

---

*最后更新: 2026年1月*