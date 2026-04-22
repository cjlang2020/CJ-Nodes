"""
多功能AI节点 - 统一的文本处理节点
使用共享基础模块重构
"""
import folder_paths
import comfy.model_management as mm
from aitools_base import (
    BaseModelManager,
    PromptManager,
    clean_think_content,
    clean_prompt_keywords,
    register_llm_folder
)


# 确保LLM目录已注册
register_llm_folder()

# 初始化提示词管理器（T目录用于文本提示词）
prompt_manager = PromptManager("T")


class MultiFunAINode(BaseModelManager):
    """多功能AI处理节点"""

    @classmethod
    def INPUT_TYPES(cls):
        prompt_types = prompt_manager.get_prompt_types()
        return {
            "required": {
                "model": (folder_paths.get_filename_list("LLM"),
                          {"default": "Qwen3-4B-Instruct-2507-Q5_K_M.gguf"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 1200, "min": 0, "max": 4096, "step": 1}),
                "choice_type": (prompt_types, {"default": prompt_types[0]}),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出提示词",)
    FUNCTION = "process_prompt"
    CATEGORY = "luy/AI"

    def process_prompt(self, model, keep_model_loaded, max_tokens, choice_type, prompt, seed):
        mm.soft_empty_cache()

        # 模型配置
        model_config = {
            "model": model,
            "model_type": "None",  # 纯文本模型
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
            "stop": ["```"]
        }

        # 加载模型
        llm, _ = self.get_or_reload_model(model_config)

        # 构建提示词
        prompt_content = prompt_manager.get_prompt_content(choice_type)
        prompt_content = clean_prompt_keywords(prompt_content)

        system_prompt = "直接输出结果，不要包含任何思考过程、注释或```think```标签。"
        final_prompt = f"{system_prompt}\n{prompt_content}{prompt}/no_think"

        messages = [{"role": "user", "content": final_prompt}]

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

        # 清理资源
        if not keep_model_loaded:
            self.cleanup()

        # 处理输出
        text = output['choices'][0]['message']['content']
        text = clean_think_content(text)

        return (text,)