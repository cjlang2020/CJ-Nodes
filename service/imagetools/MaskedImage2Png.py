# 兼容不同版本的ComfyUI
import torch
from comfy.utils import common_upscale
import numpy as np
import json
import re
from PIL import Image, ImageDraw
from typing import Any

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
    CATEGORY = "luy/图片处理"

    def apply_mask(self, image: torch.Tensor, mask: torch.Tensor, keep_alpha: bool):
        """
        应用遮罩并裁剪到遮罩实际大小
        - 保留透明通道：非遮罩区域透明（RGBA）
        - 不保留透明通道：非遮罩区域为纯黑色（RGB）
        """
        # 统一设备（使用图片所在设备）
        device = image.device
        mask = mask.to(device)

        # 确保图片和遮罩尺寸一致
        if image.shape[1:3] != mask.shape[1:3]:
            mask_4d = mask.unsqueeze(-1)  # 扩展为4维 [batch, h, w, 1]
            scaled_mask = common_upscale(
                mask_4d,
                image.shape[2],  # 目标宽度
                image.shape[1],  # 目标高度
                "nearest-exact",
                None
            ).to(device)  # 确保上采样后的遮罩在同一设备
            mask = scaled_mask.squeeze(-1)  # 还原为3维 [batch, h, w]

        # 应用遮罩到RGB通道（非遮罩区域变为0）
        mask_3ch = mask.unsqueeze(-1).repeat(1, 1, 1, 3).to(device)  # [batch, h, w, 3]
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
                empty = torch.zeros((1, 1, channels), device=device)
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

class DrawImageBbox(BaseNode):
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "bbox": ("STRING", {"default": "[0,0,100,100]", "description": "边界框坐标，格式为[x1,y1,x2,y2]"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE",)
    RETURN_NAMES = ("BBOX线框图", "裁切图",)
    FUNCTION = "draw_bbox"
    CATEGORY = "luy/图片处理"

    def draw_bbox(self, image: Any, bbox: str) -> tuple[torch.Tensor, torch.Tensor]:
        # 解析边界框坐标（增强容错性）
        try:
            bbox = bbox.replace("'", '"').replace(" ", "")
            bbox = bbox[1:-1].lstrip().rstrip() if bbox.startswith('[') and bbox.endswith(']') else bbox.lstrip().rstrip()
            bbox_coords = json.loads(bbox)
            if len(bbox_coords) != 4:
                raise ValueError("边界框必须包含4个值：[x1, y1, x2, y2]")
            x1, y1, x2, y2 = map(int, bbox_coords)
        except (json.JSONDecodeError, ValueError) as e:
            nums = re.findall(r'\d+', bbox)
            if len(nums) >= 4:
                x1, y1, x2, y2 = map(int, nums[:4])
            else:
                raise ValueError(f"边界框格式错误：{str(e)}。请使用[x1,y1,x2,y2]格式")

        # 处理图像格式
        try:
            if isinstance(image, torch.Tensor):
                img_np = image.cpu().numpy()
            else:
                img_np = np.array(image)

            if img_np.ndim == 4:
                img_np = img_np[0]
            elif img_np.ndim != 3:
                raise ValueError(f"不支持的图像维度：{img_np.ndim}，期望3或4维")

            if img_np.dtype == np.float32 or img_np.max() <= 1.0:
                img_np = (img_np * 255).astype(np.uint8)
            elif img_np.dtype != np.uint8:
                img_np = img_np.astype(np.uint8)

            # 获取图片尺寸并计算缩放比例
            img_height, img_width = img_np.shape[0], img_np.shape[1]
            scale_w = img_width / 1000.0
            scale_h = img_height / 1000.0

            # 缩放并修正边界框坐标
            scaled_x1 = int(round(x1 * scale_w))
            scaled_y1 = int(round(y1 * scale_h))
            scaled_x2 = int(round(x2 * scale_w))
            scaled_y2 = int(round(y2 * scale_h))

            # 确保坐标有效（防止越界和顺序错误）
            scaled_x1 = max(0, min(scaled_x1, img_width))
            scaled_y1 = max(0, min(scaled_y1, img_height))
            scaled_x2 = max(0, min(scaled_x2, img_width))
            scaled_y2 = max(0, min(scaled_y2, img_height))
            scaled_x1, scaled_x2 = min(scaled_x1, scaled_x2), max(scaled_x1, scaled_x2)
            scaled_y1, scaled_y2 = min(scaled_y1, scaled_y2), max(scaled_y1, scaled_y2)

            # 转换为PIL图像（保留原始图像用于裁切）
            pil_img_original = Image.fromarray(img_np)

            # 绘制线框图（单独处理，不影响原始图像）
            pil_img_with_bbox = pil_img_original.copy()
            draw = ImageDraw.Draw(pil_img_with_bbox)
            line_width = max(1, min(5, int((img_height + img_width) // 200)))
            draw.rectangle([(scaled_x1, scaled_y1), (scaled_x2, scaled_y2)],
                          outline="red", width=line_width)

            # 直接用原始图像裁切（无红线）
            cropped_img = pil_img_original.crop((scaled_x1, scaled_y1, scaled_x2, scaled_y2))

        except Exception as e:
            raise TypeError(f"图像处理失败：{str(e)}")

        # 转换线框图为标准格式（保持与输入图像相同设备）
        bbox_img_np = np.array(pil_img_with_bbox).astype(np.float32) / 255.0
        bbox_tensor = torch.from_numpy(bbox_img_np).unsqueeze(0).to(image.device if isinstance(image, torch.Tensor) else torch.device("cpu"))

        # 转换裁切图为标准格式（保持与输入图像相同设备）
        cropped_img_np = np.array(cropped_img).astype(np.float32) / 255.0
        cropped_tensor = torch.from_numpy(cropped_img_np).unsqueeze(0).to(image.device if isinstance(image, torch.Tensor) else torch.device("cpu"))

        return (bbox_tensor, cropped_tensor)