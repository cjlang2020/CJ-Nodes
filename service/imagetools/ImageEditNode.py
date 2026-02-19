import torch
import numpy as np
from PIL import Image
import json
import base64
from io import BytesIO
import logging

# 配置日志
logger = logging.getLogger(__name__)

class ImageEditNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 768, "min": 1, "max": 4096}),
                "canvas_height": ("INT", {"default": 1360, "min": 1, "max": 4096}),
                "edit_data": ("STRING", {"default": "empty"})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("edited_image",)
    FUNCTION = "process_edit"
    CATEGORY = "luy/图片处理"

    def process_edit(self, canvas_width, canvas_height, edit_data="empty"):
        """
        处理前端编辑后的最终Base64图片
        """
        try:
            # 初始化默认纯白画布
            final_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            # 解析编辑数据
            if edit_data != "empty" and edit_data.strip():
                try:
                    data = json.loads(edit_data)
                    # 解析前端传递的最终编辑后Base64图片（核心）
                    final_base64 = data.get("final_image_base64", "")
                    crop_w = data.get("crop_width", canvas_width)
                    crop_h = data.get("crop_height", canvas_height)

                    if final_base64:
                        # 解码Base64并加载图片
                        img_data = base64.b64decode(final_base64.split(",")[1])
                        final_img = Image.open(BytesIO(img_data)).convert("RGB")
                        # 强制更新为实际编辑后的尺寸
                        canvas_width, canvas_height = crop_w, crop_h

                except Exception as e:
                    logger.error(f"编辑数据解析失败: {str(e)}")
                    final_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            # 统一张量转换逻辑（兼容所有图片格式，和ComfyUI原生格式一致）
            image_np = np.array(final_img)
            if image_np.dtype != np.uint8:
                image_np = image_np.astype(np.uint8)
            # 归一化到[0,1]
            image_np = image_np.astype(np.float32) / 255.0
            # 兼容灰度图/RGBA
            if len(image_np.shape) == 2:
                image_np = np.stack([image_np, image_np, image_np], axis=-1)
            elif image_np.shape[-1] == 4:
                image_np = image_np[:, :, :3]
            # 增加批次维度（ComfyUI标准格式：[B, H, W, C]）
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)

            logger.info(f"图片编辑完成，输出张量维度: {image_tensor.shape}")
            return (image_tensor,)

        except Exception as e:
            # 异常返回红色错误图
            logger.error(f"图片处理总异常: {str(e)}")
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0  # 纯红背景
            return (error_image,)

class DrawPhotoNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 768, "min": 1, "max": 4096}),
                "canvas_height": ("INT", {"default": 1360, "min": 1, "max": 4096}),
                "edit_data": ("STRING", {"default": "empty"})
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("edited_image", "prompt")
    FUNCTION = "process_draw"
    CATEGORY = "luy/图片处理"

    def process_draw(self, canvas_width, canvas_height, edit_data="empty"):
        """
        处理前端编辑后的最终Base64图片，并输出提示词
        """
        try:
            final_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            if edit_data != "empty" and edit_data.strip():
                try:
                    data = json.loads(edit_data)
                    final_base64 = data.get("final_image_base64", "")
                    crop_w = data.get("crop_width", canvas_width)
                    crop_h = data.get("crop_height", canvas_height)

                    if final_base64:
                        img_data = base64.b64decode(final_base64.split(",")[1])
                        final_img = Image.open(BytesIO(img_data)).convert("RGB")
                        canvas_width, canvas_height = crop_w, crop_h

                except Exception as e:
                    logger.error(f"编辑数据解析失败: {str(e)}")
                    final_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            image_np = np.array(final_img)
            if image_np.dtype != np.uint8:
                image_np = image_np.astype(np.uint8)
            image_np = image_np.astype(np.float32) / 255.0
            if len(image_np.shape) == 2:
                image_np = np.stack([image_np, image_np, image_np], axis=-1)
            elif image_np.shape[-1] == 4:
                image_np = image_np[:, :, :3]
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)

            logger.info(f"图片绘制完成，输出张量维度: {image_tensor.shape}")
            prompt = "颜色 (#F5D6B4) 区域表示人物，颜色 (#1E5631) 区域表示成年树木，颜色 (#4CAF50) 区域表示树叶树冠，颜色 (#8FBC8F) 区域表示普通草地，颜色 (#7CCD7C) 区域表示新生草幼苗，颜色 (#4A7C59) 区域表示灌木灌木丛，颜色 (#FFB6C1) 区域表示蔷薇樱花，颜色 (#FF69B4) 区域表示玫瑰牡丹，颜色 (#FFFF00) 区域表示向日葵迎春花，颜色 (#FF6347) 区域表示苹果柿子果实，颜色 (#800000) 区域表示樱桃石榴果实，颜色 (#87CEEB) 区域表示晴朗天空，颜色 (#6495ED) 区域表示傍晚阴天天空，颜色 (#4682B4) 区域表示流动河流，颜色 (#B0E0E6) 区域表示平静湖水池塘，颜色 (#00BFFF) 区域表示海洋大海，颜色 (#696969) 区域表示山脉主体，颜色 (#A9A9A9) 区域表示山脉阴影岩石，颜色 (#A0522D) 区域表示泥土山石，颜色 (#E6E6FA) 区域表示薄云雾晨雾，颜色 (#D3D3D3) 区域表示厚云雾雾霾，颜色 (#FFFFFF) 区域表示晴天云朵，颜色 (#F0F0F0) 区域表示阴天云朵，颜色 (#FFD700) 区域表示正午太阳，颜色 (#FF8C00) 区域表示日出日落太阳，颜色 (#C17C56) 区域表示深肤色人物，颜色 (#8B4513) 区域表示柏油主路道路，颜色 (#D2691E) 区域表示泥土乡间小路，颜色 (#FFA500) 区域表示木质民居建筑，颜色 (#708090) 区域表示高楼混凝土建筑，颜色 (#FFFFFF) 区域表示建筑墙面窗框，颜色 (#000000) 区域表示建筑屋顶栏杆"
            return (image_tensor, prompt)

        except Exception as e:
            logger.error(f"图片处理总异常: {str(e)}")
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0
            return (error_image, "颜色 (#F5D6B4) 区域表示人物，颜色 (#1E5631) 区域表示成年树木，颜色 (#4CAF50) 区域表示树叶树冠，颜色 (#8FBC8F) 区域表示普通草地，颜色 (#7CCD7C) 区域表示新生草幼苗，颜色 (#4A7C59) 区域表示灌木灌木丛，颜色 (#FFB6C1) 区域表示蔷薇樱花，颜色 (#FF69B4) 区域表示玫瑰牡丹，颜色 (#FFFF00) 区域表示向日葵迎春花，颜色 (#FF6347) 区域表示苹果柿子果实，颜色 (#800000) 区域表示樱桃石榴果实，颜色 (#87CEEB) 区域表示晴朗天空，颜色 (#6495ED) 区域表示傍晚阴天天空，颜色 (#4682B4) 区域表示流动河流，颜色 (#B0E0E6) 区域表示平静湖水池塘，颜色 (#00BFFF) 区域表示海洋大海，颜色 (#696969) 区域表示山脉主体，颜色 (#A9A9A9) 区域表示山脉阴影岩石，颜色 (#A0522D) 区域表示泥土山石，颜色 (#E6E6FA) 区域表示薄云雾晨雾，颜色 (#D3D3D3) 区域表示厚云雾雾霾，颜色 (#FFFFFF) 区域表示晴天云朵，颜色 (#F0F0F0) 区域表示阴天云朵，颜色 (#FFD700) 区域表示正午太阳，颜色 (#FF8C00) 区域表示日出日落太阳，颜色 (#C17C56) 区域表示深肤色人物，颜色 (#8B4513) 区域表示柏油主路道路，颜色 (#D2691E) 区域表示泥土乡间小路，颜色 (#FFA500) 区域表示木质民居建筑，颜色 (#708090) 区域表示高楼混凝土建筑，颜色 (#FFFFFF) 区域表示建筑墙面窗框，颜色 (#000000) 区域表示建筑屋顶栏杆")

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageEditNode": ImageEditNode,
    "DrawPhotoNode": DrawPhotoNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageEditNode": "Image Edit Node (修复版-画笔+液化+橡皮擦)",
    "DrawPhotoNode": "Draw Photo Node (绘制图片)"
}