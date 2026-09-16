import torch
import numpy as np
from PIL import Image
import json
import base64
import os
from io import BytesIO
import logging

import folder_paths

# 配置日志
logger = logging.getLogger(__name__)


def _resolve_canvas_file(rel_path):
    """解析前端上传的画布文件（input/cj_canvas/），并做路径包含校验"""
    if not rel_path or ".." in rel_path:
        return None
    input_dir = folder_paths.get_directory_by_type("input")
    if not input_dir:
        return None
    input_dir = os.path.abspath(input_dir)
    path = os.path.abspath(os.path.join(input_dir, rel_path))
    if os.path.commonpath((input_dir, path)) != input_dir or not os.path.isfile(path):
        return None
    return path


def _payload_image(data, file_key, b64_key):
    """优先读取上传的画布文件，旧工作流内嵌的 base64 仍然兼容"""
    rel_path = data.get(file_key)
    if rel_path:
        path = _resolve_canvas_file(rel_path)
        if path is None:
            logger.warning(f"画布文件不存在，改用空白画布: {rel_path}")
            return None
        return Image.open(path).convert("RGB")
    b64 = data.get(b64_key, "")
    if b64:
        return Image.open(BytesIO(base64.b64decode(b64.split(",")[1]))).convert("RGB")
    return None

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
                    # 优先使用上传到服务器的画布文件（新格式），旧工作流的内嵌 base64 仍兼容
                    crop_w = data.get("crop_width", canvas_width)
                    crop_h = data.get("crop_height", canvas_height)
                    loaded = _payload_image(data, "final_image", "final_image_base64")
                    if loaded is not None:
                        final_img = loaded
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
                    # 优先使用上传到服务器的画布文件（新格式），旧工作流的内嵌 base64 仍兼容
                    crop_w = data.get("crop_width", canvas_width)
                    crop_h = data.get("crop_height", canvas_height)
                    loaded = _payload_image(data, "final_image", "final_image_base64")
                    if loaded is not None:
                        final_img = loaded
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
            prompt = "颜色 (#1E5631) 区域表示树木，颜色 (#4CAF50) 区域表示树冠，颜色 (#8FBC8F) 区域表示草地，颜色 (#FFB6C1) 区域表示花，颜色 (#87CEEB) 区域表示天空，颜色 (#4682B4) 区域表示河流，颜色 (#B0E0E6) 区域表示湖水，颜色 (#00BFFF) 区域表示海洋，颜色 (#696969) 区域表示山脉，颜色 (#A0522D) 区域表示泥土，颜色 (#E6E6FA) 区域表示云雾，颜色 (#FFFFFF) 区域表示云朵，颜色 (#FFD700) 区域表示太阳，颜色 (#F5D6B4) 区域表示人物，颜色 (#8B4513) 区域表示道路，颜色 (#FFA500) 区域表示建筑，颜色 (#708090) 区域表示高楼，颜色 (#000000) 区域表示建筑"
            return (image_tensor, prompt)

        except Exception as e:
            logger.error(f"图片处理总异常: {str(e)}")
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0
            return (error_image, "null")

class ImageDesign:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 768, "min": 1, "max": 4096}),
                "canvas_height": ("INT", {"default": 768, "min": 1, "max": 4096}),
                "edit_data": ("STRING", {"default": "empty"})
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "IMAGE")
    RETURN_NAMES = ("edited_image", "prompt", "original_image")
    FUNCTION = "process_design"
    CATEGORY = "luy/图片处理"

    def _img_to_tensor(self, img):
        arr = np.array(img)
        if arr.dtype != np.uint8:
            arr = arr.astype(np.uint8)
        arr = arr.astype(np.float32) / 255.0
        if len(arr.shape) == 2:
            arr = np.stack([arr, arr, arr], axis=-1)
        elif arr.shape[-1] == 4:
            arr = arr[:, :, :3]
        return torch.from_numpy(arr).unsqueeze(0)

    def process_design(self, canvas_width, canvas_height, edit_data="empty"):
        try:
            final_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
            original_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            if edit_data != "empty" and edit_data.strip():
                try:
                    data = json.loads(edit_data)
                    # 优先使用上传到服务器的画布文件（新格式），旧工作流的内嵌 base64 仍兼容
                    crop_w = data.get("crop_width", canvas_width)
                    crop_h = data.get("crop_height", canvas_height)
                    loaded = _payload_image(data, "final_image", "final_image_base64")
                    if loaded is not None:
                        final_img = loaded
                        canvas_width, canvas_height = crop_w, crop_h
                    original = _payload_image(data, "original_image", "original_image_base64")
                    if original is not None:
                        original_img = original

                except Exception as e:
                    logger.error(f"设计数据解析失败: {str(e)}")
                    final_img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))

            image_tensor = self._img_to_tensor(final_img)
            original_tensor = self._img_to_tensor(original_img)

            logger.info(f"图片设计完成，输出张量维度: {image_tensor.shape}")
            prompt = ""
            if edit_data != "empty" and edit_data.strip():
                try:
                    data = json.loads(edit_data)
                    layers_info = data.get("layers", [])
                    if layers_info:
                        parts = []
                        for l in layers_info:
                            name = l.get("name", "")
                            text = (l.get("text") or "").strip()
                            parts.append(f"颜色【{name}】区域内容重绘为【{text}】")
                        prompt = "；".join(parts)
                except Exception:
                    pass
            if not prompt:
                prompt = "图片设计无描述"
            return (image_tensor, prompt, original_tensor)

        except Exception as e:
            logger.error(f"图片设计总异常: {str(e)}")
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0
            return (error_image, "null", error_image)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageEditNode": ImageEditNode,
    "DrawPhotoNode": DrawPhotoNode,
    "ImageDesign": ImageDesign
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageEditNode": "Image Edit Node (修复版-画笔+液化+橡皮擦)",
    "DrawPhotoNode": "Draw Photo Node (绘制图片)",
    "ImageDesign": "Image Design Node (设计图片)"
}