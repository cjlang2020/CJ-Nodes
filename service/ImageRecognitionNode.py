import json
import os
import folder_paths
import torch
import numpy as np
from PIL import Image
from transformers import AutoTokenizer, AutoModelForCausalLM

try:
    from comfy.nodes import BaseNode
    from comfy.utils import get_path
    from comfy import config
except ImportError:
    class BaseNode:
        pass
    def get_path(path):
        return os.path.abspath(path)
    config = {"models_path": "image_models"}

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"image_models": {}}

config_data = load_config()

class ImageRecognitionNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.tokenizers = {}
        self.models = {}
        # FastVLM特定的图像标记索引（关键修复）
        self.IMAGE_TOKEN_INDEX = -200

    @classmethod
    def INPUT_TYPES(cls):
        model_list = list(config_data["image_models"].keys())
        return {
            "required": {
                "模型选择": (model_list,),
                "图片输入": ("IMAGE",),
                "提示词": ("STRING", {
                    "default": "<image>\n用中文简要描述这张图片风格、布局、存在的元素等。",
                    "multiline": True,
                    "placeholder": "请输入关于图片的提示词...",
                    "rows": 5
                }),
                "最大生成长度": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 65536,
                    "step": 1,
                    "display": "number"
                }),
                "运行后清理GPU缓存": (["否", "是"],),
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("识别结果",)
    FUNCTION = "recognize_image"
    CATEGORY = "luy"

    def load_model_and_tokenizer(self, model_name):
        model_rel_path = config_data["image_models"].get(model_name)
        if not model_rel_path:
            raise ValueError(f"模型路径未找到: {model_name}")

        full_path = os.path.join(folder_paths.models_dir, model_rel_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"模型路径不存在: {full_path}")

        if model_name in self.models and model_name in self.tokenizers:
            return self.models[model_name], self.tokenizers[model_name]

        # 加载模型和分词器，与测试代码完全一致
        tokenizer = AutoTokenizer.from_pretrained(full_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            full_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
        )

        # 设置pad_token（FastVLM需要）
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        self.models[model_name] = model
        self.tokenizers[model_name] = tokenizer
        return model, tokenizer

    def recognize_image(self, 模型选择, 图片输入, 提示词, 最大生成长度, 运行后清理GPU缓存):
        if not 提示词.strip():
            提示词 = "<image>\n用中文描述这张图片风格、布局、存在的元素等,返回结果不允许出现：这张图片表现或者图片展示什么等这样的描述，直接输出描述部分。"
        else:
            if "<image>" not in 提示词:
                提示词 = "<image>\n" + 提示词
        try:
            # 加载模型（与测试代码一致）
            model, tokenizer = self.load_model_and_tokenizer(模型选择)

            # 处理图片输入（转换为PIL Image，与测试代码的Image.open效果一致）
            img = 图片输入[0]
            if isinstance(img, torch.Tensor):
                # 转换Tensor为PIL Image
                img = img.cpu()
                # 如果是0-1范围的float，转换为0-255的uint8
                if img.dtype == torch.float32 and img.max() <= 1.0:
                    img = (img * 255).byte()
                # 处理通道顺序 (C, H, W) -> (H, W, C)
                if img.dim() == 3 and img.shape[0] in (1, 3, 4):
                    img = img.permute(1, 2, 0)
                img_np = img.numpy()
            else:
                img_np = np.array(img)
                if img_np.max() <= 1.0:
                    img_np = (img_np * 255).astype(np.uint8)

            # 确保是3通道RGB
            img_np = img_np.squeeze()  # 去除单通道维度
            if img_np.ndim == 2:
                image = Image.fromarray(img_np, mode='L').convert('RGB')
            else:
                image = Image.fromarray(img_np).convert('RGB')

            # 构建输入（完全复刻测试代码的逻辑）
            messages = [{"role": "user", "content": 提示词}]
            rendered = tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, tokenize=False
            )

            # 分割并插入图像标记
            pre, post = rendered.split("<image>", 1)
            pre_ids = tokenizer(pre, return_tensors="pt", add_special_tokens=False).input_ids
            post_ids = tokenizer(post, return_tensors="pt", add_special_tokens=False).input_ids

            # 使用硬编码的图像标记索引（关键修复）
            img_tok = torch.tensor([[self.IMAGE_TOKEN_INDEX]], dtype=pre_ids.dtype)
            input_ids = torch.cat([pre_ids, img_tok, post_ids], dim=1).to(model.device)
            attention_mask = torch.ones_like(input_ids, device=model.device)

            # 处理图像特征（与测试代码一致）
            px = model.get_vision_tower().image_processor(images=image, return_tensors="pt")["pixel_values"]
            px = px.to(model.device, dtype=model.dtype)

            # 生成结果（与测试代码一致）
            with torch.no_grad():
                out = model.generate(
                    inputs=input_ids,
                    attention_mask=attention_mask,
                    images=px,
                    max_new_tokens=最大生成长度,
                )

            result = tokenizer.decode(out[0], skip_special_tokens=True)

            # 清理GPU缓存
            if 运行后清理GPU缓存 == "是":
                if 模型选择 in self.models:
                    del self.models[模型选择]
                if 模型选择 in self.tokenizers:
                    del self.tokenizers[模型选择]
                del model
                del tokenizer
                torch.cuda.empty_cache()

            return (result,)

        except Exception as e:
            return (f"处理失败: {str(e)}",)
