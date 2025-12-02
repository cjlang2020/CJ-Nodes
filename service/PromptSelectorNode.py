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
        """扫描选项文件夹中的所有txt文件，并按文件名的数字序号从小到大排序"""
        options_folder = cls._get_options_folder()
        if not os.path.exists(options_folder):
            os.makedirs(options_folder)
            return []  # 改为返回列表，保留排序顺序

        numbered_files = []
        for filename in os.listdir(options_folder):
            if filename.endswith(".txt"):
                # 提取文件名开头的数字序号（适配“1-适用场景.txt”格式）
                match = re.match(r'^(\d+)-', filename)
                if match:
                    file_number = int(match.group(1))
                    # 提取参数名（去掉序号和后缀）
                    param_name = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
                    numbered_files.append((file_number, param_name, filename))
                else:
                    # 无序号文件排最后
                    numbered_files.append((9999, os.path.splitext(filename)[0], filename))

        # 严格按数字序号升序排序
        numbered_files.sort(key=lambda x: x[0])
        return numbered_files  # 返回排序后的列表（包含序号、参数名、文件名）

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
        """动态生成输入类型，严格按文件名序号排序"""
        required_inputs = {}
        # 获取排序后的文件列表
        sorted_files = cls._scan_options_files()
        # 按排序顺序生成参数
        for _, param_name, filename in sorted_files:
            required_inputs[param_name] = (cls._load_options(filename),)

        # 添加布尔值参数
        required_inputs["启用选择节点"] = ("BOOLEAN", {"default": True})

        return {
            "required": required_inputs,
            "optional": {
                "txt_str": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入自定义提示词...会串接到前面",
                    "rows": 5
                }),  # lora关键词
            }
        }

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
            return text.strip(), ""

    def generate_text(self, txt_str, 启用选择节点=True,** kwargs):
        """动态处理所有参数（严格按序号顺序）"""
        # 获取排序后的字段列表
        sorted_files = self._scan_options_files()
        fields = [param_name for _, param_name, _ in sorted_files]

        # 如果未启用选择节点，直接返回txt_str内容
        if not 启用选择节点:
            return (txt_str.strip(), txt_str.strip(), txt_str.strip(), "")

        selections = {}
        for field in fields:
            value = kwargs.get(field, "忽略 (Ignore)")
            # 获取该字段对应的选项列表
            field_options = self.INPUT_TYPES()['required'][field][0]
            selections[field] = self.random_choice(value, field_options)

        # 按序号顺序收集中文、英文等关键词
        chinese_keywords = []
        english_keywords = []
        mix_keywords = []
        dropdown_selections = []

        for field in fields:
            value = selections[field]
            if "忽略" not in value:
                chinese_part, english_part = self._extract_parts(value)
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

        # 处理基础提示词并拼接结果
        txt_str_clean = txt_str.strip().rstrip(",").lstrip(",")
        def join_keywords(base, keywords):
            if not keywords:
                return base
            if not base:
                return ",".join(keywords)
            return f"{base},{','.join(keywords)}"

        chinese_result = join_keywords(txt_str_clean, chinese_keywords)
        english_result = join_keywords(txt_str_clean, english_keywords)
        mix_result = join_keywords(txt_str_clean, mix_keywords)
        dropdown_result = "、".join(dropdown_selections)

        return (chinese_result, english_result, mix_result, dropdown_result)