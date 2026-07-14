import torch
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageGridCrop:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "columns": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
                "rows": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
                "col_gap": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "row_gap": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "grid_crop"
    CATEGORY = "luy/图片处理"

    def grid_crop(self, image, columns, rows, col_gap, row_gap):
        try:
            batch = image.shape[0]
            _, H, W, C = image.shape

            total_gap_w = (columns - 1) * col_gap
            total_gap_h = (rows - 1) * row_gap

            if W <= total_gap_w or H <= total_gap_h:
                raise ValueError(f"图片尺寸({W}x{H})小于间距总和({total_gap_w}x{total_gap_h})")

            panel_w = (W - total_gap_w) // columns
            panel_h = (H - total_gap_h) // rows
            step_w = panel_w + col_gap
            step_h = panel_h + row_gap

            if panel_w <= 0 or panel_h <= 0:
                raise ValueError(f"裁切尺寸({panel_w}x{panel_h})无效，图片太小或间距过大")

            imgs = []
            for i in range(batch):
                img_np = image[i].cpu().numpy()
                if img_np.dtype != np.uint8:
                    img_np = (img_np * 255).astype(np.uint8)

                mode = "RGBA" if C == 4 else "RGB"
                pil_img = Image.fromarray(img_np, mode=mode)

                for r in range(rows):
                    for c in range(columns):
                        left = c * step_w
                        top = r * step_h
                        right = left + panel_w
                        bottom = top + panel_h

                        cropped = pil_img.crop((left, top, right, bottom))
                        out_np = np.array(cropped).astype(np.float32) / 255.0
                        imgs.append(out_np)

            result = torch.from_numpy(np.stack(imgs, axis=0))
            return (result,)

        except Exception as e:
            logger.error(f"图片网格裁切异常: {str(e)}")
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0
            return (error_image,)


NODE_CLASS_MAPPINGS = {
    "ImageGridCrop": ImageGridCrop,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageGridCrop": "Luy-图片网格裁切",
}
