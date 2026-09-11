# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class StringSplitDeal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
                "delimiter": ("STRING", {"default": ","}),
                "trim": ("BOOLEAN", {"default": True}),
                "remove_empty": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("array", "count")
    FUNCTION = "split_text"
    OUTPUT_IS_LIST = (True, False)
    CATEGORY = "luy/字符处理"

    def split_text(self, text, delimiter, trim, remove_empty):
        """
        将字符串按分隔符拆分为字符串数组
        :param text: 待拆分的原始字符串
        :param delimiter: 分隔符，支持字面量 \\n（换行）、\\t（制表符）
        :param trim: 是否去除每项首尾空白
        :param remove_empty: 是否移除空项
        :return: (字符串数组, 数组长度)
        """
        # 支持用字面量 \n、\t 表示换行符、制表符
        delimiter = delimiter.replace("\\n", "\n").replace("\\t", "\t")

        if delimiter:
            parts = text.split(delimiter)
        else:
            # 分隔符为空时按单个字符拆分
            parts = list(text)

        result = []
        for part in parts:
            if trim:
                part = part.strip()
            if remove_empty and not part:
                continue
            result.append(part)

        # 避免空数组导致下游节点不执行
        if not result:
            result = [""]

        return (result, len(result))
