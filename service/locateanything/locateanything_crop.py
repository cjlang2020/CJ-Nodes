import os
import json
import uuid
from collections import deque
import torch
import numpy as np
from PIL import Image, ImageFilter
import folder_paths


class LocateAnythingCropNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "bbox_json": ("STRING", {"multiline": True}),
                "output_dir": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "留空则使用 ComfyUI output 目录",
                }),
                "remove_bg": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "从边缘去除指定背景色，物体内部同色区域不受影响",
                }),
                "bg_color": ("STRING", {
                    "default": "#FFFFFF",
                    "multiline": False,
                    "placeholder": "十六进制颜色值，如 #FFFFFF",
                }),
                "tolerance": ("INT", {
                    "default": 7,
                    "min": 0,
                    "max": 128,
                    "step": 1,
                    "tooltip": "颜色匹配容差，越大去除范围越广",
                }),
                "feather": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "边缘羽化像素数，0=不羽化",
                }),
                "feather_bg": ("STRING", {
                    "default": "#FFFFFF",
                    "multiline": False,
                    "placeholder": "羽化边缘混合到此背景色，可避免阴影",
                }),
            },
        }

    RETURN_TYPES = ("INT", "IMAGE")
    RETURN_NAMES = ("count", "preview")
    FUNCTION = "crop"
    CATEGORY = "luy/目标检测"

    @staticmethod
    def _tensor2pil(image: torch.Tensor) -> Image.Image:
        i = image[0].cpu().numpy()
        i = (i * 255).astype(np.uint8)
        return Image.fromarray(i, mode="RGB")

    @staticmethod
    def _pil2tensor(img: Image.Image) -> torch.Tensor:
        arr = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(arr)[None, ...]

    @staticmethod
    def _remove_edge_color(img: Image.Image, bg_hex: str, tolerance: int) -> Image.Image:
        bg_hex = bg_hex.lstrip("#")
        target_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (0, 2, 4))

        arr = np.array(img, dtype=np.uint8)
        h, w = arr.shape[:2]

        dr = arr[:, :, 0].astype(np.int32) - target_rgb[0]
        dg = arr[:, :, 1].astype(np.int32) - target_rgb[1]
        db = arr[:, :, 2].astype(np.int32) - target_rgb[2]
        color_mask = (dr * dr + dg * dg + db * db) <= tolerance * tolerance

        visited = np.zeros((h, w), dtype=bool)
        q = deque()

        for x in range(w):
            if color_mask[0, x] and not visited[0, x]:
                visited[0, x] = True
                q.append((0, x))
            if color_mask[h - 1, x] and not visited[h - 1, x]:
                visited[h - 1, x] = True
                q.append((h - 1, x))
        for y in range(h):
            if color_mask[y, 0] and not visited[y, 0]:
                visited[y, 0] = True
                q.append((y, 0))
            if color_mask[y, w - 1] and not visited[y, w - 1]:
                visited[y, w - 1] = True
                q.append((y, w - 1))

        while q:
            cy, cx = q.popleft()
            if cy > 0 and not visited[cy - 1, cx] and color_mask[cy - 1, cx]:
                visited[cy - 1, cx] = True
                q.append((cy - 1, cx))
            if cy < h - 1 and not visited[cy + 1, cx] and color_mask[cy + 1, cx]:
                visited[cy + 1, cx] = True
                q.append((cy + 1, cx))
            if cx > 0 and not visited[cy, cx - 1] and color_mask[cy, cx - 1]:
                visited[cy, cx - 1] = True
                q.append((cy, cx - 1))
            if cx < w - 1 and not visited[cy, cx + 1] and color_mask[cy, cx + 1]:
                visited[cy, cx + 1] = True
                q.append((cy, cx + 1))

        out = arr.copy()
        out[visited, 3] = 0
        return Image.fromarray(out, mode="RGBA")

    @staticmethod
    def _apply_feather(img: Image.Image, radius: int, bg_hex: str) -> Image.Image:
        if radius <= 0:
            return img
        bg_hex = bg_hex.lstrip("#")
        bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (0, 2, 4))

        pad = radius * 2
        padded = Image.new("RGBA", (img.width + pad, img.height + pad), (*bg_rgb, 0))
        padded.paste(img, (radius, radius), img)

        alpha = padded.split()[3]
        blurred = np.array(alpha.filter(ImageFilter.GaussianBlur(radius=radius)), dtype=np.uint8)

        out = np.array(padded, dtype=np.uint8)
        out[:, :, 3] = blurred

        return Image.fromarray(out, mode="RGBA").crop(
            (radius, radius, radius + img.width, radius + img.height))

    def crop(self, image, bbox_json, output_dir, remove_bg, bg_color, tolerance, feather, feather_bg):
        pil_img = self._tensor2pil(image)

        bbox_list = json.loads(bbox_json)
        if not bbox_list:
            return (0, torch.zeros((1, 64, 64, 3), dtype=torch.float32))

        if not output_dir.strip():
            output_dir = folder_paths.get_output_directory()
        os.makedirs(output_dir, exist_ok=True)

        cropped_pils = []
        count = 0

        for item in bbox_list:
            b = item["bbox"]
            x1 = max(0, int(b["x1"]))
            y1 = max(0, int(b["y1"]))
            x2 = min(pil_img.width, int(b["x2"]))
            y2 = min(pil_img.height, int(b["y2"]))

            if x2 <= x1 or y2 <= y1:
                continue

            crop_rgba = pil_img.crop((x1, y1, x2, y2)).convert("RGBA")

            if remove_bg:
                crop_rgba = self._remove_edge_color(crop_rgba, bg_color, tolerance)

            if feather > 0:
                crop_rgba = self._apply_feather(crop_rgba, feather, feather_bg)

            filename = f"{uuid.uuid4().hex}.png"
            filepath = os.path.join(output_dir, filename)
            crop_rgba.save(filepath, "PNG")
            count += 1
            cropped_pils.append(crop_rgba)

        if not cropped_pils:
            return (0, torch.zeros((1, 64, 64, 3), dtype=torch.float32))

        import math
        n = len(cropped_pils)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        pad = 10
        cell_size = max(max(img.width, img.height) for img in cropped_pils)
        grid_w = cols * cell_size + (cols - 1) * pad
        grid_h = rows * cell_size + (rows - 1) * pad
        preview = Image.new("RGBA", (grid_w, grid_h), (0, 0, 0, 0))
        for idx, img in enumerate(cropped_pils):
            cx = (idx % cols) * (cell_size + pad)
            cy = (idx // cols) * (cell_size + pad)
            if img.width > cell_size or img.height > cell_size:
                img.thumbnail((cell_size, cell_size), Image.LANCZOS)
            preview.paste(img, (cx + (cell_size - img.width) // 2, cy + (cell_size - img.height) // 2), img)

        preview_rgb = Image.new("RGB", preview.size, (0, 0, 0))
        preview_rgb.paste(preview, mask=preview.split()[3])

        return (count, self._pil2tensor(preview_rgb))


NODE_CLASS_MAPPINGS = {
    "LocateAnythingCropNode": LocateAnythingCropNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LocateAnythingCropNode": "Luy-LocateAnything 裁剪提取",
}
