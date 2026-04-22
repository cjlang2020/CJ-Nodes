"""
Qwen3 纯文本聊天节点
使用共享基础模块重构
"""
from aitools_base import (
    BaseModelManager,
    load_config,
    register_llm_folder
)
import folder_paths
import comfy.model_management as mm


# 确保LLM目录已注册
register_llm_folder()

config_data = load_config()


class Qwen3Deal(BaseModelManager):
    """Qwen3纯文本处理节点"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": (folder_paths.get_filename_list("LLM"),
                         {"default": "Qwen3-4B-Instruct-2507-Q5_K_M.gguf"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 512, "min": 0, "max": 4096, "step": 1}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process"
    CATEGORY = "luy/AI"

    def process(self, model, keep_model_loaded, max_tokens, prompt, seed):
        mm.soft_empty_cache()

        # 模型配置
        model_config = {
            "model": model,
            "model_type": "None",  # 纯文本模型不需要chat handler
            "think_mode": False,
            "n_ctx": 8192,
            "n_gpu_layers": -1,
        }

        # 推理参数
        inference_params = {
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_k": 30,
            "top_p": 0.9,
            "min_p": 0.05,
            "repeat_penalty": 1.0,
        }

        # 加载模型
        llm, _ = self.get_or_reload_model(model_config)

        messages = [{"role": "user", "content": prompt}]

        # 推理
        try:
            output = llm.create_chat_completion(
                messages=messages,
                seed=seed,
                **inference_params
            )
        except Exception as e:
            error_msg = f"模型推理失败：{str(e)[:150]}"
            print(f"[错误] LLM推理失败: {str(e)}")
            return (error_msg,)

        # 清理资源（如果不保持加载）
        if not keep_model_loaded:
            self.cleanup()

        # 处理输出
        text = output['choices'][0]['message']['content']
        text = text.lstrip(": ").lstrip()

        return (text,)