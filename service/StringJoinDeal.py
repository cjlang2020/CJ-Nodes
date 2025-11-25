# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class StringJoinDeal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "original_str": ("STRING", {"default": "请输入原始字符串..."}),
                "join_type": (["拼接在前", "拼接在后", "字符串替换", "透传不处理"],),
                "new_str": ("STRING", {  # 新增/保留：用于拼接或替换的字符串
                    "multiline": True,
                    "default": "请输入..."
                })
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "strdeal"
    CATEGORY = "luy"

    def strdeal(self, original_str, join_type, new_str):
        """
        处理字符串的核心逻辑
        :param original_str: 传入的原始字符串（待处理）
        :param join_type: 处理类型（拼接在前/在后、字符串替换、透传不处理）
        :param new_str: 拼接用字符串 或 替换后的新子串
        :return: 处理后的字符串
        """
        if join_type == "拼接在前":
            return (new_str + original_str,)
        elif join_type == "拼接在后":
            return (original_str + new_str,)
        elif join_type == "字符串替换":
            return (new_str,)
        elif join_type == "透传不处理":
            return (original_str,)