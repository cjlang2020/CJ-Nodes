import json
import base64
import torch
import numpy as np
from PIL import Image
import io


class EditRegionNode:
    """图片区域编辑节点 - 前端画布绘制BBOX区域并标记编辑提示"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "frontend_data": ("STRING", {"default": "", "multiline": True,
                                            "tooltip": "前端序列化的完整参数JSON（隐藏）"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "prompt_json")
    FUNCTION = "process"
    CATEGORY = "luy/提示词"

    def process(self, frontend_data=""):
        data = self._parse(frontend_data)

        image = self._decode_image(data.get("image_data", ""))
        if image is None:
            image = self._create_blank_image()

        prompt_text = data.get("prompt_text", "")
        edit_items = data.get("edit_items", [])

        output_items = []
        for item in edit_items:
            bbox_px = item.get("bbox_px", [0, 0, 0, 0])
            bbox_str = ",".join(str(max(0, round(v))) for v in bbox_px[:4])
            output_items.append({
                "bbox": bbox_str,
                "edit_text": item.get("edit_text", "")
            })

        prompt_json = json.dumps({
            "prompt_text": prompt_text,
            "edit_items": output_items
        }, ensure_ascii=False, indent=2)

        return (image, prompt_json)

    def _parse(self, raw):
        if not raw:
            return {}
        try:
            d = json.loads(raw)
            return d if isinstance(d, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def _decode_image(self, image_data):
        if not image_data:
            return None
        try:
            if image_data.startswith("data:"):
                image_data = image_data.split(",", 1)[1]
            img_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_np = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(img_np).unsqueeze(0)
        except Exception as e:
            print(f"[EditRegionNode] Error decoding image: {e}")
            return None

    def _create_blank_image(self):
        img = Image.new("RGB", (512, 512), color=(128, 128, 128))
        img_np = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)
