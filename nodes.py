from .service.PoseKeypointData import PoseKeypointData
from .service.EmptyLatentImage import EmptyLatentImage
from .service.BatchImageLoader import BatchImageLoader
from .service.LLMNode import LLMNode
from .service.VisionModelNode import VisionModelNode
from .service.PromptSelectorNode import PromptSelectorNode

NODE_CLASS_MAPPINGS = {
    "PoseKeypointData": PoseKeypointData,
    "EmptyLatentImage": EmptyLatentImage,
    "BatchImageLoader": BatchImageLoader,
    "LLMNode": LLMNode,
    "VisionModelNode": VisionModelNode,
    "PromptSelectorNode": PromptSelectorNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseKeypointData": "POSE_KEYPOINT数据转换",
    "EmptyLatentImage": "输出图片尺寸",
    "BatchImageLoader": "从文件夹读取图片",
    "LLMNode": "本地大模型服务",
    "VisionModelNode":"本地视觉大模型",
    "PromptSelectorNode": "提示词选择器"
}