import os
import io
import json
import torch
import zipfile
import numpy as np
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo

import folder_paths
from .utils import cqdm

class ImageBatchtoImageList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_batch": ("image_batch", ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "convert"
    CATEGORY = "luy"

    def convert(self, image_batch):
        image_list = []
        for img in image_batch:
            img_final_np = np.array(img).astype(np.float32) / 255.0
            image_list.append(torch.from_numpy(img_final_np)[None, ])
        return (image_list,)

class ImageBatchtoImages:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_batch": ("image_batch", ),
                "width": ("INT", {"default": 512}),
                "height": ("INT", {"default": 512}),
                "interpolation": (["nearest", "bilinear", "bicubic", "lanczos"],),
                "mothed": (["crop (center)", "resize (stretch)", "pad (fill)", "pad (edge)"],),
                "transparency": ("BOOLEAN", {"default": False},),
                "fill_color": ("COLORCODE", {"default": "#000000"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "convert"
    CATEGORY = "luy"

    def convert(self, image_batch, width, height, interpolation, mothed, transparency, fill_color):
        image_list = []
        mask_list = []

        interpolation_map = {
            "nearest": Image.NEAREST,
            "bilinear": Image.BILINEAR,
            "bicubic": Image.BICUBIC,
            "lanczos": Image.LANCZOS
        }

        try:
            _interpolation = interpolation_map[interpolation]
        except:
            _interpolation = Image.LANCZOS

        for _img in image_batch:
            hex_color = fill_color.lstrip("#")
            alpha = 0 if transparency else 255
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

            img = _img.copy().convert('RGBA') if transparency else _img.copy().convert('RGB')
            processed_img = img

            if img.size != (width, height):
                if mothed == "resize (stretch)":
                    processed_img = img.resize((width, height), _interpolation)
                elif mothed == "crop (center)":
                    processed_img = ImageOps.fit(img, (width, height), method=_interpolation, centering=(0.5, 0.5))
                elif mothed == "pad (fill)":
                    processed_img = ImageOps.pad(img, (width, height), method=_interpolation, color=(r, g, b, alpha), centering=(0.5, 0.5))
                elif mothed == "pad (edge)":
                    ratio = min(width / img.width, height / img.height)
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    resized_img = img.resize(new_size, _interpolation)

                    delta_w = width - new_size[0]
                    delta_h = height - new_size[1]
                    padding = (delta_h // 2, delta_h - (delta_h // 2), delta_w // 2, delta_w - (delta_w // 2))
                    img_np = np.array(resized_img)

                    if len(img_np.shape) == 3:
                        pad_width = ((padding[0], padding[1]), (padding[2], padding[3]), (0, 0))
                    else:
                        pad_width = ((padding[0], padding[1]), (padding[2], padding[3]))

                    padded_np = np.pad(img_np, pad_width, mode='edge')
                    processed_img = Image.fromarray(padded_np)

            img_final_np = np.array(processed_img).astype(np.float32) / 255.0
            image_list.append(torch.from_numpy(img_final_np)[None, ])
            #mask_list.append(mask_tensor[None, ])

        output_images = torch.cat(image_list, dim=0)
        #output_masks = torch.cat(mask_list, dim=0)
        return (output_images,)

class LoadImageBatch:
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
    CATEGORY = "lhyNodes/Image"

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

class SaveImageAsZip:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "save_metadata": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "text": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_zip"
    OUTPUT_NODE = True
    CATEGORY = "lhyNodes/File"

    def save_zip(self, image, filename_prefix, save_metadata, text=None, prompt=None, extra_pnginfo=None):
        if text is not None:
            if isinstance(text, str):
                text = [text]
            elif isinstance(text, list) and all(isinstance(i, str) for i in text):
                pass
            else:
                raise ValueError(f"Unknown input format! The input must be a String or [String].")

            if len(image) != len(text):
                raise ValueError(f"Images and Text must have the same length!")

        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, image[0].shape[1], image[0].shape[0])

        zip_filename = f"{filename}_{counter:05}_.zip"
        zip_path = os.path.join(full_output_folder, zip_filename)

        print(f"Saving Zip to: {zip_path}")
        compression = zipfile.ZIP_DEFLATED if 'zlib' in zipfile.sys.modules else zipfile.ZIP_STORED

        with zipfile.ZipFile(zip_path, 'w', compression=compression) as zf:
            for i, _image in enumerate(cqdm(image)):
                i_np = 255. * _image.cpu().numpy()
                img = Image.fromarray(np.clip(i_np, 0, 255).astype(np.uint8))
                img_byte_arr = io.BytesIO()

                metadata = None
                if save_metadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))

                img.save(img_byte_arr, pnginfo=metadata, format='PNG', compress_level=self.compress_level)
                zf.writestr(f"{i:05}.png", img_byte_arr.getvalue())
                if text is not None:
                    zf.writestr(f"{i:05}.txt", str(text[i]))

        return {
            "ui": {
                "zip_filename": [zip_filename],
                "subfolder": [subfolder],
                "type": [self.type]
            }
        }

