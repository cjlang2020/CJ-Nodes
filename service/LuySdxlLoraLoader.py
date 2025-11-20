import json
import os
import folder_paths
import comfy.sd
import comfy.utils
import random
from typing import List, Tuple
from safetensors.torch import load_file, save_file
# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass


# 先获取 "loras" 根目录的路径
loras_root = folder_paths.get_folder_paths("loras")[0]  # 取第一个配置的 loras 目录
flux_loras_dir = os.path.join(loras_root, "FLUX")
flux_lora_files = [f for f in os.listdir(flux_loras_dir) if os.path.isfile(os.path.join(flux_loras_dir, f))]
flux_lora_files = [os.path.join("FLUX", f) for f in flux_lora_files]

qwen_loras_dir = os.path.join(loras_root, "Qwen")
qwen_lora_files = [f for f in os.listdir(qwen_loras_dir) if os.path.isfile(os.path.join(qwen_loras_dir, f))]
qwen_lora_files = [os.path.join("Qwen", f) for f in qwen_lora_files]

qwen_edit_loras_dir = os.path.join(loras_root, "Qwen-Edit")
qwen_edit_lora_files = [f for f in os.listdir(qwen_edit_loras_dir) if os.path.isfile(os.path.join(qwen_edit_loras_dir, f))]
qwen_edit_lora_files = [os.path.join("Qwen-Edit", f) for f in qwen_edit_lora_files]

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
                "selection_mode": (
                    ["随机", "最高频率", "最低频率", "中间值"],
                    {"tooltip": "选择标签的筛选模式"}
                ),
                "tag_count": (
                    "INT",
                    {"default": 5, "min": 1, "step": 1, "tooltip": "限制输出的标签数量"}
                )
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING",)
    RETURN_NAMES =("模型","CLIP","内置触发词",)
    OUTPUT_TOOLTIPS = ("The modified diffusion model.", "The modified CLIP model.", "元数据中存储的核心标签，按选择模式筛选后的结果.")
    FUNCTION = "load_lora"

    CATEGORY = "luy/元数据"
    DESCRIPTION = "LoRAs are used to modify diffusion and CLIP models, altering the way in which latents are denoised such as applying styles. Multiple LoRA nodes can be linked together."

    def load_lora(self, model, clip, lora_name, strength_model, strength_clip, selection_mode, tag_count):
        if strength_model == 0 and strength_clip == 0:
            return (model, clip, "")

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
        tags=""
        if selection_mode != None:
            output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
            meta = read_metadata(output_file)
            core_tags = get_core_tags(meta, min_count=1)  # 格式应为 [(tag1, count1), (tag2, count2), ...]

            # 根据选择模式筛选标签
            filtered_tags = self.filter_tags(core_tags, selection_mode, tag_count)
            tags = ",".join(filtered_tags)

        model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        return (model_lora, clip_lora, tags,)

    def filter_tags(self, core_tags: List[Tuple[str, int]], mode: str, count: int) -> List[str]:
        """根据选择模式筛选标签"""
        if not core_tags:
            return []

        # 确保不超过实际标签数量
        actual_count = min(count, len(core_tags))
        if actual_count <= 0:
            return []

        if mode == "随机":
            # 随机选择指定数量的标签
            shuffled = random.sample(core_tags, actual_count)
            return [tag for tag, _ in shuffled]

        elif mode == "最高频率":
            # 按频率降序排序，取前N个
            sorted_tags = sorted(core_tags, key=lambda x: x[1], reverse=True)
            return [tag for tag, _ in sorted_tags[:actual_count]]

        elif mode == "最低频率":
            # 按频率升序排序，取前N个
            sorted_tags = sorted(core_tags, key=lambda x: x[1])
            return [tag for tag, _ in sorted_tags[:actual_count]]

        elif mode == "中间值":
            # 按频率排序后取中间位置的标签
            sorted_tags = sorted(core_tags, key=lambda x: x[1])
            total = len(sorted_tags)
            # 计算中间起始索引
            start_idx = (total - actual_count) // 2
            return [tag for tag, _ in sorted_tags[start_idx:start_idx + actual_count]]

        return []

class LuyLoraLoaderModelOnlyALL(LuySdxlLoraLoader):
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "lora_name": (folder_paths.get_filename_list("loras"), ),
                              "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                              }}
    RETURN_TYPES = ("MODEL","STRING",)
    FUNCTION = "load_lora_model_only"
    RETURN_NAMES =("模型","内置触发词",)
    CATEGORY = "luy/元数据"

    def load_lora_model_only(self, model, lora_name, strength_model):
        output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        meta = read_metadata(output_file)
        keywords="null"
        if "lora_keywords" in meta:
            keywords=meta["lora_keywords"]
        else:
            pass
        return (self.load_lora(model, None, lora_name, strength_model, 0,None,None)[0],keywords,)

class LuyLoraLoaderModelOnlyFLUX(LuySdxlLoraLoader):
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "lora_name": (flux_lora_files, ),
                              "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                              }}
    RETURN_TYPES = ("MODEL","STRING",)
    FUNCTION = "load_lora_model_only"
    RETURN_NAMES =("模型","内置触发词",)
    CATEGORY = "luy/元数据"

    def load_lora_model_only(self, model, lora_name, strength_model):
        output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        meta = read_metadata(output_file)
        keywords="null"
        if "lora_keywords" in meta:
            keywords=meta["lora_keywords"]
        else:
            pass
        return (self.load_lora(model, None, lora_name, strength_model, 0,None,None)[0],keywords,)

