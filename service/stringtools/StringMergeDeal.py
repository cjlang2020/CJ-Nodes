# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class StringMergeDeal:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(1, 9):
            optional[f"text{i}"] = ("STRING", {"multiline": True, "default": ""})
        return {
            "required": {
                "delimiter": ("STRING", {"default": ","}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "merge_text"
    CATEGORY = "luy/字符处理"

    def merge_text(self, delimiter, **kwargs):
        """
        将多个输入字符串按分隔符拼接为一个字符串
        :param delimiter: 分隔符，支持字面量 \\n（换行）、\\t（制表符）
        :param kwargs: text1 ~ text8，可选输入，未连接或内容为空时忽略
        :return: (拼接后的字符串,)
        """
        # 支持用字面量 \n、\t 表示换行符、制表符
        delimiter = delimiter.replace("\\n", "\n").replace("\\t", "\t")

        parts = []
        for i in range(1, 9):
            value = kwargs.get(f"text{i}")
            if value is None:
                continue
            # 去除首尾空白后为空视为空项，忽略
            if not str(value).strip():
                continue
            parts.append(value)

        return (delimiter.join(parts),)
