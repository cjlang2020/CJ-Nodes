import json
from PIL import Image
import numpy as np
from comfy.utils import common_upscale
import torchvision.transforms as T
import requests
import base64
from io import BytesIO

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class VisionModelNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": False,
                    "default": "http://localhost:11434/api/generate"  # Ollama视觉模型API地址
                }),
                "model_type": (["minicpm-v:8b","gemma3:4b"],),  # 视觉模型列表
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "描述这张图片的内容，分析图片中的元素"
                }),
                "system_instruction": ("STRING", {
                    "multiline": True,
                    "default": "你是一个图像分析助手，仔细分析图片内容并详细回答问题。"
                }),
            },
            "optional": {
                "image": ("IMAGE",),  # 图片输入，使用ComfyUI的IMAGE类型
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "call_vision_model"
    CATEGORY = "luy"

    def encode_image(self, image_tensor):
        """将ComfyUI的图像张量转换为base64编码"""
        try:
            # 转换张量格式 (ComfyUI的图像通常是[B, H, W, C]或[H, W, C]格式)
            if len(image_tensor.shape) == 4:
                # 取第一个图像
                image_np = image_tensor[0].cpu().numpy()
            else:
                image_np = image_tensor.cpu().numpy()

            # 转换为PIL图像 (处理归一化的情况)
            if image_np.max() <= 1.0:
                image_np = (image_np * 255).astype("uint8")

            # 处理通道顺序 (如果需要)
            if image_np.shape[-1] == 3:  # RGB
                pil_image = Image.fromarray(image_np, mode="RGB")
            elif image_np.shape[-1] == 4:  # RGBA
                pil_image = Image.fromarray(image_np, mode="RGBA").convert("RGB")
            else:  # 灰度图
                pil_image = Image.fromarray(image_np.squeeze(), mode="L").convert("RGB")

            # 转换为base64
            buffer = BytesIO()
            pil_image.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

        except Exception as e:
            raise Exception(f"图片编码失败: {str(e)}")

    def call_vision_model(self, url, model_type, prompt, system_instruction, image=None):
        """调用视觉模型API"""
        try:
            # 构建基础请求数据
            payload = {
                "model": model_type,
                "prompt": prompt,
                "system": system_instruction,
                "options": {
                    "temperature": 0.3,
                    "num_ctx": 4096  # 视觉模型通常需要更大的上下文
                },
                "stream": False,
                "format": "json"
            }

            # 如果有图片，添加图片数据
            if image is not None:
                try:
                    image_b64 = self.encode_image(image)
                    payload["images"] = [image_b64]  # Ollama视觉模型使用images字段
                except Exception as e:
                    return (f"图片处理错误: {str(e)}",)

            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=120  # 视觉模型处理时间更长，延长超时
            )

            response.raise_for_status()

            # 解析响应
            result = response.json()
            if "response" in result:
                print("==>"+result["response"])
                return (result["response"],)
            else:
                return (f"API返回格式异常: {str(result)}",)

        except requests.exceptions.RequestException as e:
            error_msg = f"请求错误: {str(e)}"
            if hasattr(response, 'text'):
                error_msg += f"\n响应内容: {response.text}"
            return (error_msg,)
        except json.JSONDecodeError:
            return (f"解析响应失败: {response.text}",)
        except Exception as e:
            return (f"发生错误: {str(e)}",)