class SaveTextAsZip:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_zip"
    OUTPUT_NODE = True
    CATEGORY = "lhyNodes/File"

    def save_zip(self, text, filename_prefix):
        if isinstance(text, str):
            text = [text]
        elif isinstance(text, list) and all(isinstance(i, str) for i in text):
            pass
        else:
            raise ValueError(f"Unknown input format! The input must be a String or [String].")

        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, 100, 100)

        zip_filename = f"{filename}_{counter:05}_.zip"
        zip_path = os.path.join(full_output_folder, zip_filename)

        print(f"Saving Zip to: {zip_path}")
        compression = zipfile.ZIP_DEFLATED if 'zlib' in zipfile.sys.modules else zipfile.ZIP_STORED

        with zipfile.ZipFile(zip_path, 'w', compression=compression) as zf:
            for i, txt in enumerate(cqdm(text)):
                zf.writestr(f"{i:05}.txt", str(txt))

        return {
            "ui": {
                "zip_filename": [zip_filename],
                "subfolder": [subfolder],
                "type": [self.type]
            }
        }

class LoadZipBatch:
    def __init__(self):
        self.zip_dir = os.path.join(folder_paths.get_input_directory(), "zip")
        if not os.path.exists(self.zip_dir):
            os.makedirs(self.zip_dir, exist_ok=True)

    @classmethod
    def INPUT_TYPES(s):
        zip_dir = os.path.join(folder_paths.get_input_directory(), "zip")
        files = []
        if os.path.exists(zip_dir):
            files = [f for f in os.listdir(zip_dir) if f.lower().endswith(".zip")]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(zip_dir, x)), reverse=True)

        if not files:
            files = ["None"]

        return {
            "required": {
                "filename": (files, ),
            },
        }

    RETURN_TYPES = ("image_batch", "INT")
    RETURN_NAMES = ("image_batch", "count")
    FUNCTION = "load_zip"
    CATEGORY = "Custom/Image"

    def load_zip(self, filename):
        zip_path = os.path.join(self.zip_dir, filename)

        if not os.path.exists(zip_path) or filename == "None":
            raise ValueError(f"No batches found!")

        image_list = []

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for zinfo in zf.infolist():
                    if zinfo.flag_bits & 0x1:
                        raise ValueError(f"Error: The file '{filename}' is password protected. This node does not support encrypted ZIP files.")

                file_names = sorted(zf.namelist())

                for file_name in file_names:
                    if file_name.startswith(".") or file_name.startswith("__MACOSX") or "/." in file_name or file_name.endswith("/"):
                        continue

                    valid_ext = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
                    if not file_name.lower().endswith(valid_ext):
                        continue

                    try:
                        data = zf.read(file_name)
                        img = Image.open(io.BytesIO(data))
                        img = ImageOps.exif_transpose(img)
                        #img = img.convert("RGB")
                        image_list.append(img)

                    except Exception as e:
                        print(f"Warning: Failed to load image {file_name}: {e}")
                        continue

        except zipfile.BadZipFile:
             raise ValueError(f"Error: '{filename}' is not a valid ZIP file.")

        if not image_list:
            raise ValueError("No valid images found in the ZIP file.")

        return (image_list, len(image_list))

    @classmethod
    def VALIDATE_INPUTS(s, input_types):
        return True

NODE_CLASS_MAPPINGS = {
    "LoadImageBatch": LoadImageBatch,
    "SaveImageAsZip": SaveImageAsZip,
    "SaveTextAsZip": SaveTextAsZip,
    "LoadZipBatch": LoadZipBatch,
    "ImageBatchtoImages": ImageBatchtoImages,
    "ImageBatchtoImageList": ImageBatchtoImageList
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageBatch": "Load Image Batch",
    "SaveImageAsZip": "Save Image as Zip",
    "SaveTextAsZip": "Save Text as Zip",
    "LoadZipBatch": "Load Image from Zip",
    "ImageBatchtoImages": "Image Batch to Images",
    "ImageBatchtoImageList": "Image Batch to Image List"
}