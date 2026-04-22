"""
AITools 共享基础模块
统一管理模型加载、配置读取、提示词处理等功能
"""
import os
import json
import gc
import re
import base64
import folder_paths
import comfy.model_management as mm
import numpy as np
from io import BytesIO
from PIL import Image
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Qwen3VLChatHandler


# ======================== 常量定义 ========================
INVALID_CHARS = r'\/:*?"<>|'
EXCLUDE_FILES = ['.DS_Store', 'Thumbs.db', 'desktop.ini']

# 预编译正则表达式提升性能
THINK_PATTERN = re.compile(r"```[\s\S]*?think[\s\S]*?```", re.IGNORECASE)
THINK_KEYWORDS_PATTERN = re.compile(r"思考|分析|推理|步骤|```[\s\S]*?```")
CLEANUP_PATTERN = re.compile(r"```|think|\u200b")


# ======================== 模型注册 ========================
def register_llm_folder():
    """注册LLM模型目录到folder_paths"""
    llm_extensions = ['.gguf']
    folder_paths.folder_names_and_paths["LLM"] = (
        [os.path.join(folder_paths.models_dir, "LLM")],
        llm_extensions
    )


# ======================== 辅助函数 ========================
def is_valid_file(file_name):
    """校验是否为有效可读取的文件"""
    if file_name in EXCLUDE_FILES:
        return False
    if file_name.startswith(('.', '~')):
        return False
    return True


def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"prompts": {}, "models": {}}


def load_prompt_files(prompt_dir):
    """读取指定目录下的所有有效文件"""
    prompts = {}
    if not os.path.exists(prompt_dir) or not os.path.isdir(prompt_dir):
        print(f"[警告] prompt目录不存在或非法：{prompt_dir}")
        return prompts

    for file_item in os.listdir(prompt_dir):
        file_abspath = os.path.join(prompt_dir, file_item)
        if os.path.isfile(file_abspath) and is_valid_file(file_item):
            try:
                with open(file_abspath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()
                prompts[file_item] = content
                print(f"[成功] 加载prompt文件：{file_item}")
            except Exception as e:
                print(f"[警告] 读取prompt文件失败 {file_abspath} : {str(e)[:80]}")
    return prompts


def get_chat_handler(model_type):
    """获取聊天处理器"""
    if model_type == "Qwen3-VL":
        return Qwen3VLChatHandler
    elif model_type in ("None", "llama"):
        return None
    else:
        print(f"[警告] 未知的模型类型: {model_type}, 使用默认处理")
        return None


def clean_think_content(text):
    """清理think标签内容"""
    text = THINK_PATTERN.sub("", text)
    text = CLEANUP_PATTERN.sub("", text)
    return text.lstrip(": ").lstrip().rstrip()


def clean_prompt_keywords(prompt):
    """过滤提示词中的思维链引导语句"""
    return THINK_KEYWORDS_PATTERN.sub("", prompt)


# ======================== 图像处理函数 ========================
def scale_image(image, target_size):
    """缩放图像到目标尺寸"""
    if isinstance(image, np.ndarray):
        if image.dtype != np.uint8:
            image = np.clip(255.0 * image, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image)
    else:
        pil_image = image

    pil_image.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
    return np.array(pil_image)


def image2base64(image_array):
    """将numpy数组转换为base64字符串"""
    if isinstance(image_array, np.ndarray):
        if image_array.dtype != np.uint8:
            image_array = np.clip(255.0 * image_array, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_array)
    else:
        pil_image = image_array

    buffer = BytesIO()
    pil_image.save(buffer, format='JPEG', quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# ======================== 模型管理类 ========================
class BaseModelManager:
    """统一的模型管理基类"""

    def __init__(self):
        self.llm = None
        self.chat_handler = None
        self.current_config = None

    def cleanup(self):
        """清理模型资源"""
        if self.llm is not None:
            try:
                self.llm.close()
            except Exception as e:
                print(f"[警告] 关闭LLM时出错: {str(e)[:100]}")
            self.llm = None

        if self.chat_handler is not None:
            try:
                self.chat_handler._exit_stack.close()
            except Exception as e:
                print(f"[警告] 关闭chat_handler时出错: {str(e)[:100]}")
            self.chat_handler = None

        gc.collect()
        mm.soft_empty_cache()

    def load_model(self, config):
        """加载模型"""
        model = config["model"]
        mmproj_model = config.get("mmproj_model")
        model_type = config.get("model_type", "Qwen3-VL")
        think_mode = config.get("think_mode", False)
        n_ctx = config.get("n_ctx", 8192)
        n_gpu_layers = config.get("n_gpu_layers", -1)

        model_path = os.path.join(folder_paths.models_dir, 'LLM', model)
        chat_handler = None

        # 加载mmproj（如果需要）
        if mmproj_model and mmproj_model != "None":
            mmproj_path = os.path.join(folder_paths.models_dir, 'LLM', mmproj_model)
            if model_type == "None":
                raise ValueError('"model_type" cannot be None when mmproj is specified!')
            print(f"[加载] mmproj from {mmproj_path}")
            handler = get_chat_handler(model_type)
            if handler and model_type == "Qwen3-VL":
                chat_handler = handler(clip_model_path=mmproj_path, use_think_prompt=think_mode, verbose=False)
            elif handler:
                chat_handler = handler(clip_model_path=mmproj_path, verbose=False)

        print(f"[加载] model from {model_path}")

        # 模型初始化只传入必要参数，采样参数在推理时传入
        llm = Llama(
            model_path,
            chat_handler=chat_handler,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=False
        )

        return (chat_handler, llm)

    def get_or_reload_model(self, config):
        """获取或重新加载模型"""
        mm.soft_empty_cache()

        if self.llm is None or self.current_config != config:
            self.cleanup()
            self.current_config = config
            self.chat_handler, self.llm = self.load_model(config)

        return self.llm, self.chat_handler


# ======================== 提示词管理类 ========================
class PromptManager:
    """统一的提示词管理"""

    def __init__(self, prompt_dir):
        self.prompts = {}
        self.prompt_dir = prompt_dir
        self._load_prompts()

    def _load_prompts(self):
        """加载提示词文件"""
        self.prompts = load_prompt_files(self.prompt_dir)

    def refresh(self):
        """刷新提示词文件"""
        self.prompts.clear()
        self._load_prompts()

    def get_prompt_types(self):
        """获取提示词类型列表"""
        if self.prompts:
            return list(self.prompts.keys())
        return ["请放入提示词文件"]

    def get_prompt_content(self, choice_type):
        """获取指定类型的提示词内容"""
        return self.prompts.get(choice_type, "")

    def build_final_prompt(self, preset_prompt, custom_prompt, video_input=False):
        """构建最终提示词"""
        user_content = []

        if custom_prompt.strip():
            if preset_prompt.startswith('@') and preset_prompt in self.prompts:
                preset_text = self.prompts[preset_prompt]
                preset_text = preset_text.replace('{', '{{').replace('}', '}}').replace('{{}}', '{}')
                final_text = preset_text.format(custom_prompt)
                user_content.append({"type": "text", "text": final_text})
            else:
                user_content.append({"type": "text", "text": custom_prompt})
        else:
            if preset_prompt in self.prompts and preset_prompt != "请放入提示词文件":
                preset_text = self.prompts[preset_prompt]
                preset_text = preset_text.replace("@", "video" if video_input else "image")
                user_content.append({"type": "text", "text": preset_text})
            else:
                user_content.append({"type": "text", "text": ""})

        return user_content


# ======================== 初始化 ========================
# 注册LLM目录
register_llm_folder()