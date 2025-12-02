import random
import os
import re

class PromptSelectorNode:
    def __init__(self):
        super().__init__()
        self.prompt = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "提示词": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入提示词...",
                    "rows": 5
                })
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出提示词",)
    FUNCTION = "process_prompt"
    CATEGORY = "luy"

    def process_prompt(self, 提示词):
        self.prompt = 提示词
        return (self.prompt,)


class PromptGenerator:
    def __init__(self):
        pass

    @classmethod
    def _get_options_folder(cls):
        """获取选项文件夹路径"""
        return os.path.join(os.path.dirname(__file__), "options")

    @classmethod
    def _scan_options_files(cls):
        """扫描选项文件夹中的所有txt文件，并按序号排序"""
        options_folder = cls._get_options_folder()
        if not os.path.exists(options_folder):
            os.makedirs(options_folder)
            return {}

        files_dict = {}
        numbered_files = []

        for filename in os.listdir(options_folder):
            if filename.endswith(".txt"):
                # 提取文件名中的序号
                match = re.match(r'^(\d+)-', filename)
                if match:
                    # 有序号的文件
                    file_number = int(match.group(1))
                    # 去掉序号和扩展名作为参数名
                    param_name = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
                    numbered_files.append((file_number, param_name, filename))
                else:
                    # 没有序号的文件，放在后面
                    param_name = os.path.splitext(filename)[0]
                    numbered_files.append((9999, param_name, filename))

        # 按序号排序
        numbered_files.sort(key=lambda x: x[0])

        # 构建排序后的字典
        for _, param_name, filename in numbered_files:
            files_dict[param_name] = filename

        return files_dict

    @classmethod
    def _load_options(cls, filename):
        """加载单个文件的选项"""
        options = ["忽略 (Ignore)"]
        options.append("随机 (Random)")
        try:
            file_path = os.path.join(cls._get_options_folder(), filename)
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        options.append(stripped_line)
        except FileNotFoundError:
            print(f"警告：未找到文件 {filename}")
        return options

    @classmethod
    def INPUT_TYPES(cls):
        """动态生成输入类型，基于文件夹中的文件，按序号排序"""
        required_inputs = {}

        # 扫描选项文件夹中的文件（已排序）
        files_dict = cls._scan_options_files()

        # 为每个文件创建一个输入参数（保持排序）
        for param_name, filename in files_dict.items():
            required_inputs[param_name] = (cls._load_options(filename),)

        # 添加可选参数
        return {
            "required": required_inputs,
            "optional": {
                "txt_str": ("STRING", {"default": " "}),  # lora关键词
            }
        }

    # 修改返回类型，增加下拉框选择内容的输出
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("中文标签", "英文标签", "中英混合标签", "包含主题内容")
    FUNCTION = "generate_text"
    CATEGORY = "luy"

    def random_choice(self, selected_option, options):
        if selected_option == "随机 (Random)":
            actual_options = [opt for opt in options if "随机" not in opt and "忽略" not in opt]
            return random.choice(actual_options) if actual_options else selected_option
        return selected_option

    def _extract_parts(self, text):
        """提取中文部分和英文部分"""
        if not text or "忽略" in text or "随机" in text:
            return "", ""

        if " (" in text and text.endswith(")"):
            parts = text.split(" (")
            chinese_part = parts[0].strip()
            english_part = parts[1][:-1].strip()  # 去掉最后的)
            return chinese_part, english_part
        else:
            # 格式不规范时，全部作为中文
            return text.strip(), ""

    def generate_text(self, txt_str,** kwargs):
        """动态处理所有参数"""
        # 获取所有必填字段（保持排序）
        input_types = self.INPUT_TYPES()
        fields = list(input_types['required'].keys())

        selections = {}
        for field in fields:
            value = kwargs.get(field, "忽略 (Ignore)")
            field_options = input_types['required'].get(field, (["忽略 (Ignore)"],))[0]
            selections[field] = self.random_choice(value, field_options)

        # 分别收集中文、英文、中英混合的关键词
        chinese_keywords = []
        english_keywords = []
        mix_keywords = []
        # 收集下拉框选择内容（只包含中文部分）
        dropdown_selections = []

        for field in fields:  # 按排序后的顺序处理
            value = selections[field]
            if "忽略" not in value:
                chinese_part, english_part = self._extract_parts(value)

                # 收集下拉框选择内容（格式：字段（中文值））
                if chinese_part:
                    dropdown_selections.append(f"{field}（{chinese_part}）")

                if chinese_part:
                    chinese_keywords.append(chinese_part)
                if english_part:
                    english_keywords.append(english_part)
                if chinese_part and english_part:
                    mix_keywords.append(f"{chinese_part} ({english_part})")
                elif chinese_part:
                    mix_keywords.append(chinese_part)
                elif english_part:
                    mix_keywords.append(english_part)

        # 处理基础提示词
        txt_str_clean = txt_str.strip().rstrip(",").lstrip(",")

        # 拼接结果
        def join_keywords(base, keywords):
            if not keywords:
                return base
            if not base:
                return ",".join(keywords)
            return f"{base},{','.join(keywords)}"

        chinese_result = join_keywords(txt_str_clean, chinese_keywords)
        english_result = join_keywords(txt_str_clean, english_keywords)
        mix_result = join_keywords(txt_str_clean, mix_keywords)

        # 拼接下拉框选择内容（用、分隔）
        dropdown_result = "、".join(dropdown_selections)

        return (chinese_result, english_result, mix_result, dropdown_result)