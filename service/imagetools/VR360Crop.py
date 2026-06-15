from __future__ import annotations
import torch
import numpy as np
from PIL import Image
import io
import base64


class VR360Crop:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "output_width": ("INT", {"default": 1024, "min": 64, "max": 4096, "step": 8}),
                "output_height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "2:1 360全景图片输入（可选，也可在前端直接上传）"}),
            },
            "hidden": {
                "cropped_data": ("STRING", {"default": ""}),
                "panorama_b64": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "crop_panorama"

    OUTPUT_NODE = False

    CATEGORY = "luy/图像处理"
    DESCRIPTION = "360全景图片裁剪为指定视角的图片，支持鼠标拖拽旋转和滚轮缩放"

    def crop_panorama(self, output_width=1024, output_height=512, image=None, cropped_data="", panorama_b64=""):
        pano_b64 = panorama_b64
        if image is not None:
            pano_b64 = self._tensor_to_base64(image)

        if cropped_data:
            try:
                output = self._base64_to_tensor(cropped_data, output_width, output_height)
            except Exception as e:
                print(f"[VR360Crop] 裁剪数据解码失败: {e}")
                if image is not None:
                    output = self._center_crop(image, output_width, output_height)
                else:
                    output = self._blank_tensor(output_width, output_height)
        elif image is not None:
            output = self._center_crop(image, output_width, output_height)
        else:
            output = self._blank_tensor(output_width, output_height)

        return {
            "ui": {"panorama_b64": pano_b64},
            "result": (output,)
        }

    def _tensor_to_base64(self, tensor):
        if tensor.dim() == 4:
            img_np = (tensor[0].cpu().numpy() * 255).astype(np.uint8)
        else:
            img_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
        if img_np.shape[-1] == 4:
            pil_img = Image.fromarray(img_np, 'RGBA').convert('RGB')
        else:
            pil_img = Image.fromarray(img_np)
        buffer = io.BytesIO()
        pil_img.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def _base64_to_tensor(self, b64_str, target_w, target_h):
        buffer = io.BytesIO(base64.b64decode(b64_str))
        pil_img = Image.open(buffer).convert('RGB')
        if pil_img.size != (target_w, target_h):
            pil_img = pil_img.resize((target_w, target_h), Image.LANCZOS)
        img_np = np.array(pil_img).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)

    def _center_crop(self, tensor, w, h):
        if tensor.dim() == 4:
            img_np = (tensor[0].cpu().numpy() * 255).astype(np.uint8)
        else:
            img_np = (tensor.cpu().numpy() * 255).astype(np.uint8)
        if img_np.shape[-1] == 4:
            pil_img = Image.fromarray(img_np, 'RGBA').convert('RGB')
        else:
            pil_img = Image.fromarray(img_np)
        img_w, img_h = pil_img.size
        left = (img_w - w) // 2
        top = (img_h - h) // 2
        left = max(0, min(left, img_w - w))
        top = max(0, min(top, img_h - h))
        cropped = pil_img.crop((left, top, left + w, top + h))
        if cropped.size != (w, h):
            cropped = cropped.resize((w, h), Image.LANCZOS)
        img_np = np.array(cropped).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)

    def _blank_tensor(self, w, h):
        return torch.zeros((1, h, w, 3), dtype=torch.float32)
