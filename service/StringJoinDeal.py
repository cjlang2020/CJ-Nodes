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
                "text1": ("STRING", {"default": ""}),
                "join_type": (["t1->t2", "t2->t1", "t2", "t1"],),
                "text2": ("STRING", {
                    "multiline": True,
                    "default": ""
                })
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "strdeal"
    CATEGORY = "luy/字符处理"

    def strdeal(self, text1, join_type, text2):
        """
        处理字符串的核心逻辑
        :param original_str: 传入的原始字符串（待处理）
        :param join_type: 处理类型（拼接在前/在后、字符串替换、透传不处理）
        :param new_str: 拼接用字符串 或 替换后的新子串
        :return: 处理后的字符串
        """
        if join_type == "t2->t1":
            return (text2 +","+ text1,)
        elif join_type == "t1->t2":
            return (text1 +","+ text2,)
        elif join_type == "t2":
            return (text2,)
        elif join_type == "t1":
            return (text1,)