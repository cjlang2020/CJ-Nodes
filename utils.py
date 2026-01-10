import os
import math
import numpy as np
from PIL import Image, ImageOps

import comfy.utils
import folder_paths

class cqdm:
    def __init__(self, iterable=None, total=None, desc="Processing"):
        self.desc = desc
        self.pbar = None
        self.iterable = None
        self.total = total
        
        if iterable is not None:
            try:
                self.total = len(iterable)
                self.iterable = iter(iterable)
            except TypeError:
                if self.total is None:
                    raise ValueError("Total must be provided for iterables with no length.")
                    
        elif self.total is not None:
            pass
            
        else:
            raise ValueError("Either iterable or total must be provided.")
            
    def __iter__(self):
        if self.iterable is None:
            raise TypeError(f"'{type(self).__name__}' object is not iterable. Did you mean to use it with a 'with' statement?")
        if self.pbar is None:
            self.pbar = comfy.utils.ProgressBar(self.total)
        return self
    
    def __next__(self):
        if self.iterable is None:
            raise TypeError("Cannot call __next__ on a non-iterable cqdm object.")
        try:
            val = next(self.iterable)
            if self.pbar:
                self.pbar.update(1)
            return val
        except StopIteration:
            raise
            
    def __enter__(self):
        if self.pbar is None:
            self.pbar = comfy.utils.ProgressBar(self.total)
        return self.pbar
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def __len__(self):
        return self.total

def create_batch_preview(images, output_dir, file_name_prefix, max_size=2000):
    pil_images = []
    
    if isinstance(images, list):
        pil_images = images
    elif isinstance(images, Image.Image):
        pil_images = [images]
    else:
         return []

    if not pil_images:
        return []
    
    _max_size = 0xFFFFFF if len(pil_images) == 1 else max_size
    
    filename = f"{file_name_prefix}.webp"
    full_path = os.path.join(output_dir, filename)
    
    input_root = folder_paths.get_input_directory()
    try:
        subfolder = os.path.relpath(output_dir, input_root)
        if subfolder == ".": subfolder = ""
    except ValueError:
        subfolder = ""
        output_dir = folder_paths.get_temp_directory()
        full_path = os.path.join(output_dir, filename)

    if os.path.exists(full_path):
        return [{"filename": filename, "subfolder": subfolder, "type": "input"}]

    count = len(pil_images)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)

    if len(pil_images) > 0:
        ref_w, ref_h = pil_images[0].size
    else:
        ref_w, ref_h = 512, 512
    
    scale_w = _max_size / (cols * ref_w)
    scale_h = _max_size / (rows * ref_h)
    scale = min(1.0, scale_w, scale_h)

    thumb_w = max(1, int(ref_w * scale))
    thumb_h = max(1, int(ref_h * scale))

    canvas_w = cols * thumb_w
    canvas_h = rows * thumb_h
    canvas = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

    for idx, img in enumerate(pil_images):
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        img_thumb = ImageOps.pad(img, (thumb_w, thumb_h), method=Image.NEAREST, color=(0, 0, 0, 0), centering=(0.5, 0.5))
        
        c = idx % cols
        r = idx // cols
        x = c * thumb_w
        y = r * thumb_h
        
        canvas.paste(img_thumb, (x, y))

    canvas.save(full_path, format="WEBP", quality=80)

    return [{"filename": filename, "subfolder": subfolder, "type": "input"}]