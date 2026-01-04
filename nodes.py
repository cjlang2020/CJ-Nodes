from .service.PoseKeypointData import PoseKeypointData
from .service.LatentUtils import (EmptyLatentImage,LuyLoadLatent,LuySaveLatent)
from .service.BatchImageLoader import BatchImageLoader
from .service.PromptSelectorNode import (PromptSelectorNode,PromptGenerator)
from .service.ImageDrawNode import (ImageDrawNode,ImageMaskNode)
from .service.RGBA_save_tools import SavePNGZIP_and_Preview_RGBA_AnimatedWEBP
from .service.MaskedImage2Png import (MaskedImage2Png,DrawImageBbox)
from .service.LuySdxlLoraLoader import (LuySdxlLoraLoader,LuyLoraLoaderModelOnlyALL,LuyLoraLoaderModelOnlyFLUX,LuyLoraLoaderModelOnlyQWEN,LuyLoraLoaderModelOnlyQWENEDIT,LuyLoraLoaderModelOnlyByDir,UpdateLoraMetaData)
from .service.QwenEditAddLlamaTemplate import QwenEditAddLlamaTemplate
from .service.Qwen3VlImage import ImageDeal
from .service.GPTChat import ChatDeal
from .service.Qwen3Chat import Qwen3Deal
from .service.MultiFunAINode import MultiFunAINode
from .service.StringJoinDeal import StringJoinDeal
from .service.ForItemByIndex import ForItemByIndex
from .service.FileDeal import (FileReadDeal,FileSaveDeal)
from .service.LoadImageUtils import (LoadImageUtils,FolderSelectNode,LuyLoadImageBatch,ShowCanvasImage)
from .service.VramClean import VRAMClean
from .service.ConditionalSkip import ConditionalSkip


NODE_CLASS_MAPPINGS = {
    "PoseKeypointData": PoseKeypointData,
    "LuyEmptyLatentImage": EmptyLatentImage,
    "LuyLoadLatent": LuyLoadLatent,
    "LuySaveLatent": LuySaveLatent,
    "BatchImageLoader": BatchImageLoader,
    "PromptSelectorNode": PromptSelectorNode,
    "PromptGenerator":PromptGenerator,
    "ImageDrawNode":ImageDrawNode,
    "ImageMaskNode":ImageMaskNode,
    "MaskedImage2Png":MaskedImage2Png,
    "DrawImageBbox":DrawImageBbox,
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": SavePNGZIP_and_Preview_RGBA_AnimatedWEBP,
    "LuySdxlLoraLoader": LuySdxlLoraLoader,
    "LuyLoraLoaderModelOnlyALL": LuyLoraLoaderModelOnlyALL,
    "LuyLoraLoaderModelOnlyFLUX": LuyLoraLoaderModelOnlyFLUX,
    "LuyLoraLoaderModelOnlyQWEN": LuyLoraLoaderModelOnlyQWEN,
    "LuyLoraLoaderModelOnlyQWENEDIT": LuyLoraLoaderModelOnlyQWENEDIT,
    "LuyLoraLoaderModelOnlyByDir":LuyLoraLoaderModelOnlyByDir,
    "UpdateLoraMetaData":UpdateLoraMetaData,
    "QwenEditAddLlamaTemplate":QwenEditAddLlamaTemplate,
    "ImageDeal":ImageDeal,
    "ChatDeal":ChatDeal,
    "Qwen3Chat":Qwen3Deal,
    "MultiFunAINode":MultiFunAINode,
    "StringJoinDeal":StringJoinDeal,
    "ForItemByIndex":ForItemByIndex,
    "FileReadDeal":FileReadDeal,
    "FileSaveDeal":FileSaveDeal,
    "LoadImageUtils":LoadImageUtils,
    "FolderSelectNode":FolderSelectNode,
    "VRAMClean":VRAMClean,
    "ConditionalSkip":ConditionalSkip,
    "LuyLoadImageBatch":LuyLoadImageBatch,
    "ShowCanvasImage":ShowCanvasImage
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PoseKeypointData": "Luy-POSE数据转换",
    "LuyEmptyLatentImage": "Luy-创建空Latent",
    "LuyLoadLatent": "Luy-加载Latent",
    "LuySaveLatent": "Luy-保存Latent",
    "BatchImageLoader": "Luy-批量读取文件夹下图片",
    "PromptSelectorNode": "Luy-提示词选择器",
    "PromptGenerator":"Luy-提示词选择节点",
    "ImageDrawNode": "Luy-涂鸦绘制",
    "ImageMaskNode": "Luy-添加蒙版",
    "SavePNGZIP_and_Preview_RGBA_AnimatedWEBP": "Luy-RGBA图层转视频",
    "MaskedImage2Png": "Luy-遮罩转PNG",
    "DrawImageBbox":"Luy-绘制Bbox",
    "LuySdxlLoraLoader": "Luy-加载lora模型(SDXL)",
    "LuyLoraLoaderModelOnlyALL": "Luy-加载lora模型(FLUX|QWEN|QWEN-EDIT)",
    "LuyLoraLoaderModelOnlyFLUX": "Luy-加载lora模型(FLUX)",
    "LuyLoraLoaderModelOnlyQWEN": "Luy-加载lora模型(QWEN)",
    "LuyLoraLoaderModelOnlyQWENEDIT": "Luy-加载lora模型(QWEN-EDIT)",
    "LuyLoraLoaderModelOnlyByDir":"Luy-通过目录加载lora模型",
    "UpdateLoraMetaData":"Luy-更新元数据",
    "QwenEditAddLlamaTemplate":"Luy-千问编码器",
    "ImageDeal":"Luy-Qwen3-VL图片反推",
    "ChatDeal":"Luy-GPT语言大模型",
    "Qwen3Chat":"Luy-Qwen3语言大模型",
    "MultiFunAINode":"Luy-AI多功能语言大模型",
    "StringJoinDeal":"Luy-字符串处理",
    "ForItemByIndex":"Luy-循环取行文本",
    "FileReadDeal":"Luy-读取txt文件",
    "FileSaveDeal":"Luy-写入txt到文件夹",
    "LoadImageUtils":"Luy-加载图片",
    "FolderSelectNode":"Luy-选择文件夹",
    "VRAMClean":"Luy-清除显存占用",
    "ConditionalSkip":"Luy-跳过分支",
    "LuyLoadImageBatch":"Luy-批量加载",
    "ShowCanvasImage":"Luy-画布图片显示"
}