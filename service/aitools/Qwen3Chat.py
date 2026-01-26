import os
import gc
import folder_paths
import comfy.model_management as mm
from PIL import Image
import folder_paths
import json
from llama_cpp import Llama
from llama_cpp.llama_chat_format import (Qwen3VLChatHandler)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"prompts": {}, "models": {}}

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


config_data = load_config()
llm_extensions = ['.gguf']
folder_paths.folder_names_and_paths["LLM"] = ([os.path.join(folder_paths.models_dir, "LLM")], llm_extensions)

class Qwen3Deal:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 完全移除 mmproj_model 输入参数
                "model": (folder_paths.get_filename_list("LLM"), {"default": "Qwen3-4B-Instruct-2507-Q5_K_M.gguf"}),
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