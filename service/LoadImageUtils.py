from __future__ import annotations
import torch
import os
import hashlib
from PIL import Image, ImageOps, ImageSequence
import numpy as np
import folder_paths
import node_helpers
from PIL.PngImagePlugin import PngInfo

class LuyLoadImageBatch:
    def __init__(self):
        self.batch_dir = os.path.join(folder_paths.get_input_directory(), "batch")
        if not os.path.exists(self.batch_dir):
            os.makedirs(self.batch_dir, exist_ok=True)

    @classmethod
    def INPUT_TYPES(s):
        batch_dir = os.path.join(folder_paths.get_input_directory(), "batch")
        if not os.path.exists(batch_dir):
            os.makedirs(batch_dir, exist_ok=True)

        subdirs = [d for d in os.listdir(batch_dir) if os.path.isdir(os.path.join(batch_dir, d))]
        subdirs.sort(key=lambda x: os.path.getmtime(os.path.join(batch_dir, x)), reverse=True)

        if not subdirs:
            subdirs = ["None"]

        return {
            "required": {
                "batch": (subdirs, ),
            },
        }

    RETURN_TYPES = ("image_batch", "INT")
    RETURN_NAMES = ("image_batch", "count")
    FUNCTION = "process_batch"
    CATEGORY = "luy/图片处理"

    def process_batch(self, batch):
        target_dir = os.path.join(self.batch_dir, batch)

        if not os.path.exists(target_dir) or batch == "None":
            raise ValueError(f"No batches found!")

        valid_ext = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        files = sorted([f for f in os.listdir(target_dir)
            if os.path.splitext(f)[1].lower() in valid_ext
            and not f.startswith("__preview__")])

        if not files:
            raise ValueError("Empty batch folder")

        image_list = []

        for idx, filename in enumerate(files):
            img_path = os.path.join(target_dir, filename)
            img = Image.open(img_path)
            img = ImageOps.exif_transpose(img)
            #processed_img = img.convert("RGB")
            #img_np = np.array(processed_img).astype(np.float32) / 255.0
            #image_tensor = torch.from_numpy(img_np)[None, ]
            image_list.append(img)

        return (image_list, len(image_list))

