import folder_paths
import torch
import os
import json  # 新增：用于序列化/反序列化列表
from PIL import Image
import numpy as np
from comfy.utils import common_upscale
import torchvision.transforms as T

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class BatchImageLoader:
    """批量图片加载节点（保留原有逻辑，无修改）"""
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_folder": ("STRING", {"default": "input/images", "placeholder": "输入图片文件夹路径"}),
                "max_images": ("INT", {"default": 10, "min": 1, "max": 100, "step": 1, "placeholder": "最大加载图片数量"}),
                "resize": ("BOOLEAN", {"default": False, "label_on": "启用", "label_off": "禁用"}),
                "target_width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "target_height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("图片批量数据", "图片路径列表",)
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "load_images"
    CATEGORY = "luy/图片处理"

    def load_images(self, image_folder, max_images, resize, target_width, target_height):
        if not os.path.exists(image_folder):
            raise FileNotFoundError(f"文件夹不存在: {image_folder}")

        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        image_files = []
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(valid_extensions):
                image_files.append(os.path.join(image_folder, filename))

        image_files = image_files[:max_images]
        if not image_files:
            raise ValueError(f"在文件夹 {image_folder} 中未找到任何图片文件")

        images = []
        image_paths = []
        for file_path in image_files:
            try:
                img = Image.open(file_path).convert("RGB")
                if resize:
                    transform = T.Resize((target_height, target_width), interpolation=T.InterpolationMode.LANCZOS)
                    img = transform(img)
                img_np = np.array(img).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np).unsqueeze(0)
                images.append(img_tensor)
                image_paths.append(file_path)
            except Exception as e:
                print(f"加载图片 {file_path} 时出错: {str(e)}")
                continue

        if not images:
            raise RuntimeError("没有成功加载任何图片")

        batch_tensor = torch.cat(images, dim=0)
        path_str = "\n".join(image_paths)
        return (batch_tensor, path_str,)


class ImagePathScanner(BaseNode):
    """图片路径扫描节点（修改：输出JSON序列化的路径列表）"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_folder": ("STRING", {
                    "default": "input/images",
                    "placeholder": "请输入图片文件夹的绝对/相对路径"
                }),
            }
        }

    # 修改：路径列表改为单个字符串（JSON格式），数量仍为单个INT
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("路径列表(JSON字符串)", "图片数量")
    OUTPUT_IS_LIST = (False, False)  # 关键：改为非列表输出
    FUNCTION = "scan_image_paths"
    CATEGORY = "luy/图片处理"
    DESCRIPTION = "扫描指定文件夹下的图片，返回JSON格式的路径列表字符串和图片数量"

    def scan_image_paths(self, image_folder):
        # 1. 基础校验（无修改）
        if not os.path.exists(image_folder):
            raise FileNotFoundError(f"指定的文件夹不存在：{image_folder}")
        if not os.path.isdir(image_folder):
            raise NotADirectoryError(f"指定的路径不是文件夹：{image_folder}")

        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        image_full_paths = []
        for filename in os.listdir(image_folder):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in valid_extensions:
                full_path = os.path.abspath(os.path.join(image_folder, filename))
                image_full_paths.append(full_path)

        if not image_full_paths:
            raise ValueError(f"在文件夹 {image_folder} 中未找到任何图片文件（支持格式：{', '.join(valid_extensions)}）")

        array_size = len(image_full_paths)

        # 2. 核心修改：将列表序列化为JSON字符串
        path_list_json = json.dumps(image_full_paths, ensure_ascii=False)

        # 3. 返回：JSON字符串 + 数量（均为单个值）
        return (path_list_json, array_size)

class SingleImageLoader(BaseNode):
    """单张图片加载节点（保留原有逻辑，无修改）"""
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING", {
                    "default": "input/images/test.jpg",
                    "placeholder": "输入单张图片的完整路径/相对路径"
                }),
                "resize": ("BOOLEAN", {"default": False, "label_on": "启用", "label_off": "禁用"}),
                "target_width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
                "target_height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 64}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("图片数据",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "load_single_image"
    CATEGORY = "luy/图片处理"
    DESCRIPTION = "输入单张图片路径，加载并返回图片张量（支持缩放）"

    def load_single_image(self, image_path, resize, target_width, target_height):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        if not os.path.isfile(image_path):
            raise ValueError(f"指定的路径不是文件: {image_path}")

        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in valid_extensions:
            raise ValueError(f"不支持的图片格式: {file_ext}，支持格式：{valid_extensions}")

        try:
            img = Image.open(image_path).convert("RGB")
            if resize:
                transform = T.Resize((target_height, target_width), interpolation=T.InterpolationMode.LANCZOS)
                img = transform(img)
            img_np = np.array(img).astype(np.float32) / 255.0
            img_tensor = torch.from_numpy(img_np).unsqueeze(0)
            return (img_tensor,)
        except Exception as e:
            raise RuntimeError(f"加载图片失败: {str(e)}") from e

class StringArrayIndexer(BaseNode):
    """字符串数组索引取值节点（修改：解析JSON字符串为列表）"""
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 修改：输入为JSON格式的路径列表字符串（非列表）
                "path_list_json": ("STRING", {
                    "default": "",
                    "placeholder": "传入JSON格式的路径列表字符串"
                }),
                "index": ("INT", {
                    "default": 0,
                    "min": -99999,
                    "max": 99999,
                    "step": 1,
                    "placeholder": "数组索引（0开始，-1为最后一个）"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("索引对应值",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "get_array_element"
    CATEGORY = "luy/字符处理"
    DESCRIPTION = "解析JSON格式的路径列表字符串，根据索引返回对应路径"

    def get_array_element(self, path_list_json, index):
        """核心逻辑：反序列化JSON字符串为列表，再按索引取值"""
        # 1. 校验输入非空
        if not path_list_json:
            raise ValueError("输入的JSON字符串为空，请传入有效的路径列表JSON")

        # 2. 反序列化JSON字符串为列表
        try:
            string_array = json.loads(path_list_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON字符串解析失败！请确保输入是合法的JSON格式。错误：{str(e)}")

        # 3. 校验反序列化后是列表且元素为字符串
        if not isinstance(string_array, list):
            raise TypeError(f"JSON解析结果不是列表！当前类型：{type(string_array)}")
        for idx, elem in enumerate(string_array):
            if not isinstance(elem, str):
                raise TypeError(f"列表第{idx}个元素不是字符串！类型：{type(elem)}，值：{elem}")

        # 4. 校验列表非空
        if len(string_array) == 0:
            raise ValueError("解析后的路径列表为空，无法取值")

        # 5. 处理索引边界
        array_length = len(string_array)
        corrected_index = index % array_length

        # 6. 返回索引对应的值
        result = string_array[corrected_index]
        return (result,)