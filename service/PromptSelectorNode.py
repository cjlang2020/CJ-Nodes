import random
import time
import os
# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class PromptSelectorNode(BaseNode):
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


class PromptGenerator(BaseNode):

    def __init__(self):
        pass

    @classmethod
    def _load_options(cls, filename):
        options = ["忽略 (Ignore)"]
        try:
            with open(os.path.join(os.path.dirname(__file__), "options", filename), encoding="utf-8") as f:
                options.extend(line.strip() for line in f if line.strip() and not line.strip().startswith('#'))
        except FileNotFoundError:
            pass
        options.append("随机 (Random)")
        return options

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "画质": (cls._load_options("画质.txt"),),
                "人物": (cls._load_options("人物.txt"),),
                "性别": (cls._load_options("性别.txt"),),
                "角色": (cls._load_options("角色.txt"),),
                "姿势": (cls._load_options("姿势.txt"),),
                "动作": (cls._load_options("动作.txt"),),
                "朝向": (cls._load_options("朝向.txt"),),
                "上衣": (cls._load_options("上衣.txt"),),
                "下装": (cls._load_options("下装.txt"),),
                "靴子": (cls._load_options("靴子.txt"),),
                "配饰": (cls._load_options("配饰.txt"),),
                "相机": (cls._load_options("相机.txt"),),
                "镜头": (cls._load_options("镜头.txt"),),
                "灯光": (cls._load_options("灯光.txt"),),
                "俯仰": (cls._load_options("俯仰.txt"),),
                "地点": (cls._load_options("地点.txt"),),
                "天气": (cls._load_options("天气.txt"),),
                "季节": (cls._load_options("季节.txt"),),
            },
            "optional": {
                "txt_str": ("STRING",{"default": " "}),  # lora关键词
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES =("标签",)
    FUNCTION = "generate_text"
    CATEGORY ="luy"

    def random_choice(self, selected_option, options):
        if selected_option == "随机 (Random)":
            actual_options = [opt for opt in options if "随机" not in opt and "忽略" not in opt]
            return random.choice(actual_options)
        return selected_option

    def generate_text(self,txt_str, 画质,相机, 镜头, 灯光,俯仰,地点,姿势,朝向,动作,上衣,下装,靴子,配饰,天气,季节,人物,性别,角色,):

        selections = {
            field: self.random_choice(value, self.INPUT_TYPES()['required'][field][0])
            for field, value in zip(
                ["画质","相机", "镜头", "灯光", "俯仰", "地点", "姿势", "朝向", "动作", "上衣", "下装", "靴子", "配饰", "天气", "季节", "人物", "性别","角色"],
                [画质, 相机, 镜头, 灯光, 俯仰, 地点, 姿势, 朝向, 动作, 上衣, 下装, 靴子, 配饰, 天气, 季节, 人物, 性别,角色]
            )
        }
        keyword = ",".join([
            selections[field].split(" (")[1][:-1]
            for field in selections if "忽略" not in selections[field]
        ])
        return (txt_str+","+keyword,)