class LuyLoraLoaderModelOnlyQWEN(LuySdxlLoraLoader):
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "lora_name": (qwen_lora_files, ),
                              "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                              }}
    RETURN_TYPES = ("MODEL","STRING",)
    FUNCTION = "load_lora_model_only"
    RETURN_NAMES =("模型","内置触发词",)
    CATEGORY = "luy/元数据"

    def load_lora_model_only(self, model, lora_name, strength_model):
        output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        meta = read_metadata(output_file)
        keywords="null"
        if "lora_keywords" in meta:
            keywords=meta["lora_keywords"]
        else:
            pass
        return (self.load_lora(model, None, lora_name, strength_model, 0,None,None)[0],keywords,)

class LuyLoraLoaderModelOnlyQWENEDIT(LuySdxlLoraLoader):
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "lora_name": (qwen_edit_lora_files, ),
                              "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
                              }}
    RETURN_TYPES = ("MODEL","STRING",)
    FUNCTION = "load_lora_model_only"
    RETURN_NAMES =("模型","内置触发词",)
    CATEGORY = "luy/元数据"

    def load_lora_model_only(self, model, lora_name, strength_model):
        output_file = folder_paths.get_full_path_or_raise("loras", lora_name)
        meta = read_metadata(output_file)
        keywords="null"
        if "lora_keywords" in meta:
            keywords=meta["lora_keywords"]
        else:
            pass
        return (self.load_lora(model, None, lora_name, strength_model, 0,None,None)[0],keywords,)


class LuyLoraLoaderModelOnlyByDir(LuySdxlLoraLoader):
    # 类级属性：保存最后选择的目录和刷新触发值
    _last_selected_dir = None
    _refresh_trigger = 0

    @classmethod
    def INPUT_TYPES(s):
        # 获取Lora根目录
        loras_roots = folder_paths.get_folder_paths("loras")
        loras_root = loras_roots[0] if loras_roots else ""

        # 枚举所有子目录作为选项
        dir_options = []
        if os.path.isdir(loras_root):
            for item in os.listdir(loras_root):
                item_path = os.path.join(loras_root, item)
                if os.path.isdir(item_path) and not item.startswith('.'):  # 排除隐藏目录
                    dir_options.append(item)

        # 动态加载当前目录下的Lora文件
        lora_files = []
        if s._last_selected_dir and s._last_selected_dir in dir_options:
            lora_files = s._get_lora_files_in_dir(s._last_selected_dir)

        return {
            "required": {
                "model": ("MODEL",),
                "lora_dir": (dir_options, {"tooltip": "选择Lora所在的目录"}),
                "lora_name": (lora_files, {"tooltip": "选择目录中的Lora模型"}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -100.0, "max": 100.0, "step": 0.01}),
            }
        }

    # 辅助方法：获取指定目录下的Lora文件
    @classmethod
    def _get_lora_files_in_dir(cls, lora_dir):
        loras_roots = folder_paths.get_folder_paths("loras")
        loras_root = loras_roots[0] if loras_roots else ""
        target_dir = os.path.join(loras_root, lora_dir)

        lora_files = []
        if os.path.isdir(target_dir):
            for file in os.listdir(target_dir):
                file_path = os.path.join(target_dir, file)
                if os.path.isfile(file_path) and file.lower().endswith((".safetensors", ".ckpt", ".pt")):
                    lora_files.append(file)
        return lora_files

    # 关键：ComfyUI触发参数刷新的核心方法
    @classmethod
    def IS_CHANGED(cls, model, lora_dir, lora_name, strength_model):
        print("======"+lora_dir)
        # 检测目录是否变化
        if cls._last_selected_dir != lora_dir:
            cls._last_selected_dir = lora_dir  # 更新状态
            cls._refresh_trigger += 1  # 改变触发值
            return True  # 告知ComfyUI需要刷新
        # 如果目录未变，返回触发值的哈希（确保稳定性）
        return hash((cls._refresh_trigger, lora_dir))

    RETURN_TYPES = ("MODEL","STRING")
    FUNCTION = "load_lora_model_only"
    CATEGORY = "luy/元数据"

    def load_lora_model_only(self, model, lora_dir, lora_name, strength_model):
        # 保存当前选择的目录（更新类状态）
        self.__class__._last_selected_dir = lora_dir

        # 构建完整的Lora路径
        loras_roots = folder_paths.get_folder_paths("loras")
        loras_root = loras_roots[0] if loras_roots else ""
        lora_full_path = os.path.join(loras_root, lora_dir, lora_name)

        # 验证文件存在性
        if not os.path.isfile(lora_full_path):
            raise FileNotFoundError(f"Lora文件不存在: {lora_full_path}")

        # 读取元数据中的关键词
        meta = read_metadata(lora_full_path)
        keywords = meta.get("lora_keywords", "null")

        # 加载Lora模型（使用相对路径）
        relative_path = os.path.join(lora_dir, lora_name)
        model_lora = self.load_lora(model, None, relative_path, strength_model, 0, None, None)[0]

        return (model_lora, keywords,)


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
    CATEGORY = "luy/元数据"

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
            print("=================="+keyWords)
            return (str(keyWords).strip())
        except Exception as e:
            error_msg = f"替换文件失败: {str(e)}"
            if not os.path.exists(input_file) and os.path.exists(output_file):
                error_msg += "，原文件已删除但新文件重命名失败，请手动将临时文件重命名为原文件名"
                return(error_msg)
        return (str(keyWords).strip())