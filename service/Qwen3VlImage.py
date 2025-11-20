import os
import json
import torch
import numpy as np
from PIL import Image
import folder_paths
import comfy.model_management as mm
from .qwen3vluntils import get_model, image2base64, load_config, load_prompt_options, scale_image

config_data = load_config()
llm_extensions = ['.gguf']
folder_paths.folder_names_and_paths["LLM"] = ([os.path.join(folder_paths.models_dir, "LLM")], llm_extensions)
preset_prompts = config_data.get("vl_prompts", {})
preset_tags = list(preset_prompts.keys())

class ImageDeal:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": (folder_paths.get_filename_list("LLM"), {"default": "Qwen3-VL-4B-Instruct-Q5_K_M.gguf"}),
                "mmproj_model": (["None"] + folder_paths.get_filename_list("LLM"), {"default": "mmproj-BF16.gguf"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 512, "min": 0, "max": 4096, "step": 1}),
                "preset_prompt": (preset_tags, {"default": preset_tags[0] if preset_tags else ""}),
                "custom_prompt": ("STRING", {"default": "", "multiline": True}),
                "system_prompt": ("STRING", {"multiline": True, "default": ""}),
                "video_input": ("BOOLEAN", {"default": False}),
                "max_frames": ("INT", {"default": 24, "min": 2, "max": 1024, "step": 1}),
                "video_size": ([128, 256, 512, 768, 1024], {"default": 256}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
            "optional": {
                "images": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("推理文本",)
    FUNCTION = "process"
    CATEGORY = "luy/ollama-cpp"

    def process(self, model, mmproj_model, keep_model_loaded, max_tokens,
                preset_prompt, custom_prompt, system_prompt, video_input,
                max_frames, video_size, seed, images=None):
        mm.soft_empty_cache()

        # 模型配置与加载
        llmamodel_config = {
            "model": model, "mmproj_model": mmproj_model, "model_type": "Qwen3-VL",
            "think_mode": False, "n_ctx": 8192, "n_gpu_layers": -1, "keep_model_loaded": keep_model_loaded
        }
        if not hasattr(self, "llm") or self.current_config != llmamodel_config:
            if hasattr(self, "llm"):
                self.llm.close()
                try: self.chat_handler._exit_stack.close()
                except Exception: pass
            self.current_config = llmamodel_config
            self.chat_handler, self.llm = get_model(llmamodel_config)

        # 构建消息
        messages = []
        system_prompts = "请将输入的图片序列当做视频而不是静态帧序列, " + system_prompt if video_input else system_prompt
        if system_prompts.strip():
            messages.append({"role": "system", "content": system_prompts})

        user_content = []
        if custom_prompt.strip():
            if preset_prompt.startswith('@') and preset_prompt in preset_prompts:
                preset_text = load_prompt_options(preset_prompts[preset_prompt])
                preset_text = preset_text.replace('{', '{{').replace('}', '}}').replace('{{}}', '{}')
                final_text = preset_text.format(custom_prompt)
                user_content.append({"type": "text", "text": final_text})
            else:
                user_content.append({"type": "text", "text": custom_prompt})
        else:
            if preset_prompt in preset_prompts:
                user_content.append({"type": "text", "text": load_prompt_options(preset_prompts[preset_prompt]).replace("@", "video" if video_input else "image")})
            else:
                user_content.append({"type": "text", "text": ""})

        if images is not None:
            if not hasattr(self.chat_handler, "clip_model_path"):
                 raise ValueError("未配置视觉模块（mmproj）")

            frames = images
            if video_input:
                indices = np.linspace(0, len(images) - 1, max_frames, dtype=int)
                frames = [images[i] for i in indices]

            for image in frames:
                data = image2base64(scale_image(image, video_size)) if video_input else image2base64(np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}})

        messages.append({"role": "user", "content": user_content})

        # 推理与裁剪处理
        output = self.llm.create_chat_completion(messages=messages, seed=seed, max_tokens=max_tokens)
        text = output['choices'][0]['message']['content']
        return (text,)