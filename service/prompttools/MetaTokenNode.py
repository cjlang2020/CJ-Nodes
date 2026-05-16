import random
import os
import re
import time

NODE_INPUT_CACHE = {
    "last_path": "",
    "input_spec": {}
}


class MetaTokenNode:
    def __init__(self):
        random.seed(time.time() + os.getpid())

    @classmethod
    def _get_options_folder(cls, custom_path):
        if not os.path.isabs(custom_path):
            return os.path.join(os.path.dirname(__file__), custom_path)
        return custom_path

    @classmethod
    def _scan_options_files(cls, custom_path):
        options_folder = cls._get_options_folder(custom_path)
        if not os.path.exists(options_folder):
            os.makedirs(options_folder)
            print(f"提示：自定义路径 {options_folder} 不存在，已自动创建")
            return []

        numbered_files = []
        for filename in os.listdir(options_folder):
            if filename.endswith(".txt"):
                match = re.match(r'^(\d+)-', filename)
                if match:
                    file_number = int(match.group(1))
                    param_name = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
                    numbered_files.append((file_number, param_name, filename))
                else:
                    numbered_files.append((9999, os.path.splitext(filename)[0], filename))

        numbered_files.sort(key=lambda x: x[0])
        return numbered_files

    @classmethod
    def _load_options(cls, custom_path, filename):
        options_folder = cls._get_options_folder(custom_path)
        options = ["忽略 (Ignore)", "随机 (Random)"]
        try:
            file_path = os.path.join(options_folder, filename)
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        options.append(stripped_line)
        except FileNotFoundError:
            print(f"警告：{options_folder} 路径下未找到文件 {filename}")
        return options

    @classmethod
    def _generate_input_spec(cls, custom_path):
        required_inputs = {
            "自定义文件路径": ("STRING", {
                "default": custom_path,
                "placeholder": "输入txt文件存放路径，支持相对/绝对路径",
                "tooltip": "例如：prompt_meta_token 或 D:/prompt_files，修改后请刷新节点"
            }),
            "启用选择节点": ("BOOLEAN", {"default": True}),
            "随机数量": ("INT", {"default": 1, "min": 1, "max": 10, "tooltip": "随机时选取的token数量"}),
        }

        sorted_files = cls._scan_options_files(custom_path)
        for _, param_name, filename in sorted_files:
            options = cls._load_options(custom_path, filename)
            required_inputs[param_name] = (options,)

        return {
            "required": required_inputs,
            "optional": {
                "txt_str": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入自定义提示词...会串接到前面",
                    "rows": 5
                }),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True, "tooltip": "随机种子"}),
            }
        }

    @classmethod
    def INPUT_TYPES(cls):
        default_path = "prompt_meta_token"
        NODE_INPUT_CACHE["last_path"] = default_path
        NODE_INPUT_CACHE["input_spec"] = cls._generate_input_spec(default_path)
        return NODE_INPUT_CACHE["input_spec"]

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        current_path = kwargs.get("自定义文件路径", "prompt_meta_token")
        if current_path == NODE_INPUT_CACHE["last_path"]:
            return True

        print(f"检测到路径变更：{NODE_INPUT_CACHE['last_path']} → {current_path}，刷新下拉框...")
        new_input_spec = cls._generate_input_spec(current_path)
        NODE_INPUT_CACHE["last_path"] = current_path
        NODE_INPUT_CACHE["input_spec"] = new_input_spec
        cls.INPUT_TYPES = lambda: new_input_spec
        return True

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("提示词", "选择摘要", "随机token列表")
    FUNCTION = "generate_text"
    CATEGORY = "luy/提示词"

    def random_choice(self, custom_path, selected_option, filename, random_count=1):
        if selected_option != "随机 (Random)":
            return [selected_option]

        options = self._load_options(custom_path, filename)
        actual_options = [opt for opt in options if "随机" not in opt and "忽略" not in opt]
        if not actual_options:
            return []

        random.seed(time.time() * 1000000 + os.getpid() + random.randint(0, 1000000))
        count = min(random_count, len(actual_options))
        return random.sample(actual_options, count)

    def generate_text(self, 自定义文件路径, 启用选择节点, 随机数量, txt_str="", **kwargs):
        sorted_files = self._scan_options_files(自定义文件路径)
        fields_with_filename = [(param_name, filename) for _, param_name, filename in sorted_files]

        if not 启用选择节点:
            clean_txt = txt_str.strip()
            return (clean_txt, "", "")

        selected_tokens = []
        summary_parts = []
        random_token_list = []

        for param_name, filename in fields_with_filename:
            selected_option = kwargs.get(param_name, "忽略 (Ignore)")
            chosen = self.random_choice(自定义文件路径, selected_option, filename, 随机数量)

            pure_name = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
            for token in chosen:
                if "忽略" in token:
                    continue
                selected_tokens.append(token)
                summary_parts.append(f"{pure_name}：{token}")
                if selected_option == "随机 (Random)":
                    random_token_list.append(token)

        txt_str_clean = txt_str.strip().rstrip(",").lstrip(",")
        if selected_tokens:
            tokens_str = ",".join(selected_tokens)
            result = f"{txt_str_clean},{tokens_str}" if txt_str_clean else tokens_str
        else:
            result = txt_str_clean

        summary_result = "、".join(summary_parts)
        random_result = ",".join(random_token_list)

        return (result, summary_result, random_result)
