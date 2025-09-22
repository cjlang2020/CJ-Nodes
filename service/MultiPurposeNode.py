import json
import os
import folder_paths
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    from comfy.nodes import BaseNode
    from comfy.utils import get_path
    from comfy import config
except ImportError:
    class BaseNode:
        pass
    def get_path(path):
        return os.path.abspath(path)
    config = {"models_path": "models"}

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
        self.tokenizers = {}
        self.models = {}

    @classmethod
    def INPUT_TYPES(cls):
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

        full_path = folder_paths.models_dir + '/' + model_rel_path;
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"模型路径不存在: {full_path}")

        if model_name in self.models and model_name in self.tokenizers:
            return self.models[model_name], self.tokenizers[model_name]

        tokenizer = AutoTokenizer.from_pretrained(full_path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = AutoModelForCausalLM.from_pretrained(
            full_path,
            dtype="auto",
            device_map="cuda:0"
        )
        self.models[model_name] = model
        self.tokenizers[model_name] = tokenizer

        return model, tokenizer

    def process_prompt(self, 模型选择, 功能选择, 提示词):
        prompt_prefix = config_data["prompts"].get(功能选择, "")
        full_prompt = f"{prompt_prefix}\n{提示词}" if 提示词 else prompt_prefix
        try:
            model, tokenizer = self.load_model_and_tokenizer(模型选择)
            messages = [
                {"role": "user", "content": full_prompt}
            ]
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False
            )
            model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
            generated_ids = model.generate(
                **model_inputs,
                max_new_tokens=32768
            )
            output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()
            try:
                index = len(output_ids) - output_ids[::-1].index(151668)
            except ValueError:
                index = 0
            content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip()
            return (content,)

        except Exception as e:
            return (f"处理出错: {str(e)}",)