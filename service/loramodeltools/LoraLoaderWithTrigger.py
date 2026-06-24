import json
import os
import hashlib
import folder_paths
import comfy.sd
import comfy.utils

try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass


def read_metadata(file_path):
    with open(file_path, "rb") as f:
        header = f.read(8)
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        return json.loads(header_data).get("__metadata__", {})


def build_lora_tree():
    tree = {}
    loras_roots = folder_paths.get_folder_paths("loras")
    if not loras_roots:
        return tree
    loras_root = loras_roots[0]
    if not os.path.isdir(loras_root):
        return tree
    valid_exts = (".safetensors", ".ckpt", ".pt")

    # 根目录下的lora文件
    root_files = [
        f for f in sorted(os.listdir(loras_root))
        if os.path.isfile(os.path.join(loras_root, f)) and f.lower().endswith(valid_exts)
    ]
    if root_files:
        tree[".."] = root_files

    # 子文件夹
    for item in sorted(os.listdir(loras_root)):
        item_path = os.path.join(loras_root, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            files = [
                f for f in sorted(os.listdir(item_path))
                if os.path.isfile(os.path.join(item_path, f)) and f.lower().endswith(valid_exts)
            ]
            if files:
                tree[item] = files
    return tree


LORA_TREE = build_lora_tree()
TREE_JSON = json.dumps(LORA_TREE, ensure_ascii=False)


class LoraLoaderWithTrigger(BaseNode):
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL", {"tooltip": "输入的扩散模型"}),
                "strength_model": ("FLOAT", {
                    "default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01,
                    "tooltip": "Lora对模型的修改强度"
                }),
            },
            "optional": {
                "lora_tree_json": ("STRING", {
                    "default": TREE_JSON,
                    "multiline": False,
                    "tooltip": "内部数据，前端自定义UI使用"
                }),
            }
        }

    RETURN_TYPES = ("MODEL", "STRING")
    RETURN_NAMES = ("model", "lora_trigger_text")
    OUTPUT_TOOLTIPS = ("应用Lora后的模型", "从Lora元数据中读取的触发词")
    FUNCTION = "load_lora_with_trigger"
    CATEGORY = "luy/模型加载"
    DESCRIPTION = "加载Lora模型并输出触发词，支持按文件夹分类浏览"

    @classmethod
    def IS_CHANGED(cls, model, strength_model, lora_tree_json=""):
        return ""

    def load_lora_with_trigger(self, model, strength_model, lora_tree_json=""):
        lora_dir = getattr(self, "_selected_dir", "")
        lora_name = getattr(self, "_selected_name", "")

        if strength_model == 0 or not lora_name or not lora_dir:
            return (model, "null")

        loras_roots = folder_paths.get_folder_paths("loras")
        if not loras_roots:
            return (model, "null")

        if lora_dir == "..":
            lora_path = os.path.join(loras_roots[0], lora_name)
        else:
            lora_path = os.path.join(loras_roots[0], lora_dir, lora_name)
        if not os.path.isfile(lora_path):
            return (model, "null")

        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                self.loaded_lora = None

        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        trigger_text = "null"
        try:
            meta = read_metadata(lora_path)
            if "lora_keywords" in meta and meta["lora_keywords"]:
                trigger_text = meta["lora_keywords"]
        except Exception:
            pass

        model_lora, _ = comfy.sd.load_lora_for_models(model, None, lora, strength_model, 0)
        return (model_lora, trigger_text)
