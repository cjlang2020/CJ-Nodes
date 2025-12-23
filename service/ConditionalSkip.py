# 示例：自定义一个“条件开关”节点
class ConditionalSkip:
    RETURN_TYPES = ("STRING",)
    FUNCTION = "skip"
    CATEGORY = "luy"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "enable": ("BOOLEAN", {"default": True}),  # 开关
                "input_data": ("STRING",),  # 输入数据
            }
        }

    def skip(self, enable, input_data):
        # 若enable=False，返回空（使下游节点跳过该分支）
        return (input_data,) if enable else (None,)