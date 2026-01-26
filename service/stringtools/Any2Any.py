import json

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode # type: ignore
except ImportError:
    class BaseNode:
        pass

class Any2String(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "any_input": ("*",),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert"
    CATEGORY = "luy/字符处理"
    DESCRIPTION = "任意输出转换为空字符串"

    def convert(self, any_input):

        return ("",)


class Any2Number(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert"
    CATEGORY = "luy/字符处理"
    DESCRIPTION = "任意输出转换为空串"

    def convert(self, image):

        return ("",)