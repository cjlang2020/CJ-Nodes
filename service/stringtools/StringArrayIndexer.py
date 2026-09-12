# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class StringArrayIndexer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "array": ("STRING", {"forceInput": True}),
                "index": ("INT", {
                    "default": 0, "min": -9999, "max": 9999,
                    "tooltip": "Index into the string array. Negative values count from the end (-1 = last). Out of range returns empty string."
                }),
            },
        }

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "get_item"
    CATEGORY = "luy/字符处理"

    def get_item(self, array, index):
        """
        从字符串数组中按索引获取指定字符串
        :param array: 字符串数组（INPUT_IS_LIST 使整个数组作为列表进入）
        :param index: 索引，支持负数（-1 为最后一项）；越界返回空字符串
        :return: (单个字符串,)
        """
        arr = array
        idx = index[0] if isinstance(index, list) else index

        # 兼容上游输出的嵌套列表（[[s1, s2, ...]]）
        if len(arr) == 1 and isinstance(arr[0], list):
            arr = arr[0]

        if isinstance(idx, list):
            idx = idx[0] if idx else 0

        if -len(arr) <= idx < len(arr):
            return (str(arr[idx]),)
        return ("",)
