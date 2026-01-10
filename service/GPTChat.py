import os
import gc
import folder_paths
import comfy.model_management as mm
from .qwen3vluntils import get_model, load_config

config_data = load_config()
llm_extensions = ['.gguf']
folder_paths.folder_names_and_paths["LLM"] = ([os.path.join(folder_paths.models_dir, "LLM")], llm_extensions)

class ChatDeal:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 完全移除 mmproj_model 输入参数
                "model": (folder_paths.get_filename_list("LLM"), {"default": "gtp-oss-20b-Q4.gguf"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 512, "min": 0, "max": 4096, "step": 1}),
                "prompt": ("STRING", {"multiline": True, "default": "",}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process"
    CATEGORY = "luy/AI"

    def process(self, model, keep_model_loaded, max_tokens, prompt, seed):
        mm.soft_empty_cache()

        # 模型配置中完全移除 mmproj_model 字段
        llmamodel_config = {
            "model": model,
            "model_type": "llama",  # 工具支持的模型类型
            "think_mode": False,    # 禁用think模式
            "n_ctx": 8192,
            "n_gpu_layers": -1,
            "keep_model_loaded": keep_model_loaded
        }

        # 处理 get_model 可能依赖 mmproj_model 的问题：
        # 若工具函数强制需要该参数，这里通过字典get方法设置默认值None
        # （兼容工具函数内部逻辑，避免KeyError）
        adjusted_config = llmamodel_config.copy()
        adjusted_config["mmproj_model"] = adjusted_config.get("mmproj_model", None)

        parameters = {"max_tokens": max_tokens}

        if not hasattr(self, "llm") or self.current_config != adjusted_config:
            if hasattr(self, "llm"):
                self.llm.close()
                try:
                    self.chat_handler._exit_stack.close()
                except Exception:
                    pass
            self.current_config = adjusted_config
            # 传入调整后的配置（包含默认None的mmproj_model，避免工具报错）
            self.chat_handler, self.llm = get_model(adjusted_config)

        messages = [{"role": "user", "content": prompt}]

        output = self.llm.create_chat_completion(
            messages=messages,
            seed=seed,** parameters
        )

        if not keep_model_loaded:
            self.llm.close()
            try:
                self.chat_handler._exit_stack.close()
            except Exception:
                pass
            del self.llm, self.chat_handler
            gc.collect()
            mm.soft_empty_cache()

        text = output['choices'][0]['message']['content']
        text = text.lstrip(": ").lstrip()

        return (text,)