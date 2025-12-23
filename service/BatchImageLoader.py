import folder_paths
import torch
import os
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
    """
    批量图片加载节点，能够从指定文件夹读取所有图片
    支持常见图片格式（jpg, jpeg, png, bmp, gif）
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        """定义节点的输入参数"""
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
    CATEGORY = "luy"

    def load_images(self, image_folder, max_images, resize, target_width, target_height):
        """加载指定文件夹中的图片"""
        # 检查文件夹是否存在
        if not os.path.exists(image_folder):
            raise FileNotFoundError(f"文件夹不存在: {image_folder}")

        # 支持的图片扩展名
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

        # 获取文件夹中所有图片文件
        image_files = []
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(valid_extensions):
                image_files.append(os.path.join(image_folder, filename))

        # 限制最大加载数量
        image_files = image_files[:max_images]

        if not image_files:
            raise ValueError(f"在文件夹 {image_folder} 中未找到任何图片文件")

        # 加载并处理图片
        images = []
        image_paths = []

        for file_path in image_files:
            try:
                # 打开图片
                img = Image.open(file_path).convert("RGB")

                # 如果需要调整大小
                if resize:
                    # 使用高质量的缩放
                    transform = T.Resize((target_height, target_width), interpolation=T.InterpolationMode.LANCZOS)
                    img = transform(img)

                # 转换为张量
                img_np = np.array(img).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np).unsqueeze(0)
                images.append(img_tensor)

                # 保存图片路径
                image_paths.append(file_path)

            except Exception as e:
                print(f"加载图片 {file_path} 时出错: {str(e)}")
                continue

        if not images:
            raise RuntimeError("没有成功加载任何图片")

        # 合并所有图片张量
        batch_tensor = torch.cat(images, dim=0)

        # 生成图片路径字符串
        path_str = "\n".join(image_paths)

        return (batch_tensor, path_str,)
