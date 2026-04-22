import os
import sys
import importlib.util
import traceback

# 初始化映射字典
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 自定义显示名映射（保留你原来的个性化名称）
CUSTOM_DISPLAY_NAMES = {
    "Any2Number": "Luy-Any2Number",
    "Any2String": "Luy-Any2String",
    "LuyEmptyLatentImage": "Luy-空Latent",
    "LuyLoadLatent": "Luy-加载Latent",
    "LuySaveLatent": "Luy-保存Latent",
    "SingleImageLoader": "Luy-单张图片加载",
    "StringArrayIndexer": "Luy-读取数组值",
    "PromptSelectorNode": "Luy-提示词Web选择器",
    "PromptGenerator":"Luy-画图提示词",
    "Wan22PromptSelector":"Luy-Wan2.2提示词",
    "ImageMaskNode": "Luy-添加蒙版",
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": "Luy-RGBA图层转视频",
    "MaskedImage2Png": "Luy-遮罩转PNG",
    "DrawImageBbox":"Luy-绘制Bbox",
    "LuySdxlLoraLoader": "Luy-加载lora模型(SDXL)",
    "LuyLoraLoaderModelOnlyALL": "Luy-加载lora模型(FLUX|QWEN|QWEN-EDIT)",
    "LuyLoraLoaderModelOnlyFLUX": "Luy-加载lora模型(FLUX)",
    "LuyLoraLoaderModelOnlyQWEN": "Luy-加载lora模型(QWEN)",
    "LuyLoraLoaderModelOnlyQWENEDIT": "Luy-加载lora模型(QWEN-EDIT)",
    "LuyLoraLoaderModelOnlyByDir":"Luy-通过目录加载lora模型",
    "UpdateLoraMetaData":"Luy-更新元数据",
    "QwenEditAddLlamaTemplate":"Luy-千问编码器",
    "ImageDeal":"Luy-Qwen3-VL图片反推",
    "ChatDeal":"Luy-GPT语言大模型",
    "Qwen3Deal":"Luy-Qwen3语言大模型",
    "MultiFunAINode":"Luy-AI多功能语言大模型",
    "StringJoinDeal":"Luy-字符串处理",
    "ForItemByIndex":"Luy-循环取行文本",
    "FileReadDeal":"Luy-读取txt文件",
    "FileSaveDeal":"Luy-写入txt到文件夹",
    "LoadImageUtils":"Luy-加载图片",
    "FolderSelectNode":"Luy-选择文件夹",
    "VRAMClean":"Luy-清除显存占用",
    "ConditionalSkip":"Luy-跳过分支",
    "LuyLoadImageBatch":"Luy-批量加载",
    "MultiFrameVideo":"Luy-多帧视频处理",
    "VisClipCopyImageReference":"Luy-视觉参考",
    "LuyWanImageToVideoSVIPro":"Luy-图像转视频SVIPlus",
    "QwenMultiangleCameraNode": "Luy-镜头视角控制（柯基版）",
    "QwenPlusMultiangleCameraNode": "Luy-镜头视角控制（魔改版）",
    "QwenLoraMultiangleCameraNode": "Luy-镜头视角控制（Lora标准版）",
    "QwenMultiangleLightningNode":"Luy-多角度光照控制节点",
    "EditPromptNode":"Luy-自定义提示词",
    "PainterFLF2V":"Luy-Painter首尾帧",
    "PainterLongVideo":"Luy-Painter长视频增强",
    "PainterI2V":"Luy-PainterI2V图片转视频",
    "PainterI2VAdvanced":"Luy-PainterI2V图片转视频高级版",
    "PainterFluxImageEdit": "Luy-Flux2图像编辑",
    "PainterAudioCut":"Luy-音频裁剪节点",
    "ImageEditNode":"Luy-绘画节点",
    "PromptPickerNode": "Luy-SDXL提示词选择器",
    "llama_run":"Luy-LlamaCpp反推",
    "llama_run_simple":"Luy-LlamaCpp反推(简化版)",
    "SDXLPromptPickerNode": "Luy-SDXL角色提示词",
    "LuySaveImage": "Luy-保存图片到本地",
    "LlamaCppAPINode": "Luy-LlamaCpp本地API",
    "LlamaCppAPIRefreshPrompts": "Luy-刷新提示词模板",
}

