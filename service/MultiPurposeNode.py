import json
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
    from comfy.utils import get_path  # 用于获取ComfyUI的正确路径
    from comfy import config  # 用于获取ComfyUI配置
except ImportError:
    class BaseNode:
        pass
    # 兼容模式下的路径处理
    def get_path(path):
        return os.path.abspath(path)
    config = {"models_path": "models"}  # 默认模型路径

# 加载配置文件
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"prompts": {}, "models": {}}

config_data = load_config()

class MultiPurposeNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.prompt = ""
        self.tokenizers = {}  # 缓存tokenizer实例
        self.models = {}      # 缓存模型实例

    @classmethod
    def INPUT_TYPES(cls):
        # 获取配置中的模型和提示类型列表
        model_list = list(config_data["models"].keys())
        prompt_types = list(config_data["prompts"].keys())

        return {
            "required": {
                "模型选择": (model_list,),
                "功能选择": (prompt_types,),
                "提示词": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入提示词...",
                    "rows": 5
                })
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出提示词",)
    FUNCTION = "process_prompt"
    CATEGORY = "luy"

    def load_model_and_tokenizer(self, model_name):
        """加载模型和分词器，使用相对路径和缓存机制"""
        model_rel_path = config_data["models"].get(model_name)
        if not model_rel_path:
            raise ValueError(f"模型路径未找到: {model_name}")

        # 获取ComfyUI的模型根目录（从配置中读取，默认为"models"）
        models_root = config.get("models_path", "models")
        # 构建完整模型路径：ComfyUI模型根目录 + 配置中的相对路径
        full_path = get_path(os.path.join('ComfyUI',models_root, model_rel_path))

        # 检查路径是否存在
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"模型路径不存在: {full_path}")

        # 检查缓存
        if model_name in self.models and model_name in self.tokenizers:
            return self.models[model_name], self.tokenizers[model_name]

        # 加载tokenizer
        tokenizer = AutoTokenizer.from_pretrained(full_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # 加载模型
        model = AutoModelForCausalLM.from_pretrained(
            full_path,
            dtype="auto",
            device_map="cuda:0"
        )

        # 存入缓存
        self.models[model_name] = model
        self.tokenizers[model_name] = tokenizer

        return model, tokenizer

    def process_prompt(self, 模型选择, 功能选择, 提示词):
        # 获取选中的功能对应的提示词前缀
        prompt_prefix = config_data["prompts"].get(功能选择, "")
        # 组合完整提示词
        full_prompt = f"{prompt_prefix}\n{提示词}" if 提示词 else prompt_prefix
        try:
            # 加载模型和分词器
            model, tokenizer = self.load_model_and_tokenizer(模型选择)

            # 构建对话消息
            messages = [
                {"role": "user", "content": full_prompt}
            ]

            # 应用聊天模板
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )

            # 处理输入
            model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

            # 生成回复
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=32768
            )

            # 提取生成的内容
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            # 处理特殊标记
            try:
                # 找到结束标记
                index = len(output_ids) - output_ids[::-1].index(151668)
            except ValueError:
                index = 0

            # 解码输出
            content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
            return (content,)

        except Exception as e:
            # 错误处理，返回错误信息
            return (f"处理出错: {str(e)}",)