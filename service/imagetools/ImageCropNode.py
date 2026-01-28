import torch
import numpy as np
from PIL import Image
import json
import base64
from io import BytesIO
import logging

# 配置日志（和参考代码保持一致）
logger = logging.getLogger(__name__)

class ImageCropNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 画布宽高（会被自动更新为裁剪区域尺寸）
                "canvas_width": ("INT", {"default": 768, "min": 1, "max": 2048}),
                "canvas_height": ("INT", {"default": 1360, "min": 1, "max": 2048}),
                # 隐藏参数：存储Base64图片+裁剪坐标
                "crop_data": ("STRING", {"default": "empty"})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("cropped_image",)
    FUNCTION = "process_crop"
    CATEGORY = "luy"

    def process_crop(self, canvas_width, canvas_height, crop_data="empty"):
        """
        参照参考代码的张量转换逻辑，实现自动图片裁剪功能
        """
        try:
            # ========== 步骤1：初始化默认画布 ==========
            img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            # ========== 步骤2：解析裁剪数据 ==========
            if crop_data != "empty" and crop_data.strip():
                try:
                    data = json.loads(crop_data)
                    # 解析Base64图片
                    img_base64 = data.get("image_base64", "")
                    if img_base64:
                        # 解码Base64图片
                        img_data = base64.b64decode(img_base64.split(",")[1])
                        img = Image.open(BytesIO(img_data)).convert("RGB")

                    # 解析裁剪坐标（使用画布尺寸作为默认值）
                    crop_coords = data.get("crop_coords", [0, 0, canvas_width, canvas_height])
                    x1, y1, x2, y2 = [int(round(float(c))) for c in crop_coords]

                    # 标准化裁剪坐标
                    img_width, img_height = img.size
                    x1 = max(0, min(img_width - 1, x1))
                    y1 = max(0, min(img_height - 1, y1))
                    x2 = max(x1 + 1, min(img_width, x2))
                    y2 = max(y1 + 1, min(img_height, y2))

                    # 执行裁剪
                    img = img.crop((x1, y1, x2, y2))

                except Exception as e:
                    logger.error(f"裁剪解析失败: {str(e)}")
                    # 失败后重置为纯白画布
                    img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            # ========== 步骤3：完全参照参考代码的张量转换逻辑 ==========
            image_np = np.array(img)
            if image_np.dtype != np.uint8:
                image_np = image_np.astype(np.uint8)
            image_np = image_np.astype(np.float32) / 255.0

            # 兼容灰度图/RGBA
            if len(image_np.shape) == 2:
                image_np = np.stack([image_np, image_np, image_np], axis=-1)
            elif image_np.shape[-1] == 4:
                image_np = image_np[:, :, :3]

            # 增加批次维度
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)
            logger.info(f"输出张量维度: {image_tensor.shape}")

            return (image_tensor,)

        except Exception as e:
            # 异常时返回红色错误图
            error_msg = f"图片裁剪出错: {str(e)}"
            logger.error(error_msg)
            error_image = torch.ones((1, 100, 100, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0
            return (error_image,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageCropNode": ImageCropNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageCropNode": "Luy-图片裁剪"
}