# 获取当前文件所在目录（你的CJ-Nodes目录）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# 定义service目录的绝对路径
SERVICE_DIR = os.path.join(CURRENT_DIR, "service")

# 关键修复1：将service目录加入Python路径，解决模块导入问题
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

# 递归加载指定目录下的所有节点文件
def load_nodes_from_file(file_path):
    try:
        # 生成唯一模块名，避免重复
        module_name = f"cj_nodes_{os.path.basename(file_path)[:-3]}"
        # 创建模块规范
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            print(f"无法创建模块规范: {file_path}")
            return

        # 创建并加载模块
        module = importlib.util.module_from_spec(spec)

        # 关键修复：将文件所在目录及其父目录添加到sys.path，确保相对导入能工作
        file_dir = os.path.dirname(file_path)
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)

        # 同时添加service目录，确保跨目录导入能工作
        parent_of_file_dir = os.path.dirname(file_dir)
        if parent_of_file_dir not in sys.path:
            sys.path.insert(0, parent_of_file_dir)

        # 不设置__package__，让相对导入基于sys.path解析
        module.__package__ = None

        spec.loader.exec_module(module)

        # 遍历模块中的所有类并添加到映射
        for member_name in dir(module):
            member = getattr(module, member_name)
            # 关键修复3：只导入「ComfyUI有效节点类」
            # 条件：是类 + 包含节点核心属性（INPUT_TYPES/RETURN_TYPES/FUNCTION）
            if (isinstance(member, type) and
                hasattr(member, "INPUT_TYPES") and
                hasattr(member, "RETURN_TYPES") and
                hasattr(member, "FUNCTION")):

                # 关键修复4：给节点类添加RELATIVE_PYTHON_MODULE属性，避免BytesIO报错
                if not hasattr(member, "RELATIVE_PYTHON_MODULE"):
                    setattr(member, "RELATIVE_PYTHON_MODULE", module_name)

                NODE_CLASS_MAPPINGS[member_name] = member
                # 设置显示名：优先用自定义名称，没有则用Luy-类名
                display_name = CUSTOM_DISPLAY_NAMES.get(member_name, f"Luy-{member_name}")
                NODE_DISPLAY_NAME_MAPPINGS[member_name] = display_name
                print(f"✅ 成功导入节点类: {member_name} (来自 {file_path})")

    except ImportError as e:
        print(f"❌ 加载文件 {file_path} 失败（模块缺失）: {e}")
        traceback.print_exc()  # 打印详细错误，方便定位缺失的模块
    except Exception as e:
        print(f"❌ 加载文件 {file_path} 失败: {e}")
        traceback.print_exc()

# 递归遍历目录
if os.path.exists(SERVICE_DIR):
    for root, dirs, files in os.walk(SERVICE_DIR):
        for filename in files:
            # 只处理.py文件，排除__init__.py和临时文件
            if filename.endswith(".py") and not filename.startswith("__"):
                file_path = os.path.join(root, filename)
                load_nodes_from_file(file_path)
else:
    print(f"⚠️ 警告：service目录不存在: {SERVICE_DIR}")

# 可选：打印加载结果，方便调试
print(f"\n📊 最终加载结果：共识别 {len(NODE_CLASS_MAPPINGS)} 个有效节点")
if NODE_CLASS_MAPPINGS:
    print(f"🔍 已加载的节点列表: {list(NODE_CLASS_MAPPINGS.keys())}")
else:
    print("⚠️ 未加载到任何有效节点，请检查：")
    print("  1. service目录下是否有包含节点属性的.py文件")
    print("  2. 节点类是否定义了INPUT_TYPES/RETURN_TYPES/FUNCTION")
    print("  3. 依赖模块（如qwen3vluntils）是否存在")

# 兼容ComfyUI的节点加载规范
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']