class ShowCanvasImage:
    def __init__(self):
        self.batch_dir = os.path.join(folder_paths.get_input_directory(), "batch")
        if not os.path.exists(self.batch_dir):
            os.makedirs(self.batch_dir, exist_ok=True)

    @classmethod
    def INPUT_TYPES(s):
        batch_dir = os.path.join(folder_paths.get_input_directory(), "batch")
        if not os.path.exists(batch_dir):
            os.makedirs(batch_dir, exist_ok=True)

        subdirs = [d for d in os.listdir(batch_dir) if os.path.isdir(os.path.join(batch_dir, d))]
        subdirs.sort(key=lambda x: os.path.getmtime(os.path.join(batch_dir, x)), reverse=True)

        if not subdirs:
            subdirs = ["None"]

        # 获取图片文件列表用于单选
        image_files = ["None"]
        if subdirs and subdirs[0] != "None":
            target_dir = os.path.join(batch_dir, subdirs[0])
            if os.path.exists(target_dir):
                valid_ext = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
                files = sorted([f for f in os.listdir(target_dir)
                    if os.path.splitext(f)[1].lower() in valid_ext
                    and not f.startswith("__preview__")])
                if files:
                    image_files = files

        return {
            "required": {
                "batch": (subdirs, ),
                "image": (image_files, ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load_single_image"
    CATEGORY = "luy/图片处理"

    def load_single_image(self, batch, image):
        if batch == "None" or image == "None":
            raise ValueError("No batch or image selected!")

        target_dir = os.path.join(self.batch_dir, batch)
        img_path = os.path.join(target_dir, image)

        if not os.path.exists(img_path):
            raise ValueError(f"Image not found: {image}")

        img = Image.open(img_path)
        img = ImageOps.exif_transpose(img)

        # 处理单张图片
        i = ImageSequence.Iterator(img).__next__()
        i = ImageOps.exif_transpose(i)

        if i.mode == 'I':
            i = i.point(lambda i: i * (1 / 255))
        image_tensor = i.convert("RGB")

        image_tensor = np.array(image_tensor).astype(np.float32) / 255.0
        image_tensor = torch.from_numpy(image_tensor)[None,]

        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        elif i.mode == 'P' and 'transparency' in i.info:
            mask = np.array(i.convert('RGBA').getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")

        return (image_tensor, mask)

class LoadImageUtils:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {"required":
                    {
                        "image": (sorted(files), {"image_upload": True, "multiple": True}),
                        "folder": ("FOLDER", {"default": "./input", "allow_create_dir": True})
                    },
                }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    CATEGORY = "luy/图片处理"


    def load_image(self, image):
        # 处理多张图片上传的情况
        if isinstance(image, list):
            # 如果是图片列表，处理每张图片
            output_images = []
            output_masks = []

            for img_name in image:
                image_path = folder_paths.get_annotated_filepath(img_name)
                print(">>>>>>>当前加载图片路径:" + image_path)
                img = node_helpers.pillow(Image.open, image_path)

                # 处理单张图片（只取第一帧）
                i = ImageSequence.Iterator(img).__next__()
                i = node_helpers.pillow(ImageOps.exif_transpose, i)

                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image_tensor = i.convert("RGB")

                image_tensor = np.array(image_tensor).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image_tensor)[None,]

                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                elif i.mode == 'P' and 'transparency' in i.info:
                    mask = np.array(i.convert('RGBA').getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")

                output_images.append(image_tensor)
                output_masks.append(mask.unsqueeze(0))

            # 将所有图片拼接成一个批次
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)

        else:
            # 处理单张图片的情况
            image_path = folder_paths.get_annotated_filepath(image)
            print(">>>>>>>当前加载图片路径:" + image_path)
            img = node_helpers.pillow(Image.open, image_path)

            output_images = []
            output_masks = []
            w, h = None, None

            excluded_formats = ['MPO']

            for i in ImageSequence.Iterator(img):
                i = node_helpers.pillow(ImageOps.exif_transpose, i)

                if i.mode == 'I':
                    i = i.point(lambda i: i * (1 / 255))
                image_tensor = i.convert("RGB")

                if len(output_images) == 0:
                    w = image_tensor.size[0]
                    h = image_tensor.size[1]

                if image_tensor.size[0] != w or image_tensor.size[1] != h:
                    continue

                image_tensor = np.array(image_tensor).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image_tensor)[None,]
                if 'A' in i.getbands():
                    mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                elif i.mode == 'P' and 'transparency' in i.info:
                    mask = np.array(i.convert('RGBA').getchannel('A')).astype(np.float32) / 255.0
                    mask = 1. - torch.from_numpy(mask)
                else:
                    mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
                output_images.append(image_tensor)
                output_masks.append(mask.unsqueeze(0))

            if len(output_images) > 1 and img.format not in excluded_formats:
                output_image = torch.cat(output_images, dim=0)
                output_mask = torch.cat(output_masks, dim=0)
            else:
                output_image = output_images[0]
                output_mask = output_masks[0]

        return (output_image, output_mask)

    @classmethod
    def IS_CHANGED(s, image):
        image_path = folder_paths.get_annotated_filepath(image)
        print(">>>>>>>"+image_path)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image file: {}".format(image)

        return True




class FolderSelectNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                        "dirpath": ("STRING", {
                            "default": "",
                            "multiline": False,
                            "placeholder": "请右键打开文件夹..."
                })
            }
        }

    RETURN_TYPES = ("STRING",)  # 返回选中的文件夹路径
    RETURN_NAMES = ("folder_path",)
    FUNCTION = "select_folder"
    CATEGORY = "luy"

    def select_folder(self, dirpath):
        # 拼接完整路径（自定义文件夹列表的处理逻辑）
        return (dirpath,)