from .service.PoseKeypointData import PoseKeypointData
from .service.EmptyLatentImage import EmptyLatentImage
from .service.BatchImageLoader import BatchImageLoader
from .service.LLMNode import LLMNode
from .service.VisionModelNode import VisionModelNode
from .service.PromptSelectorNode import PromptSelectorNode
from .service.MultiPurposeNode import MultiPurposeNode
from .service.ImageRecognitionNode import ImageRecognitionNode
from .service.ImageDrawNode import ImageDrawNode

NODE_CLASS_MAPPINGS = {
    "PoseKeypointData": PoseKeypointData,
    "EmptyLatentImage": EmptyLatentImage,
    "BatchImageLoader": BatchImageLoader,
    "LLMNode": LLMNode,
    "VisionModelNode": VisionModelNode,
    "PromptSelectorNode": PromptSelectorNode,
    "MultiPurposeNode":MultiPurposeNode,
    "ImageRecognitionNode":ImageRecognitionNode,
    "ImageDrawNode":ImageDrawNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseKeypointData": "Luy-POSE数据转换",
    "EmptyLatentImage": "Luy-输出图片尺寸",
    "BatchImageLoader": "Luy-文件夹读取批量图片",
    "LLMNode": "Luy-Ollama语言大模型",
    "VisionModelNode":"Luy-Ollama视觉大模型",
    "PromptSelectorNode": "Luy-提示词选择器",
    "MultiPurposeNode": "Luy-本地多功能AI节点",
    "ImageRecognitionNode": "Luy-图片反推",
    "ImageDrawNode": "Luy-涂鸦"
}