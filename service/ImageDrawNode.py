# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode  # type: ignore
except ImportError:
    class BaseNode:
        pass
import base64
import io
import logging
from PIL import Image
import numpy as np
import torch
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageDrawNode")

class ImageDrawNode(BaseNode):
    """
    将Base64编码字符串转换为ComfyUI可识别的图像格式
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """定义节点的输入类型"""
        return {
            "required": {
                "base64_string": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("输出图片",)
    FUNCTION = "process_image"
    CATEGORY = "luy"

    def process_image(self, base64_string):
        """
        将base64字符串转换为ComfyUI图像
        """
        try:
            if not base64_string.strip():
                raise ValueError("输入的base64字符串为空")

            original_length = len(base64_string)
            if 'base64,' in base64_string:
                base64_string = base64_string.split('base64,')[1]
            else:
                logger.info(f"未发现base64前缀，字符串长度: {len(base64_string)}")

            if len(base64_string) % 4 != 0:
                padding_needed = 4 - (len(base64_string) % 4)
                base64_string += '=' * padding_needed
            try:
                image_data = base64.b64decode(base64_string, validate=True)
            except Exception as e:
                raise ValueError(f"base64解码失败: {str(e)}")

            try:
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                image_np_temp = np.array(image)
            except Exception as e:
                raise ValueError(f"无法从解码数据创建图像: {str(e)}")
            image_np = np.array(image).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)

            return (image_tensor,)

        except Exception as e:
            error_msg = f"转换Base64到图像时出错: {str(e)}"
            logger.error(error_msg)
            error_image = torch.ones((1, 100, 100, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0  # 红色通道保留，绿蓝通道设为0
            return (error_image,)