# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode  # type: ignore
except ImportError:
    class BaseNode:
        pass
import torch
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageMaskNode")

class ImageMaskNode:
    """
    将图片数组中指定区域涂黑，并输出对应蒙版的节点
    包含全面的尺寸验证，防止出现0尺寸的输入
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # 输入图片数组
                "x": ("INT", {"default": 0, "min": 0, "step": 1}),  # 像素起点X
                "y": ("INT", {"default": 0, "min": 0, "step": 1}),  # 像素起点Y
                "width": ("INT", {"default": 100, "min": 1, "step": 1}),  # 区域宽度
                "height": ("INT", {"default": 100, "min": 1, "step": 1}),  # 区域高度
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("输出图片", "输出蒙版")
    FUNCTION = "process_region"
    CATEGORY = "luy"

    def process_region(self, images, x, y, width, height):
        """
        处理图像区域并生成蒙版，包含完整的尺寸验证逻辑
        确保不会产生高度或宽度为0的输出
        """
        # 1. 基础验证：检查输入图像是否有效
        if images is None:
            logger.error("输入图像为None")
            return (None, None)

        if len(images.shape) != 4:
            logger.error(f"输入图像格式不正确，预期4维张量，实际{len(images.shape)}维")
            return (images, torch.zeros((images.shape[0], 1, 1, 1), dtype=torch.float32, device=images.device))

        # 2. 提取图像尺寸并验证
        batch_size, img_height, img_width, channels = images.shape

        # 检查图像自身尺寸是否有效
        if img_height <= 0 or img_width <= 0:
            logger.error(f"图像自身尺寸无效: 高度={img_height}, 宽度={img_width}")
            # 返回原图像和最小有效蒙版(1x1)
            return (images, torch.zeros((batch_size, 1, 1, 1), dtype=torch.float32, device=images.device))

        # 3. 计算区域坐标并进行严格边界处理
        # 确保起点不超出图像范围
        start_x = max(0, min(x, img_width - 1))  # 确保x在有效范围内
        start_y = max(0, min(y, img_height - 1))  # 确保y在有效范围内

        # 计算终点，确保不超出图像边界
        end_x = min(start_x + width, img_width)
        end_y = min(start_y + height, img_height)

        # 4. 确保区域尺寸有效（至少1x1）
        # 强制区域宽度至少为1
        if end_x <= start_x:
            logger.warning(f"区域宽度无效({end_x - start_x})，自动调整为1")
            end_x = start_x + 1
            # 防止调整后超出边界
            if end_x > img_width:
                end_x = img_width
                start_x = max(0, end_x - 1)

        # 强制区域高度至少为1
        if end_y <= start_y:
            logger.warning(f"区域高度无效({end_y - start_y})，自动调整为1")
            end_y = start_y + 1
            # 防止调整后超出边界
            if end_y > img_height:
                end_y = img_height
                start_y = max(0, end_y - 1)

        # 5. 复制原始图像并处理指定区域
        result = images.clone()
        result[:, start_y:end_y, start_x:end_x, :] = 0.0  # 将区域涂黑

        # 6. 创建蒙版（确保尺寸有效）
        mask = torch.zeros((batch_size, img_height, img_width, 1), dtype=torch.float32, device=images.device)
        mask[:, start_y:end_y, start_x:end_x, :] = 1.0  # 蒙版标记区域

        # 7. 最终验证输出尺寸
        self._validate_output_size(result, "处理后图像")
        self._validate_output_size(mask, "生成的蒙版")

        return (result, mask)

    def _validate_output_size(self, tensor, name):
        """验证输出张量的尺寸是否有效"""
        if len(tensor.shape) >= 2:
            height = tensor.shape[1]
            width = tensor.shape[2]
            if height <= 0 or width <= 0:
                logger.error(f"{name}尺寸无效: 高度={height}, 宽度={width}")
        else:
            logger.error(f"{name}格式不正确，维度不足: {len(tensor.shape)}")
