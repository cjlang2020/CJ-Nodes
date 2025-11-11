import json
import os
import folder_paths
import comfy.sd
import comfy.utils
from safetensors.torch import load_file, save_file
# 兼容不同版本的ComfyUI
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

def get_core_tags(meta, min_count=10):
    """
    从元数据中提取核心标签
    :param meta: 读取到的完整元数据
    :param min_count: 核心标签的最小出现次数（可调整）
    :return: 排序后的核心标签列表（按出现次数降序）
    """
    tag_freq_str = meta.get("ss_tag_frequency", "{}")
    try:
        tag_freq_dict = json.loads(tag_freq_str)
    except json.JSONDecodeError:
        print("标签数据解析失败")
        return []

    all_tags = {}
    for dataset_key, tags in tag_freq_dict.items():
        for tag, count in tags.items():
            all_tags[tag] = count
    core_tags = [(tag, count) for tag, count in all_tags.items() if count >= min_count]
    core_tags.sort(key=lambda x: x[1], reverse=True)
    return core_tags

def add_metadata(input_path, output_path, new_meta):
    tensors = load_file(input_path, device="cpu")
    with open(input_path, "rb") as f:
        header = f.read(8)
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        original_meta = json.loads(header_data).get("__metadata__", {})

    updated_meta = {**original_meta,** new_meta}
    save_file(tensors, output_path, metadata=updated_meta)
    print(f"已添加元数据并保存到: {output_path}")

class LuySdxlLoraLoader(BaseNode):
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL", {"tooltip": "The diffusion model the LoRA will be applied to."}),
                "clip": ("CLIP", {"tooltip": "The CLIP model the LoRA will be applied to."}),
                "lora_name": (folder_paths.get_filename_list("loras"), {"tooltip": "The name of the LoRA."}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01, "tooltip": "How strongly to modify the diffusion model. This value can be negative."}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01, "tooltip": "How strongly to modify the CLIP model. This value can be negative."}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP","STRING")
    OUTPUT_TOOLTIPS = ("The modified diffusion model.", "The modified CLIP model.","元数据中存储的核心标签，按次数排序，先出现的次数最多.")
    FUNCTION = "load_lora"

    CATEGORY = "luy"
    DESCRIPTION = "LoRAs are used to modify diffusion and CLIP models, altering the way in which latents are denoised such as applying styles. Multiple LoRA nodes can be linked together."

    def load_lora(self, model, clip, lora_name, strength_model, strength_clip):
        if strength_model == 0 and strength_clip == 0:
            return (model, clip)

        lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                self.loaded_lora = None

        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        meta = read_metadata(output_file)
        core_tags = get_core_tags(meta, min_count=1)
        tags=",".join([tag for tag, _ in core_tags])
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        return (model_lora, clip_lora,tags)

class LuyLoraLoaderModelOnly(LuySdxlLoraLoader):
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "lora_name": (folder_paths.get_filename_list("loras"), ),
                              "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                              }}
    RETURN_TYPES = ("MODEL","STRING")
    FUNCTION = "load_lora_model_only"
    CATEGORY = "luy"

    def load_lora_model_only(self, model, lora_name, strength_model):
        output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        meta = read_metadata(output_file)
        keywords="null"
        if "lora_keywords" in meta:
            keywords=meta["lora_keywords"]
        else:
            pass
        return (self.load_lora(model, None, lora_name, strength_model, 0)[0],keywords)

class UpdateLoraMetaData(BaseNode):
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora_name": (folder_paths.get_filename_list("loras"), {"tooltip": "只能更新Flux和Qwen的lora"}),
                "keyWords": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Lora的关键触发词",
                    "rows": 3
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_TOOLTIPS = ("返回提示词即可")
    FUNCTION = "update_lora"
    CATEGORY = "luy"

    def update_lora(self, lora_name,keyWords):
        input_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        output_file = input_file.replace(".safetensors", "_meta.safetensors")
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as e:
                return (f"错误：临时文件已存在且无法删除 - {str(e)}")
        add_metadata(input_file, output_file, {
            "lora_keywords": keyWords
        })
        meta = read_metadata(output_file)

        if "lora_keywords" not in meta or meta["lora_keywords"] != keyWords:
            if os.path.exists(output_file):
                os.remove(output_file)
            return (r"错误：元数据写入验证失败")

        try:
            if os.path.exists(input_file):
                os.remove(input_file)
            os.rename(output_file, input_file)
            return (str(keyWords).strip())
        except Exception as e:
            error_msg = f"替换文件失败: {str(e)}"
            if not os.path.exists(input_file) and os.path.exists(output_file):
                error_msg += "，原文件已删除但新文件重命名失败，请手动将临时文件重命名为原文件名"
                return(error_msg)
        return (str(keyWords).strip())