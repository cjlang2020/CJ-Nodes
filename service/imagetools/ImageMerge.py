import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

# 合并类型配置：(列数, 行数, 最大图片数)
MERGE_LAYOUTS = {
    "一行": (0, 1, 9),      # 动态列数，1行
    "一列": (1, 0, 9),      # 1列，动态行数
    "3x3": (3, 3, 9),
    "2x4": (2, 4, 8),
    "4x2": (4, 2, 8),
    "2x2": (2, 2, 4),
    "1+2": (2, 2, 3),       # 上1下2，特殊布局
    "2+1": (2, 2, 3),       # 上2下1，特殊布局
}


class ImageMerge:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "merge_type": (list(MERGE_LAYOUTS.keys()),),
                "border_width": ("INT", {"default": 16, "min": 0, "max": 100, "step": 1}),
                "bg_color": (["亮色(白)", "暗色(黑)"],),
                "text_size": ("INT", {"default": 36, "min": 8, "max": 100, "step": 1}),
                "text_color": (["暗色(黑)", "亮色(白)"],),
                "fit_longest_edge": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
                "image_6": ("IMAGE",),
                "image_7": ("IMAGE",),
                "image_8": ("IMAGE",),
                "image_9": ("IMAGE",),
                "text_1": ("STRING", {"default": "", "multiline": True}),
                "text_2": ("STRING", {"default": "", "multiline": True}),
                "text_3": ("STRING", {"default": "", "multiline": True}),
                "text_4": ("STRING", {"default": "", "multiline": True}),
                "text_5": ("STRING", {"default": "", "multiline": True}),
                "text_6": ("STRING", {"default": "", "multiline": True}),
                "text_7": ("STRING", {"default": "", "multiline": True}),
                "text_8": ("STRING", {"default": "", "multiline": True}),
                "text_9": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "merge_images"
    CATEGORY = "luy/图片处理"
    DESCRIPTION = "将多张图片按指定布局合并为一张图片，支持边框和文字标注"

    def merge_images(self, merge_type, border_width, bg_color, text_size, text_color, fit_longest_edge,
                     image_1=None, image_2=None, image_3=None,
                     image_4=None, image_5=None, image_6=None,
                     image_7=None, image_8=None, image_9=None,
                     text_1="", text_2="", text_3="",
                     text_4="", text_5="", text_6="",
                     text_7="", text_8="", text_9=""):
        try:
            # 收集所有图片和文字
            images = [image_1, image_2, image_3, image_4, image_5,
                      image_6, image_7, image_8, image_9]
            texts = [text_1, text_2, text_3, text_4, text_5,
                     text_6, text_7, text_8, text_9]

            # 过滤掉空图片，保留索引用于后续文字对应
            valid_images = []
            valid_texts = []
            for i, img in enumerate(images):
                if img is not None:
                    valid_images.append(img)
                    valid_texts.append(texts[i] if i < len(texts) else "")

            if not valid_images:
                logger.warning("没有输入任何图片，返回空白图片")
                result = torch.ones((1, 200, 200, 3), dtype=torch.float32)
                return (result,)

            # 颜色设置
            bg_rgb = (255, 255, 255) if bg_color == "亮色(白)" else (0, 0, 0)
            text_rgb = (0, 0, 0) if text_color == "暗色(黑)" else (255, 255, 255)

            # 获取布局配置
            cols, rows, max_count = MERGE_LAYOUTS[merge_type]

            # 限制图片数量
            valid_images = valid_images[:max_count]
            valid_texts = valid_texts[:max_count]

            # 转换为PIL图片并获取尺寸
            pil_images = []
            for img in valid_images:
                img_np = img.cpu().numpy()
                # 处理batch维度，取第一张图片
                if len(img_np.shape) == 4:
                    img_np = img_np[0]
                if img_np.dtype != np.uint8:
                    img_np = (img_np * 255).astype(np.uint8)
                if img_np.shape[-1] == 4:
                    img_np = img_np[:, :, :3]
                pil_img = Image.fromarray(img_np, mode="RGB")
                pil_images.append(pil_img)

            # 最长边适配：根据1920x1080目标尺寸等比缩放
            if fit_longest_edge:
                target_w, target_h = 1920, 1080
                scaled_images = []
                for pil_img in pil_images:
                    w, h = pil_img.size
                    if w >= h:
                        # 宽图：按宽度缩放到1920
                        ratio = target_w / w
                        new_w = target_w
                        new_h = int(h * ratio)
                    else:
                        # 高图：按高度缩放到1080
                        ratio = target_h / h
                        new_w = int(w * ratio)
                        new_h = target_h
                    scaled_images.append(pil_img.resize((new_w, new_h), Image.LANCZOS))
                pil_images = scaled_images

            # 计算单元格尺寸（所有图片统一大小）
            max_img_width = max(img.width for img in pil_images)
            max_img_height = max(img.height for img in pil_images)

            # 检查是否有文字
            has_text = any(t.strip() for t in valid_texts)
            text_height = (text_size + 10) if has_text else 0

            cell_width = max_img_width + 2 * border_width
            cell_height = max_img_height + 2 * border_width + text_height

            # 计算实际行列数（根据图片数量动态调整）
            num_images = len(pil_images)
            if merge_type == "一行":
                cols = num_images
                rows = 1
            elif merge_type == "一列":
                cols = 1
                rows = num_images
            elif merge_type in ("1+2", "2+1"):
                cols = 2
                rows = 2
            else:
                # 网格布局：根据图片数量计算实际需要的列数和行数
                import math
                cols = min(cols, num_images)
                rows = math.ceil(num_images / cols)

            # 创建画布
            canvas_width = cols * cell_width
            canvas_height = rows * cell_height
            canvas = Image.new("RGB", (canvas_width, canvas_height), bg_rgb)
            draw = ImageDraw.Draw(canvas)

            # 尝试加载字体（加粗）
            font = None
            try:
                # Windows加粗字体路径
                font_path = "C:/Windows/Fonts/msyhbd.ttc"
                font = ImageFont.truetype(font_path, text_size)
            except:
                try:
                    font_path = "C:/Windows/Fonts/simhei.ttf"
                    font = ImageFont.truetype(font_path, text_size)
                except:
                    font = ImageFont.load_default()

            # 放置图片
            for idx, (pil_img, text) in enumerate(zip(pil_images, valid_texts)):
                # 计算网格位置
                if merge_type == "1+2":
                    # 上面1个居中，下面2个
                    if idx == 0:
                        grid_x, grid_y = 0, 0
                    elif idx == 1:
                        grid_x, grid_y = 0, 1
                    elif idx == 2:
                        grid_x, grid_y = 1, 1
                    else:
                        break
                elif merge_type == "2+1":
                    # 上面2个，下面1个居中
                    if idx == 0:
                        grid_x, grid_y = 0, 0
                    elif idx == 1:
                        grid_x, grid_y = 1, 0
                    elif idx == 2:
                        grid_x, grid_y = 0, 1
                    else:
                        break
                else:
                    grid_x = idx % cols
                    grid_y = idx // cols
                    if grid_y >= rows:
                        break

                # 计算绘制位置
                paste_x = grid_x * cell_width + border_width
                paste_y = grid_y * cell_height + border_width

                # 居中放置图片
                offset_x = (cell_width - 2 * border_width - pil_img.width) // 2
                offset_y = (cell_height - 2 * border_width - text_height - pil_img.height) // 2
                paste_x += offset_x
                paste_y += offset_y

                # 粘贴图片
                canvas.paste(pil_img, (paste_x, paste_y))

                # 绘制文字
                if text.strip() and font:
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_x = grid_x * cell_width + (cell_width - text_w) // 2
                    # 文字位置：图片底部下方
                    text_y = paste_y + pil_img.height + 5
                    draw.text((text_x, text_y), text, fill=text_rgb, font=font)

            # 转换为tensor
            result_np = np.array(canvas).astype(np.float32) / 255.0
            result = torch.from_numpy(result_np).unsqueeze(0)

            return (result,)

        except Exception as e:
            logger.error(f"图片合并异常: {str(e)}")
            import traceback
            traceback.print_exc()
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            return (error_image,)


NODE_CLASS_MAPPINGS = {
    "ImageMerge": ImageMerge,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMerge": "Luy-图片合并",
}
