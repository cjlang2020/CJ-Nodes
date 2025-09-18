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