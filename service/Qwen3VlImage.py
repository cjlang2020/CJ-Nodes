import os
import json
import torch
import numpy as np
from PIL import Image
import folder_paths
import comfy.model_management as mm
from .qwen3vluntils import get_model, image2base64, load_config, scale_image

config_data = load_config()
llm_extensions = ['.gguf']
folder_paths.folder_names_and_paths["LLM"] = ([os.path.join(folder_paths.models_dir, "LLM")], llm_extensions)


# ======================== 核心修复+优化区域 START ========================
# 1. 定义prompt文件目录（使用原始字符串避免转义，确认此路径是纯文件目录，不含文件内容！）
PROMPT_FILE_DIR = os.path.join(os.path.dirname(__file__), "ai_prompt/V")
# 初始化预设prompt字典
preset_prompts = {}

# 2. 过滤Windows非法文件名字符（防止文件命名错误导致路径异常）
INVALID_CHARS = r'\/:*?"<>|'
# 3. 定义需要排除的文件（隐藏文件、系统文件、临时文件）
EXCLUDE_FILES = ['.DS_Store', 'Thumbs.db', 'desktop.ini']

def is_valid_file(file_name):
    """校验是否为有效可读取的prompt文件"""
    if file_name in EXCLUDE_FILES:
        return False
    # 排除隐藏文件（开头带.或~）
    if file_name.startswith(('.', '~')):
        return False
    return True

# 读取指定目录下的所有有效文件，生成 preset_prompts：文件名=key，文件内容=value
if os.path.exists(PROMPT_FILE_DIR) and os.path.isdir(PROMPT_FILE_DIR):
    # 遍历目录下所有项，严格区分【文件】和【文件夹】
    for file_item in os.listdir(PROMPT_FILE_DIR):
        # 拼接完整路径（仅用文件名拼接，避免内容混入）
        file_abspath = os.path.join(PROMPT_FILE_DIR, file_item)
        # 只处理【文件】，跳过文件夹/快捷方式等
        if os.path.isfile(file_abspath) and is_valid_file(file_item):
            try:
                # 读取文件内容，utf-8编码+忽略编码错误，自动去除首尾空白符
                with open(file_abspath, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read().strip()
                # 核心赋值：纯文件名作为key，文件内容作为value
                preset_prompts[file_item] = file_content
                print(f"成功加载prompt文件：{file_item}")
            except Exception as e:
                # 容错：单个文件读取失败不影响整体，打印详细日志
                print(f"【警告】读取prompt文件失败 {file_abspath} ，错误原因：{str(e)[:100]}")
else:
    print(f"【警告】prompt目录不存在或不是有效目录：{PROMPT_FILE_DIR}，请检查路径！")

# 生成下拉选单的标签列表（为空时给默认值，避免节点报错）
preset_tags = list(preset_prompts.keys()) if preset_prompts else ["请在V目录下放prompt文件"]
# ======================== 核心修复+优化区域 END ========================

class ImageDeal:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": (folder_paths.get_filename_list("LLM"), {"default": "Qwen3-VL-4B-Instruct-Q5_K_M.gguf"}),
                "mmproj_model": (["None"] + folder_paths.get_filename_list("LLM"), {"default": "mmproj-BF16.gguf"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 800, "min": 0, "max": 4096, "step": 1}),
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
    CATEGORY = "luy/AI"

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
                preset_text = preset_prompts[preset_prompt]
                preset_text = preset_text.replace('{', '{{').replace('}', '}}').replace('{{}}', '{}')
                final_text = preset_text.format(custom_prompt)
                user_content.append({"type": "text", "text": final_text})
            else:
                user_content.append({"type": "text", "text": custom_prompt})
        else:
            if preset_prompt in preset_prompts and preset_prompt != "请在V目录下放prompt文件":
                # 保留原逻辑：自动替换preset_text里的@字符为 video/image
                preset_text = preset_prompts[preset_prompt]
                preset_text = preset_text.replace("@", "video" if video_input else "image")
                user_content.append({"type": "text", "text": preset_text})
            else:
                user_content.append({"type": "text", "text": ""})

        if images is not None:
            if not hasattr(self.chat_handler, "clip_model_path"):
                 raise ValueError("未配置视觉模块（mmproj），请加载对应的mmproj_model文件！")

            frames = images
            if video_input:
                indices = np.linspace(0, len(images) - 1, max_frames, dtype=int)
                frames = [images[i] for i in indices]

            for image in frames:
                try:
                    data = image2base64(scale_image(image, video_size)) if video_input else image2base64(np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
                    user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}})
                except Exception as e:
                    print(f"【警告】图片转base64失败，错误原因：{str(e)[:50]}")
                    continue

        messages.append({"role": "user", "content": user_content})

        # 推理与裁剪处理
        try:
            output = self.llm.create_chat_completion(messages=messages, seed=seed, max_tokens=max_tokens)
            text = output['choices'][0]['message']['content']
        except Exception as e:
            text = f"推理失败，错误原因：{str(e)[:200]}"
            print(f"【错误】LLM推理失败：{str(e)}")

        return (text,)