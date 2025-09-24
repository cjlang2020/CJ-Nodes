# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode  # type: ignore
except ImportError:
    class BaseNode:
        pass

# 导入必要的库
import base64
import io
import logging
from PIL import Image
import numpy as np
import torch

# 配置日志
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
            # 检查输入是否为空
            if not base64_string.strip():
                raise ValueError("输入的base64字符串为空")

            # 移除可能存在的前缀（如"data:image/png;base64,"）
            original_length = len(base64_string)
            if 'base64,' in base64_string:
                base64_string = base64_string.split('base64,')[1]
                logger.info(f"移除了base64前缀，原始长度: {original_length}, 处理后长度: {len(base64_string)}")
            else:
                logger.info(f"未发现base64前缀，字符串长度: {len(base64_string)}")

            # 检查base64字符串的有效性（简单检查）
            if len(base64_string) % 4 != 0:
                # 尝试补充padding
                padding_needed = 4 - (len(base64_string) % 4)
                base64_string += '=' * padding_needed
                logger.warning(f"base64字符串长度不是4的倍数，已自动补充{padding_needed}个等号")

            # 解码base64字符串为字节数据
            try:
                image_data = base64.b64decode(base64_string, validate=True)
                logger.info(f"base64解码成功，得到{len(image_data)}字节的数据")
            except Exception as e:
                raise ValueError(f"base64解码失败: {str(e)}")

            # 将字节数据转换为PIL图像
            try:
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
                logger.info(f"成功创建PIL图像，尺寸: {image.size}, 模式: {image.mode}")
                # 打印图像像素的统计信息，看是否有有效数据
                image_np_temp = np.array(image)
                logger.info(f"PIL图像转numpy数组后，最大值: {image_np_temp.max()}, 最小值: {image_np_temp.min()}, 均值: {image_np_temp.mean()}")
            except Exception as e:
                raise ValueError(f"无法从解码数据创建图像: {str(e)}")

            # 将PIL图像转换为numpy数组
            image_np = np.array(image).astype(np.float32) / 255.0
            logger.info(f"转换为numpy数组，形状: {image_np.shape}")
            # 打印归一化后数组的统计信息
            logger.info(f"归一化后数组，最大值: {image_np.max()}, 最小值: {image_np.min()}, 均值: {image_np.mean()}")

            # 将numpy数组转换为PyTorch张量，并调整维度以符合ComfyUI要求
            # ComfyUI期望的格式是 (1, height, width, 3)
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)
            logger.info(f"转换为张量，形状: {image_tensor.shape}")
            # 打印张量的统计信息
            logger.info(f"张量，最大值: {image_tensor.max()}, 最小值: {image_tensor.min()}, 均值: {image_tensor.mean()}")

            return (image_tensor,)

        except Exception as e:
            error_msg = f"转换Base64到图像时出错: {str(e)}"
            logger.error(error_msg)
            # 返回一个可见的错误图像（100x100红色图像）而不是1x1黑色图像，便于识别错误
            error_image = torch.ones((1, 100, 100, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0  # 红色通道保留，绿蓝通道设为0
            return (error_image,)