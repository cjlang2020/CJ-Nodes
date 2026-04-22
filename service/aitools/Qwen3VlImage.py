"""
Qwen3-VL 图像/视频处理节点
使用共享基础模块重构
"""
import numpy as np
import folder_paths
import comfy.model_management as mm
from aitools_base import (
    BaseModelManager,
    PromptManager,
    scale_image,
    image2base64,
    register_llm_folder,
    clean_think_content
)


# 确保LLM目录已注册
register_llm_folder()

# 初始化提示词管理器
PROMPT_FILE_DIR = "V"
prompt_manager = PromptManager(PROMPT_FILE_DIR)


class ImageDeal(BaseModelManager):
    """图像/视频处理节点"""

    @classmethod
    def INPUT_TYPES(s):
        preset_tags = prompt_manager.get_prompt_types()
        return {
            "required": {
                "model": (folder_paths.get_filename_list("LLM"),
                         {"default": "Qwen3-VL-4B-Instruct-Q5_K_M.gguf"}),
                "mmproj_model": (["None"] + folder_paths.get_filename_list("LLM"),
                                {"default": "mmproj-BF16.gguf"}),
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

        # 模型配置
        model_config = {
            "model": model,
            "mmproj_model": mmproj_model,
            "model_type": "Qwen3-VL",
            "think_mode": False,
            "n_ctx": 8192,
            "n_gpu_layers": -1,
        }

        # 加载模型
        llm, chat_handler = self.get_or_reload_model(model_config)

        # 构建消息
        messages = []
        system_prompts = ("请将输入的图片序列当做视频而不是静态帧序列, " + system_prompt
                         if video_input else system_prompt)
        if system_prompts.strip():
            messages.append({"role": "system", "content": system_prompts})

        # 构建用户内容
        user_content = prompt_manager.build_final_prompt(preset_prompt, custom_prompt, video_input)

        # 处理图像
        if images is not None:
            if not hasattr(chat_handler, "clip_model_path"):
                raise ValueError("未配置视觉模块（mmproj），请加载对应的mmproj_model文件！")

            frames = images
            if video_input:
                indices = np.linspace(0, len(images) - 1, max_frames, dtype=int)
                frames = [images[i] for i in indices]

            for image in frames:
                try:
                    if video_input:
                        data = image2base64(scale_image(image, video_size))
                    else:
                        img_array = np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)
                        data = image2base64(img_array)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{data}"}
                    })
                except Exception as e:
                    print(f"[警告] 图片转base64失败: {str(e)[:50]}")
                    continue

        messages.append({"role": "user", "content": user_content})

        # 推理参数
        inference_params = {
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_k": 30,
            "top_p": 0.9,
        }

        # 推理
        try:
            output = llm.create_chat_completion(
                messages=messages,
                seed=seed,
                **inference_params
            )
            text = output['choices'][0]['message']['content']
            text = clean_think_content(text)
        except Exception as e:
            text = f"推理失败，错误原因：{str(e)[:200]}"
            print(f"[错误] LLM推理失败：{str(e)}")

        # 清理资源
        if not keep_model_loaded:
            self.cleanup()

        return (text,)