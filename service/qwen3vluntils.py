import os
import io
import json
import base64
import torch
import numpy as np
from PIL import Image
import folder_paths
from llama_cpp import Llama
from llama_cpp.llama_chat_format import (Qwen3VLChatHandler)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"prompts": {}, "models": {}}

def image2base64(image):
    img = Image.fromarray(image)
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_base64

def load_prompt_options(filename):
    txt_str=""
    try:
        with open(os.path.join(os.path.dirname(__file__), "prompt_options", filename), encoding="utf-8") as f:
            txt_str=f.read()
    except FileNotFoundError:
        pass
    return txt_str

def scale_image(image: torch.Tensor, max_size: int = 128):
    resized_frames = []
    img_np = np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)
    img_pil = Image.fromarray(img_np)

    w, h = img_pil.size
    scale = min(max_size / max(w, h), 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    img_resized = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return np.array(img_resized)

def get_chat_handler(model_type):
    match model_type:
        case "Qwen3-VL":
            return Qwen3VLChatHandler
        case "None":
            return None
        case _:
            raise ValueError(f'Unknow model type: "{model_type}"')

def get_model(config):
    model = config["model"]
    mmproj_model = config["mmproj_model"]
    model_type = config.get("model_type", "Qwen3-VL")
    think_mode = config.get("think_mode", False)
    n_ctx = config.get("n_ctx", 8192)
    n_gpu_layers = config.get("n_gpu_layers", -1)

    model_path = os.path.join(folder_paths.models_dir, 'LLM', model)
    chat_handler = None
    if mmproj_model and mmproj_model != "None":
        mmproj_path = os.path.join(folder_paths.models_dir, 'LLM', mmproj_model)
        if model_type == "None":
            raise ValueError('"model_type" cannot be None!')
        print(f"Loading mmproj from {mmproj_path}")
        handler = get_chat_handler(model_type)
        if model_type == "Qwen3-VL":
            chat_handler = handler(clip_model_path=mmproj_path, use_think_prompt=think_mode, verbose=False)
        else:
            chat_handler = handler(clip_model_path=mmproj_path, verbose=False)
    print(f"Loading model from {model_path}")
    # 使用默认参数，只调整必要的
    llm = Llama(
        model_path,
        chat_handler=chat_handler,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        verbose=False,
        # 其他参数使用默认值
        top_k=30,
        top_p=0.9,
        min_p=0.05,
        typical_p=1.0,
        temperature=0.8,
        repeat_penalty=1.0,
        frequency_penalty=0.0,
        presence_penalty=1.0,
        mirostat_mode=0,
        mirostat_eta=0.1,
        mirostat_tau=5.0
    )
    return (chat_handler, llm)
