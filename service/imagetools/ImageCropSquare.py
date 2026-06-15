import torch
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageCropSquare:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "crop_position": (["左上角", "右上角", "左下角", "右下角", "中央"],),
                "crop_type": (["最短边", "1024像素"],),
                "scale": (["是", "否"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "crop_square"
    CATEGORY = "luy/图片处理"

    def crop_square(self, image, crop_position, crop_type, scale):
        try:
            batch = image.shape[0]
            H, W = image.shape[1], image.shape[2]

            short_side = min(W, H)
            if crop_type == "1024像素":
                size = min(1024, short_side)
            else:
                size = short_side

            if crop_position == "左上角":
                left, top = 0, 0
            elif crop_position == "右上角":
                left, top = W - size, 0
            elif crop_position == "左下角":
                left, top = 0, H - size
            elif crop_position == "右下角":
                left, top = W - size, H - size
            else:
                left, top = (W - size) // 2, (H - size) // 2

            imgs = []
            for i in range(batch):
                img_np = image[i].cpu().numpy()
                if img_np.dtype != np.uint8:
                    img_np = (img_np * 255).astype(np.uint8)

                if img_np.shape[-1] == 4:
                    img_np = img_np[:, :, :3]

                pil_img = Image.fromarray(img_np, mode="RGB")
                cropped = pil_img.crop((left, top, left + size, top + size))

                if scale == "是":
                    cropped = cropped.resize((1024, 1024), Image.LANCZOS)

                out_np = np.array(cropped).astype(np.float32) / 255.0
                imgs.append(out_np)

            result = torch.from_numpy(np.stack(imgs, axis=0))
            return (result,)

        except Exception as e:
            logger.error(f"图片裁切正方形异常: {str(e)}")
            error_image = torch.ones((1, 200, 200, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0
            return (error_image,)


NODE_CLASS_MAPPINGS = {
    "ImageCropSquare": ImageCropSquare,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageCropSquare": "Luy-图片裁切正方形",
}
