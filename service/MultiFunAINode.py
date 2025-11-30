import json
import os
import re
import folder_paths
import gc
import comfy.model_management as mm
from .qwen3vluntils import get_model, load_config, load_prompt_options

# 加载配置并初始化LLM路径
config_data = load_config()
llm_extensions = ['.gguf']
folder_paths.folder_names_and_paths["LLM"] = ([os.path.join(folder_paths.models_dir, "LLM")], llm_extensions)


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"prompts": {}, "models": {}}

config_data = load_config()
prompt_types = list(config_data["prompts"].keys())

class MultiFunAINode:
    def __init__(self):
        super().__init__()
        self.prompt = ""
        self.tokenizers = {}
        self.models = {}
        self.current_config = None  # 初始化配置跟踪

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (folder_paths.get_filename_list("LLM"), {"default": "Qwen3-4B-Instruct-2507-Q5_K_M.gguf"}),
                "keep_model_loaded": ("BOOLEAN", {"default": True}),
                "max_tokens": ("INT", {"default": 800, "min": 0, "max": 4096, "step": 1}),
                "choice_type": (prompt_types, {"default": prompt_types[0] if prompt_types else ""}),
                "prompt": ("STRING", {"multiline": True, "default": "",}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出提示词",)
    FUNCTION = "process_prompt"
    CATEGORY = "luy"

    def process_prompt(self, model, keep_model_loaded, max_tokens, choice_type, prompt, seed):
        mm.soft_empty_cache()

        # 1. 强化禁用think模式的配置（增加显式抑制参数）
        llmamodel_config = {
            "model": model,
            "model_type": "llama",
            "think_mode": False,
            "n_ctx": 8192,
            "n_gpu_layers": -1,
            "keep_model_loaded": keep_model_loaded,
            "enable_thinking": False,  # 新增：传递额外抑制参数
            "no_thinking": True      # 新增：兼容工具函数的其他禁用标识
        }

        adjusted_config = llmamodel_config.copy()
        adjusted_config["mmproj_model"] = adjusted_config.get("mmproj_model", None)

        parameters = {
            "max_tokens": max_tokens,
            "temperature": 0.7,  # 降低随机性，减少模型额外输出
            "stop": ["```"]       # 遇到think标签起始符立即停止生成
        }

        # 2. 重新初始化模型（确保配置生效）
        if not hasattr(self, "llm") or self.current_config != adjusted_config:
            if hasattr(self, "llm"):
                self.llm.close()
                try:
                    self.chat_handler._exit_stack.close()
                except Exception:
                    pass
            self.current_config = adjusted_config
            self.chat_handler, self.llm = get_model(adjusted_config)

        # 3. 净化提示词（移除可能触发think的内容）
        prompt_full = load_prompt_options(config_data["prompts"].get(choice_type, ""))
        # 过滤提示词中的思维链引导语句
        prompt_full = re.sub(r"思考|分析|推理|步骤|```[\s\S]*?```", "", prompt_full)
        # 强制添加禁用think的指令
        system_prompt = "直接输出结果，不要包含任何思考过程、注释或```think```标签。"
        final_prompt = f"{system_prompt}\n{prompt_full}{prompt}/no_think"

        messages = [{"role": "user", "content": final_prompt}]
        output = self.llm.create_chat_completion(
            messages=messages,
            seed=seed,** parameters
        )

        # 清理资源
        if not keep_model_loaded:
            self.llm.close()
            try:
                self.chat_handler._exit_stack.close()
            except Exception:
                pass
            del self.llm, self.chat_handler
            gc.collect()
            mm.soft_empty_cache()

        # 4. 强制过滤输出中的think内容
        text = output['choices'][0]['message']['content']
        # 移除所有```think```块及内容
        text = re.sub(r"```[\s\S]*?think[\s\S]*?```", "", text, flags=re.IGNORECASE)
        # 移除残留的标签碎片
        text = re.sub(r"```|think|\u200b", "", text)
        # 清理首尾空白和符号
        text = text.lstrip(": ").lstrip().rstrip()

        return (text,)