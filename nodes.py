from .service.PoseKeypointData import PoseKeypointData
from .service.EmptyLatentImage import EmptyLatentImage
from .service.BatchImageLoader import BatchImageLoader
from .service.LLMNode import LLMNode
from .service.VisionModelNode import VisionModelNode
from .service.PromptSelectorNode import (PromptSelectorNode,PromptGenerator)
from .service.MultiPurposeNode import MultiPurposeNode
from .service.ImageRecognitionNode import ImageRecognitionNode
from .service.ImageDrawNode import ImageDrawNode
from .service.ImageMaskNode import ImageMaskNode
from .service.RGBA_save_tools import SavePNGZIP_and_Preview_RGBA_AnimatedWEBP
from .service.MaskedImage2Png import (MaskedImage2Png,DrawImageBbox)
from .service.LuySdxlLoraLoader import (LuySdxlLoraLoader,LuyLoraLoaderModelOnly,LuyLoraLoaderModelOnlyByDir,UpdateLoraMetaData)
from .service.QwenEditAddLlamaTemplate import QwenEditAddLlamaTemplate
from .service.Qwen3VlImage import ImageDeal
from .service.GPTChat import ChatDeal

NODE_CLASS_MAPPINGS = {
    "PoseKeypointData": PoseKeypointData,
    "EmptyLatentImage": EmptyLatentImage,
    "BatchImageLoader": BatchImageLoader,
    "LLMNode": LLMNode,
    "VisionModelNode": VisionModelNode,
    "PromptSelectorNode": PromptSelectorNode,
    "PromptGenerator":PromptGenerator,
    "MultiPurposeNode":MultiPurposeNode,
    "ImageRecognitionNode":ImageRecognitionNode,
    "ImageDrawNode":ImageDrawNode,
    "ImageMaskNode":ImageMaskNode,
    "MaskedImage2Png":MaskedImage2Png,
    "DrawImageBbox":DrawImageBbox,
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": SavePNGZIP_and_Preview_RGBA_AnimatedWEBP,
    "LuySdxlLoraLoader": LuySdxlLoraLoader,
    "LuyLoraLoaderModelOnly": LuyLoraLoaderModelOnly,
    "LuyLoraLoaderModelOnlyByDir":LuyLoraLoaderModelOnlyByDir,
    "UpdateLoraMetaData":UpdateLoraMetaData,
    "QwenEditAddLlamaTemplate":QwenEditAddLlamaTemplate,
    "ImageDeal":ImageDeal,
    "ChatDeal":ChatDeal
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseKeypointData": "Luy-POSE数据转换",
    "EmptyLatentImage": "Luy-输出图片尺寸",
    "BatchImageLoader": "Luy-批量读取文件夹下图片",
    "LLMNode": "Luy-语言大模型",
    "VisionModelNode":"Luy-视觉大模型",
    "PromptSelectorNode": "Luy-提示词选择器",
    "PromptGenerator":"Luy-提示词选择节点",
    "MultiPurposeNode": "Luy-多功能AI",
    "ImageRecognitionNode": "Luy-苹果模型图片反推",
    "ImageDrawNode": "Luy-涂鸦绘制",
    "ImageMaskNode": "Luy-添加蒙版",
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": "Luy-RGBA图层",
    "MaskedImage2Png": "Luy-遮罩转PNG",
    "DrawImageBbox":"Luy-绘制Bbox",
    "LuySdxlLoraLoader": "Luy-加载lora模型(SDXL)",
    "LuyLoraLoaderModelOnly": "Luy-加载lora模型(FLUX|QWEN|QWEN-EDIT)",
    "LuyLoraLoaderModelOnlyByDir":"Luy-通过目录加载lora模型",
    "UpdateLoraMetaData":"Luy-更新元数据",
    "QwenEditAddLlamaTemplate":"Luy-千问编辑",
    "ImageDeal":"Luy-Qwen3-VL图片反推",
    "ChatDeal":"Luy-GPT语言大模型"
}