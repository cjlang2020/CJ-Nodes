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
    输入一张图片和一个遮罩，输出仅保留遮罩区域的图片
    （可选择保留透明通道或使用黑色背景，尺寸为遮罩实际大小）
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        """定义输入类型：图片、遮罩、是否保留透明通道"""
        return {
            "required": {
                "image": ("IMAGE",),  # 输入图片 [批次, 高度, 宽度, 3]
                "mask": ("MASK",),   # 输入遮罩 [批次, 高度, 宽度]
                "keep_alpha": ("BOOLEAN", {"default": True}),  # 是否保留透明通道
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "apply_mask"
    CATEGORY = "luy"

    def apply_mask(self, image: torch.Tensor, mask: torch.Tensor, keep_alpha: bool):
        """
        应用遮罩并裁剪到遮罩实际大小
        - 保留透明通道：非遮罩区域透明（RGBA）
        - 不保留透明通道：非遮罩区域为纯黑色（RGB）
        """
        # 确保图片和遮罩尺寸一致
        if image.shape[1:3] != mask.shape[1:3]:
            mask_4d = mask.unsqueeze(-1)  # 扩展为4维 [batch, h, w, 1]
            scaled_mask = common_upscale(
                mask_4d,
                image.shape[2],  # 目标宽度
                image.shape[1],  # 目标高度
                "nearest-exact",
                None
            )
            mask = scaled_mask.squeeze(-1)  # 还原为3维 [batch, h, w]

        # 应用遮罩到RGB通道（非遮罩区域变为0）
        mask_3ch = mask.unsqueeze(-1).repeat(1, 1, 1, 3)  # [batch, h, w, 3]
        masked_rgb = image * mask_3ch  # 遮罩区域保留原图颜色，其他区域为0（黑色）

        # 处理每个批次，裁剪到遮罩实际大小
        batch_size = mask.shape[0]
        result_images = []

        for b in range(batch_size):
            current_mask = mask[b]
            current_rgb = masked_rgb[b]  # [h, w, 3]

            # 找到遮罩有效区域（值>0.5视为有效）
            non_zero = torch.nonzero(current_mask > 0.5)
            if non_zero.numel() == 0:
                # 无有效遮罩区域，返回1x1的空图像
                channels = 4 if keep_alpha else 3
                empty = torch.zeros((1, 1, channels), device=image.device)
                result_images.append(empty.unsqueeze(0))  # 保持批次维度
                continue

            # 计算遮罩有效区域的边界框
            min_y, min_x = non_zero.min(dim=0).values
            max_y, max_x = non_zero.max(dim=0).values
            # 转换为整数坐标（确保切片正确）
            min_y, min_x = int(min_y), int(min_x)
            max_y, max_x = int(max_y), int(max_x)

            # 裁剪RGB通道到遮罩实际区域
            cropped_rgb = current_rgb[min_y:max_y+1, min_x:max_x+1, :]  # [h_crop, w_crop, 3]

            if keep_alpha:
                # 裁剪Alpha通道并合并（非遮罩区域透明）
                current_alpha = mask[b].unsqueeze(-1)  # [h, w, 1]
                cropped_alpha = current_alpha[min_y:max_y+1, min_x:max_x+1, :]  # [h_crop, w_crop, 1]
                result = torch.cat([cropped_rgb, cropped_alpha], dim=-1)  # [h_crop, w_crop, 4]
            else:
                # 不保留Alpha通道（非遮罩区域已为黑色）
                result = cropped_rgb  # [h_crop, w_crop, 3]

            # 添加批次维度
            result_images.append(result.unsqueeze(0))

        # 合并所有批次结果
        final_result = torch.cat(result_images, dim=0)
        return (final_result,)