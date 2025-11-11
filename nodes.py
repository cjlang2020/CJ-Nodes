from .service.PoseKeypointData import PoseKeypointData
from .service.EmptyLatentImage import EmptyLatentImage
from .service.BatchImageLoader import BatchImageLoader
from .service.LLMNode import LLMNode
from .service.VisionModelNode import VisionModelNode
from .service.PromptSelectorNode import PromptSelectorNode
from .service.MultiPurposeNode import MultiPurposeNode
from .service.ImageRecognitionNode import ImageRecognitionNode
from .service.ImageDrawNode import ImageDrawNode
from .service.ImageMaskNode import ImageMaskNode
from .service.RGBA_save_tools import SavePNGZIP_and_Preview_RGBA_AnimatedWEBP
from .service.MaskedImage2Png import MaskedImage2Png
from .service.OllamaCppQwenVl import (LoadllamaCppModel,ImageAnasisyAdv,ChatAnasisyAdv,LlamaCppParameters,JsonToBbox)
from .service.LuySdxlLoraLoader import (LuySdxlLoraLoader,LuyLoraLoaderModelOnly,UpdateLoraMetaData)

NODE_CLASS_MAPPINGS = {
    "PoseKeypointData": PoseKeypointData,
    "EmptyLatentImage": EmptyLatentImage,
    "BatchImageLoader": BatchImageLoader,
    "LLMNode": LLMNode,
    "VisionModelNode": VisionModelNode,
    "PromptSelectorNode": PromptSelectorNode,
    "MultiPurposeNode":MultiPurposeNode,
    "ImageRecognitionNode":ImageRecognitionNode,
    "ImageDrawNode":ImageDrawNode,
    "ImageMaskNode":ImageMaskNode,
    "MaskedImage2Png":MaskedImage2Png,
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": SavePNGZIP_and_Preview_RGBA_AnimatedWEBP,
    "LoadllamaCppModel": LoadllamaCppModel,
    "ImageAnasisyAdv": ImageAnasisyAdv,
    "ChatAnasisyAdv": ChatAnasisyAdv,
    "LlamaCppParameters": LlamaCppParameters,
    "JsonToBbox": JsonToBbox,
    "LuySdxlLoraLoader": LuySdxlLoraLoader,
    "LuyLoraLoaderModelOnly": LuyLoraLoaderModelOnly,
    "UpdateLoraMetaData":UpdateLoraMetaData
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseKeypointData": "Luy-POSE数据转换",
    "EmptyLatentImage": "Luy-输出图片尺寸",
    "BatchImageLoader": "Luy-批量读取文件夹下图片",
    "LLMNode": "Luy-语言大模型",
    "VisionModelNode":"Luy-视觉大模型",
    "PromptSelectorNode": "Luy-提示词选择器",
    "MultiPurposeNode": "Luy-多功能AI",
    "ImageRecognitionNode": "Luy-苹果模型图片反推",
    "ImageDrawNode": "Luy-涂鸦绘制",
    "ImageMaskNode": "Luy-添加蒙版",
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": "Luy-RGBA图层",
    "MaskedImage2Png": "Luy-遮罩转PNG",
    "LoadllamaCppModel": "Luy-加载模型",
    "ImageAnasisyAdv": "Luy-图像反推",
    "ChatAnasisyAdv": "Luy-文本推理",
    "LlamaCppParameters": "Luy-参数设置",
    "JsonToBbox": "Luy-JSON to BBOX",
    "LuySdxlLoraLoader": "Lyu-加载lora模型(SDXL)",
    "LuyLoraLoaderModelOnly": "Lyu-加载lora模型(FLUX|QWEN|QWEN-EDIT)",
    "UpdateLoraMetaData":"Luy-更新元数据"
}