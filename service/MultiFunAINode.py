import json
import os
import re
import folder_paths
import gc
import comfy.model_management as mm
from .qwen3vluntils import get_model, load_config

# 加载配置并初始化LLM路径
config_data = load_config()
llm_extensions = ['.gguf']
folder_paths.folder_names_and_paths["LLM"] = ([os.path.join(folder_paths.models_dir, "LLM")], llm_extensions)

# ======================== 核心改造区域 START ========================
# 定义固定读取目录（你指定的 T 目录，原始字符串防止转义报错）
PROMPT_FILE_DIR =  os.path.join(os.path.dirname(__file__), "ai_prompt/T")
# 初始化预设prompt字典 文件名=key，文件内容=value
prompt_types_dict = {}

# 过滤Windows非法文件名字符+系统无效文件
INVALID_CHARS = r'\/:*?"<>|'
EXCLUDE_FILES = ['.DS_Store', 'Thumbs.db', 'desktop.ini']

def is_valid_file(file_name):
    """校验是否为有效可读取的prompt文件"""
    if file_name in EXCLUDE_FILES:
        return False
    # 排除隐藏文件/临时文件
    if file_name.startswith(('.', '~')):
        return False
    return True

# 读取指定目录下的所有有效文件，生成字典
if os.path.exists(PROMPT_FILE_DIR) and os.path.isdir(PROMPT_FILE_DIR):
    for file_item in os.listdir(PROMPT_FILE_DIR):
        file_abspath = os.path.join(PROMPT_FILE_DIR, file_item)
        # 严格只处理【文件】，跳过文件夹/快捷方式，且过滤无效文件
        if os.path.isfile(file_abspath) and is_valid_file(file_item):
            try:
                # 读取文件内容，utf8编码+容错，自动去除首尾空白符
                with open(file_abspath, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read().strip()
                # 核心赋值：文件名 = key ， 文件内容 = value
                prompt_types_dict[file_item] = file_content
                print(f"✅ 成功加载T目录prompt文件：{file_item}")
            except Exception as e:
                print(f"⚠️ 读取T目录prompt文件失败 {file_abspath} : {str(e)[:80]}")
else:
    print(f"⚠️ prompt目录不存在或非法：{PROMPT_FILE_DIR}，请检查路径！")

# 生成下拉选单的标签列表，为空时给默认值防止节点报错
prompt_types = list(prompt_types_dict.keys()) if prompt_types_dict else ["请在T目录放入提示词文件"]
# ======================== 核心改造区域 END ========================

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
                "max_tokens": ("INT", {"default": 1200, "min": 0, "max": 4096, "step": 1}),
                "choice_type": (prompt_types, {"default": prompt_types[0] if prompt_types else ""}),
                "prompt": ("STRING", {"multiline": True, "default": "",}),
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

        # 3. 净化提示词（移除可能触发think的内容）【核心修改：读取T目录的文件内容】
        # 替换原从config读取，改为从我们加载的文件字典读取
        prompt_full = prompt_types_dict.get(choice_type, "")
        # 过滤提示词中的思维链引导语句
        prompt_full = re.sub(r"思考|分析|推理|步骤|```[\s\S]*?```", "", prompt_full)
        # 强制添加禁用think的指令
        system_prompt = "直接输出结果，不要包含任何思考过程、注释或```think```标签。"
        final_prompt = f"{system_prompt}\n{prompt_full}{prompt}/no_think"

        messages = [{"role": "user", "content": final_prompt}]

        # 增加推理异常捕获，防止节点崩溃
        try:
            output = self.llm.create_chat_completion(
                messages=messages,
                seed=seed,** parameters
            )
        except Exception as e:
            text = f"模型推理失败：{str(e)[:150]}"
            print(f"❌ LLM推理错误: {str(e)}")
            return (text,)

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