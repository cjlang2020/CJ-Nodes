import json

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode # type: ignore
except ImportError:
    class BaseNode:
        pass

class PoseKeypointData(BaseNode):
    """
    将POSE_KEYPOINT数据转换为字符串，并打印所有内容到控制台
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pose_keypoint": ("POSE_KEYPOINT",),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "convert_and_print"
    CATEGORY = "luy"
    DESCRIPTION = "打印POSE_KEYPOINT所有数据并转为字符串"

    def convert_and_print(self, pose_keypoint):
        """转换并打印所有数据"""
        try:
            return (json.dumps(pose_keypoint, ensure_ascii=False, indent=2),)
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            return (error_msg,)