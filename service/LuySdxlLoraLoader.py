import json
import folder_paths
import comfy.sd
import comfy.utils
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
    # 提取标签频率字符串并解析为JSON
    tag_freq_str = meta.get("ss_tag_frequency", "{}")
    try:
        tag_freq_dict = json.loads(tag_freq_str)
    except json.JSONDecodeError:
        print("标签数据解析失败")
        return []

    # 提取所有标签（忽略数据集分组键，如"5_zkz"）
    all_tags = {}
    for dataset_key, tags in tag_freq_dict.items():
        for tag, count in tags.items():
            all_tags[tag] = count  # 若有重复标签（多数据集），取最后一次出现的计数

    # 筛选核心标签（出现次数≥min_count）并按次数降序排序
    core_tags = [(tag, count) for tag, count in all_tags.items() if count >= min_count]
    core_tags.sort(key=lambda x: x[1], reverse=True)
    return core_tags


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
        # 读取核心标签（最小出现次数设为1，可根据需求调整）
        core_tags = get_core_tags(meta, min_count=1)
        tags=",".join([tag for tag, _ in core_tags])
        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        return (model_lora, clip_lora,tags)
