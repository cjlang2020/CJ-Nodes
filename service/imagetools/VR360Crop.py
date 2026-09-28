from __future__ import annotations
import os
import torch
import numpy as np
from PIL import Image
import json
import base64
from io import BytesIO

import folder_paths


def _resolve_input_file(rel_path):
    """解析前端上传的截图文件（input/cj_canvas/），并做路径包含校验（同 ImageEditNode._resolve_canvas_file）"""
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


class VR360Crop:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "output_width": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "output_height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "crop_data": ("STRING", {"default": "empty"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "2:1 360全景图片输入（可选，也可在前端直接上传）"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "crop_panorama"

    OUTPUT_NODE = False

    CATEGORY = "luy/图像处理"
    DESCRIPTION = "360全景图片裁剪为指定视角的图片，支持鼠标拖拽旋转和滚轮缩放"

    def crop_panorama(self, output_width=1024, output_height=512, crop_data="empty", image=None):
        final_img = Image.new("RGB", (output_width, output_height), (0, 0, 0))

        if crop_data != "empty" and crop_data.strip():
            try:
                data = json.loads(crop_data)
                # 优先使用上传到服务器的截图文件（新格式，widget 不再持久化 base64），
                # 旧工作流内嵌的 image_base64 仍兼容
                img = None
                file_ref = data.get("image_file")
                if file_ref:
                    path = _resolve_input_file(file_ref)
                    if path is None:
                        print(f"[VR360Crop] 截图文件不存在，改用中心裁剪: {file_ref}")
                    else:
                        with Image.open(path) as im:
                            img = im.convert("RGB")
                else:
                    final_base64 = data.get("image_base64", "")
                    if final_base64:
                        img_data = base64.b64decode(final_base64.split(",")[-1])
                        img = Image.open(BytesIO(img_data)).convert("RGB")
                if img is not None:
                    if img.size != (output_width, output_height):
                        img = img.resize((output_width, output_height), Image.LANCZOS)
                    final_img = img
            except Exception as e:
                print(f"[VR360Crop] crop_data解析失败: {e}")
                if image is not None:
                    final_img = self._center_crop_pil(image, output_width, output_height)
        elif image is not None:
            final_img = self._center_crop_pil(image, output_width, output_height)

        image_np = np.array(final_img)
        if image_np.dtype != np.uint8:
            image_np = image_np.astype(np.uint8)
        image_np = image_np.astype(np.float32) / 255.0
        if len(image_np.shape) == 2:
            image_np = np.stack([image_np, image_np, image_np], axis=-1)
        elif image_np.shape[-1] == 4:
            image_np = image_np[:, :, :3]
        image_tensor = torch.from_numpy(image_np).unsqueeze(0)

        return {"result": (image_tensor,), "ui": {"vr360_input_image": [self._encode_input_image(image)] if image is not None else []}}

    def _center_crop_pil(self, tensor, w, h):
        if tensor.dim() == 4:
            img_np = (tensor[0].cpu().numpy() * 255).astype(np.uint8)
        else:
            img_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_np).convert("RGB")
        img_w, img_h = pil_img.size
        left = max(0, (img_w - w) // 2)
        top = max(0, (img_h - h) // 2)
        right = min(img_w, left + w)
        bottom = min(img_h, top + h)
        cropped = pil_img.crop((left, top, right, bottom))
        if cropped.size != (w, h):
            cropped = cropped.resize((w, h), Image.LANCZOS)
        return cropped

    def _encode_input_image(self, tensor):
        if tensor is None:
            return ""
        if tensor.dim() == 4:
            img_np = (tensor[0].cpu().numpy() * 255).astype(np.uint8)
        else:
            img_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_np).convert("RGB")
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
