import os
import sys
import re
import json
import gc
import torch
import numpy as np
from PIL import Image, ImageDraw
import folder_paths

_INFERENCE_SRC = r"D:\AI\LocateAnything-3B\src"
if _INFERENCE_SRC not in sys.path:
    sys.path.insert(0, _INFERENCE_SRC)

from inference import LocateAnythingWorker

_MODEL_CACHE = {}

_COLORS = [
    "red", "blue", "green", "orange", "purple", "cyan",
    "magenta", "lime", "pink", "teal", "navy", "maroon",
]

LABEL_PATTERN = re.compile(r"<ref>(.*?)</ref>")


class LocateAnythingNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "model_type": (["nf4", "fp8"], {"default": "nf4"}),
                "prompt": ("STRING", {
                    "default": "person, car",
                    "multiline": True,
                    "placeholder": "输入检测目标，多个用逗号分隔",
                }),
                "task": (["detect", "ground_single", "ground_multi", "detect_text", "point"], {
                    "default": "detect",
                }),
                "mode": (["hybrid", "fast", "slow"], {
                    "default": "hybrid",
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 64,
                    "max": 8192,
                    "step": 64,
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.05,
                }),
                "max_image_side": ("INT", {
                    "default": 640,
                    "min": 256,
                    "max": 2048,
                    "step": 64,
                    "tooltip": "输入图片最长边限制。值越大精度越高但显存消耗剧增，8GB显存建议≤640",
                }),
                "unload_model": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "推理后卸载模型释放显存，下次推理重新加载",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "bbox_json")
    FUNCTION = "process"
    CATEGORY = "luy/目标检测"

    def _get_worker(self, model_type: str) -> LocateAnythingWorker:
        model_path = os.path.join(
            folder_paths.models_dir, "LocateAnything-3B", model_type
        )
        if not os.path.isdir(model_path):
            raise RuntimeError(
                f"模型路径不存在: {model_path}\n"
                f"请将 LocateAnything-3B 模型放入 "
                f"{os.path.join(folder_paths.models_dir, 'LocateAnything-3B')} 目录下的 fp8 或 nf4 子文件夹中。"
            )
        if model_path not in _MODEL_CACHE:
            _MODEL_CACHE[model_path] = LocateAnythingWorker(model_path)
        return _MODEL_CACHE[model_path]

    def _unload(self, model_type: str):
        model_path = os.path.join(
            folder_paths.models_dir, "LocateAnything-3B", model_type
        )
        worker = _MODEL_CACHE.pop(model_path, None)
        if worker is not None:
            del worker
        gc.collect()
        torch.cuda.empty_cache()

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
    def _preprocess(img: Image.Image, max_side: int) -> Image.Image:
        w, h = img.size
        if max(w, h) > max_side:
            img = img.copy()
            img.thumbnail((max_side, max_side), Image.LANCZOS)
        return img

    def process(self, image, model_type, prompt, task, mode, max_tokens, temperature, max_image_side, unload_model):
        pil_img = self._tensor2pil(image)
        orig_w, orig_h = pil_img.size
        pil_img = self._preprocess(pil_img, max_image_side)
        inf_w, inf_h = pil_img.size

        worker = self._get_worker(model_type)

        task_map = {
            "detect": lambda: worker.detect(
                pil_img,
                [p.strip() for p in prompt.split(",") if p.strip()],
                generation_mode=mode,
                max_new_tokens=max_tokens,
                temperature=temperature,
            ),
            "ground_single": lambda: worker.ground_single(
                pil_img, prompt,
                generation_mode=mode,
                max_new_tokens=max_tokens,
                temperature=temperature,
            ),
            "ground_multi": lambda: worker.ground_multi(
                pil_img, prompt,
                generation_mode=mode,
                max_new_tokens=max_tokens,
                temperature=temperature,
            ),
            "detect_text": lambda: worker.detect_text(
                pil_img,
                generation_mode=mode,
                max_new_tokens=max_tokens,
                temperature=temperature,
            ),
            "point": lambda: worker.point(
                pil_img, prompt,
                generation_mode=mode,
                max_new_tokens=max_tokens,
                temperature=temperature,
            ),
        }

        if task not in task_map:
            raise ValueError(f"未知任务类型: {task}")

        result = task_map[task]()
        answer = result["answer"]

        boxes = LocateAnythingWorker.parse_boxes(answer, inf_w, inf_h)
        points = LocateAnythingWorker.parse_points(answer, inf_w, inf_h)
        labels = LABEL_PATTERN.findall(answer)

        scale_x = orig_w / inf_w
        scale_y = orig_h / inf_h

        bbox_list = []
        for i, b in enumerate(boxes):
            bbox_list.append({
                "label": labels[i] if i < len(labels) else "",
                "bbox": {
                    "x1": round(b["x1"] * scale_x, 2),
                    "y1": round(b["y1"] * scale_y, 2),
                    "x2": round(b["x2"] * scale_x, 2),
                    "y2": round(b["y2"] * scale_y, 2),
                },
            })

        full_img = self._tensor2pil(image)
        draw = ImageDraw.Draw(full_img)
        for i, b in enumerate(boxes):
            color = _COLORS[i % len(_COLORS)]
            x1 = b["x1"] * scale_x
            y1 = b["y1"] * scale_y
            x2 = b["x2"] * scale_x
            y2 = b["y2"] * scale_y
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            if i < len(labels):
                draw.text((x1 + 2, y1 - 14), labels[i], fill=color)

        for p in points:
            draw.ellipse([p["x"] * scale_x - 5, p["y"] * scale_y - 5,
                          p["x"] * scale_x + 5, p["y"] * scale_y + 5], fill="blue")

        if unload_model:
            self._unload(model_type)

        out_tensor = self._pil2tensor(full_img)
        return (out_tensor, json.dumps(bbox_list, ensure_ascii=False))


NODE_CLASS_MAPPINGS = {
    "LocateAnythingNode": LocateAnythingNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LocateAnythingNode": "Luy-LocateAnything 目标检测",
}
