import random
import os

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
    def _load_options(cls, filename):
        options = ["忽略 (Ignore)"]
        try:
            file_path = os.path.join(os.path.dirname(__file__), "options", filename)
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        options.append(stripped_line)
        except FileNotFoundError:
            print(f"警告：未找到文件 {filename}")
        options.append("随机 (Random)")
        return options

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "画质": (cls._load_options("画质.txt"),),
                "画风": (cls._load_options("画风.txt"),),
                "性别": (cls._load_options("性别.txt"),),
                "人物": (cls._load_options("人物.txt"),),
                "角色": (cls._load_options("角色.txt"),),
                "姿势": (cls._load_options("姿势.txt"),),
                "动作": (cls._load_options("动作.txt"),),
                "朝向": (cls._load_options("朝向.txt"),),
                "灯光": (cls._load_options("灯光.txt"),),
                "俯仰": (cls._load_options("俯仰.txt"),),
                "地点": (cls._load_options("地点.txt"),),
                "天气": (cls._load_options("天气.txt"),),
                "上衣": (cls._load_options("上衣.txt"),),
                "下装": (cls._load_options("下装.txt"),),
                "靴子": (cls._load_options("靴子.txt"),),
                "配饰": (cls._load_options("配饰.txt"),),
                "相机": (cls._load_options("相机.txt"),),
                "镜头": (cls._load_options("镜头.txt"),),
                "季节": (cls._load_options("季节.txt"),),
                "特效": (cls._load_options("特效.txt"),),
            },
            "optional": {
                "txt_str": ("STRING", {"default": " "}),  # lora关键词
            }
        }

    # 修改返回类型为三个STRING
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("中文标签", "英文标签", "中英混合标签")
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

    def generate_text(self, txt_str, 画质, 画风, 特效, 相机, 镜头, 灯光, 俯仰, 地点, 姿势, 朝向, 动作, 上衣, 下装, 靴子, 配饰, 天气, 季节, 人物, 性别, 角色):
        fields = ["画质", "画风", "特效", "相机", "镜头", "灯光", "俯仰", "地点",
                  "姿势", "朝向", "动作", "上衣", "下装", "靴子", "配饰", "天气",
                  "季节", "人物", "性别", "角色"]
        values = [画质, 画风, 特效, 相机, 镜头, 灯光, 俯仰, 地点, 姿势, 朝向,
                  动作, 上衣, 下装, 靴子, 配饰, 天气, 季节, 人物, 性别, 角色]

        selections = {}
        for field, value in zip(fields, values):
            field_options = self.INPUT_TYPES()['required'].get(field, (["忽略 (Ignore)"],))[0]
            selections[field] = self.random_choice(value, field_options)

        # 分别收集中文、英文、中英混合的关键词
        chinese_keywords = []
        english_keywords = []
        mix_keywords = []

        for field, value in selections.items():
            if "忽略" not in value:
                chinese_part, english_part = self._extract_parts(value)

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

        return (chinese_result, english_result, mix_result)