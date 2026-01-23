import torch
import numpy as np
from PIL import Image, ImageDraw
import json
import base64
from io import BytesIO
import logging

# 配置日志（和参考代码保持一致）
logger = logging.getLogger(__name__)

class MouseDrawNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 512, "min": 128, "max": 2048}),
                "canvas_height": ("INT", {"default": 512, "min": 128, "max": 2048}),
                "draw_data": ("STRING", {"default": "empty"})  # 从hidden移到required
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("draw_image",)
    FUNCTION = "generate_image"
    CATEGORY = "Luy"

    def generate_image(self, canvas_width, canvas_height, draw_data="empty"):
        """
        完全参照ImageDrawNode的张量转换逻辑，生成手绘图像并输出标准ComfyUI张量
        """
        try:
            # ========== 步骤1：强制标准化输入参数 ==========
            canvas_width = max(128, min(2048, int(canvas_width)))
            canvas_height = max(128, min(2048, int(canvas_height)))

            # ========== 步骤2：初始化画布（RGB格式） ==========
            img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
            draw = ImageDraw.Draw(img)

            # ========== 步骤3：解析并绘制路径 ==========
            if draw_data != "empty" and draw_data.strip():
                try:
                    data = json.loads(draw_data)
                    # 解析背景色（带容错）
                    bg_hex = data.get("bg_color", "#ffffff").lstrip('#')
                    if len(bg_hex) not in (3, 6):
                        bg_hex = "ffffff"
                    if len(bg_hex) == 3:
                        bg_hex = bg_hex * 2
                    try:
                        bg_r = int(bg_hex[0:2], 16)
                        bg_g = int(bg_hex[2:4], 16)
                        bg_b = int(bg_hex[4:6], 16)
                    except ValueError:
                        bg_r, bg_g, bg_b = 255, 255, 255

                    # 重新创建画布
                    img = Image.new("RGB", (canvas_width, canvas_height), (bg_r, bg_g, bg_b))
                    draw = ImageDraw.Draw(img)

                    # 绘制路径
                    paths = data.get("paths", [])
                    for path in paths:
                        points = path.get("points", [])
                        if len(points) < 2:
                            continue

                        # 解析画笔属性
                        color_hex = path.get("color", "#000000").lstrip('#')
                        if len(color_hex) not in (3, 6):
                            color_hex = "000000"
                        if len(color_hex) == 3:
                            color_hex = color_hex * 2
                        try:
                            r = int(color_hex[0:2], 16)
                            g = int(color_hex[2:4], 16)
                            b = int(color_hex[4:6], 16)
                        except ValueError:
                            r, g, b = 0, 0, 0
                        color = (r, g, b)

                        try:
                            size = max(1, min(100, int(path.get("size", 5))))
                        except (ValueError, TypeError):
                            size = 5

                        is_eraser = path.get("is_eraser", False)
                        if is_eraser:
                            color = (bg_r, bg_g, bg_b)

                        # 处理坐标点
                        int_points = []
                        for p in points:
                            try:
                                x = float(p[0]) if isinstance(p, (list, tuple)) else 0
                                y = float(p[1]) if isinstance(p, (list, tuple)) else 0
                                int_points.append((int(round(x)), int(round(y))))
                            except (ValueError, TypeError, IndexError):
                                continue

                        # 绘制线条
                        for i in range(1, len(int_points)):
                            x1, y1 = int_points[i-1]
                            x2, y2 = int_points[i]
                            x1 = max(0, min(canvas_width-1, x1))
                            y1 = max(0, min(canvas_height-1, y1))
                            x2 = max(0, min(canvas_width-1, x2))
                            y2 = max(0, min(canvas_height-1, y2))
                            draw.line([(x1, y1), (x2, y2)], fill=color, width=size)
                            draw.ellipse([(x2 - size//2, y2 - size//2),
                                          (x2 + size//2, y2 + size//2)], fill=color)
                except Exception as e:
                    logger.error(f"绘图解析失败: {str(e)}")
                    # 失败后重置为纯白画布
                    img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            # ========== 步骤4：完全参照ImageDrawNode的张量转换逻辑（核心修改） ==========
            # 1. PIL Image → numpy数组（和参考代码一致）
            image_np = np.array(img)

            # 2. 强制保证数据类型为uint8（参考代码的核心逻辑）
            if image_np.dtype != np.uint8:
                image_np = image_np.astype(np.uint8)

            # 3. 转换为浮点数并归一化到[0,1]（和参考代码完全一致）
            image_np = image_np.astype(np.float32) / 255.0

            # 4. 兼容灰度图/RGBA（参考代码的关键容错）
            if len(image_np.shape) == 2:  # 灰度图转RGB
                image_np = np.stack([image_np, image_np, image_np], axis=-1)
            elif image_np.shape[-1] == 4:  # RGBA去掉Alpha通道
                image_np = image_np[:, :, :3]

            # 5. 仅增加批次维度（参考代码的核心：不做permute！）
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)

            # 6. 最终校验
            logger.info(f"输出张量维度: {image_tensor.shape}")  # 应输出 (1, H, W, 3)
            return (image_tensor,)

        except Exception as e:
            # 异常时返回红色错误图（和参考代码的异常处理逻辑一致）
            error_msg = f"生成手绘图像出错: {str(e)}"
            logger.error(error_msg)
            error_image = torch.ones((1, 100, 100, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0  # 红色背景
            return (error_image,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "MouseDrawNode": MouseDrawNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MouseDrawNode": "Mouse Draw Node"
}