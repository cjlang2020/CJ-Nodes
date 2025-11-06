# 兼容不同版本的ComfyUI
import torch
from comfy.utils import common_upscale

try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class MaskedImage2Png(BaseNode):
    """
    输入一张图片和一个遮罩，输出仅保留遮罩区域的图片（非遮罩区域透明）
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """定义输入类型：图片（RGB）和遮罩（单通道）"""
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图片 (格式：[批次, 高度, 宽度, 通道数]，值范围0-1)
                "mask": ("MASK",),   # 输入遮罩 (格式：[批次, 高度, 宽度]，值范围0-1，1表示保留区域)
            }
        }

    RETURN_TYPES = ("IMAGE",)  # 输出格式：带透明通道的图片
    FUNCTION = "apply_mask"    # 主函数
    CATEGORY = "luy"  # 在ComfyUI中的分类

    def apply_mask(self, image: torch.Tensor, mask: torch.Tensor):
        """
        应用遮罩到图片，保留遮罩区域，其他区域透明

        参数:
            image: 输入图片张量，形状为 [batch, height, width, 3] (RGB)
            mask: 遮罩张量，形状为 [batch, height, width] (单通道，0-1值)

        返回:
            带透明通道的图片张量，形状为 [batch, height, width, 4] (RGBA)
        """
        # 确保图片和遮罩尺寸一致（如果不一致，将遮罩缩放到图片尺寸）
        if image.shape[1:3] != mask.shape[1:3]:
            # 遮罩需要先扩展为4维才能缩放 (批次, 高度, 宽度, 1)
            mask_4d = mask.unsqueeze(-1)
            # 缩放到图片尺寸（使用最近邻插值，保持遮罩边缘清晰）
            scaled_mask = common_upscale(
                mask_4d,
                image.shape[2],  # 目标宽度
                image.shape[1],  # 目标高度
                "nearest-exact",
                None
            )
            # 还原为3维遮罩 [batch, height, width]
            mask = scaled_mask.squeeze(-1)

        # 将遮罩扩展为3通道（与图片的RGB通道对应），用于对每个颜色通道应用遮罩
        mask_3ch = mask.unsqueeze(-1).repeat(1, 1, 1, 3)  # 形状变为 [batch, height, width, 3]

        # 应用遮罩：保留遮罩区域的像素（mask=1的区域），其他区域变为0
        masked_rgb = image * mask_3ch

        # 创建Alpha通道（透明通道）：遮罩区域不透明（1），其他区域完全透明（0）
        alpha_channel = mask.unsqueeze(-1)  # 形状变为 [batch, height, width, 1]

        # 合并RGB和Alpha通道，形成RGBA图片
        masked_rgba = torch.cat([masked_rgb, alpha_channel], dim=-1)

        return (masked_rgba,)