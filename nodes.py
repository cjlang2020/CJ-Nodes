from .service.Any2Any import (Any2Number,Any2String)
from .service.LatentUtils import (EmptyLatentImage,LuyLoadLatent,LuySaveLatent)
from .service.BatchImageLoader import (BatchImageLoader,ImagePathScanner,SingleImageLoader,StringArrayIndexer)
from .service.PromptSelectorNode import (PromptSelectorNode,PromptGenerator,Wan22PromptSelector)
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
from .service.FirstEndFrameDeal import FirstEndFrameDeal
from .service.MultiFrameVideo import MultiFrameVideo
from .service.VisClipCopy import VisClipCopyImageReference
from .service.LuyWanImageToVideoSVIPro import (LuyWanImageToVideoSVIPro,LuyWanImageToVideoSVIPro2)
from .service.LuyWanFirstLastFrameToVideo import (LuyWanFirstLastFrameToVideo,LuyWanFirstLastFrameToVideo2)
from .service.QwenMultiangleCameraNode import (QwenMultiangleCameraNode,QwenPlusMultiangleCameraNode,QwenLoraMultiangleCameraNode,QwenMultiangleLightningNode)
from .service.EditPromptNode import EditPromptNode

NODE_CLASS_MAPPINGS = {
    "Any2Number": Any2Number,
    "Any2String": Any2String,
    "LuyEmptyLatentImage": EmptyLatentImage,
    "LuyLoadLatent": LuyLoadLatent,
    "LuySaveLatent": LuySaveLatent,
    "ImagePathScanner": ImagePathScanner,
    "SingleImageLoader": SingleImageLoader,
    "StringArrayIndexer": StringArrayIndexer,
    "BatchImageLoader": BatchImageLoader,
    "PromptSelectorNode": PromptSelectorNode,
    "PromptGenerator":PromptGenerator,
    "Wan22PromptSelector":Wan22PromptSelector,
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
    "ShowCanvasImage":ShowCanvasImage,
    "MultiFrameVideo":MultiFrameVideo,
    "FirstEndFrameDeal":FirstEndFrameDeal,
    "VisClipCopyImageReference":VisClipCopyImageReference,
    "LuyWanImageToVideoSVIPro":LuyWanImageToVideoSVIPro,
    "LuyWanImageToVideoSVIPro2":LuyWanImageToVideoSVIPro2,
    "LuyWanFirstLastFrameToVideo":LuyWanFirstLastFrameToVideo,
    "LuyWanFirstLastFrameToVideo2":LuyWanFirstLastFrameToVideo2,
    "QwenMultiangleCameraNode": QwenMultiangleCameraNode,
    "QwenPlusMultiangleCameraNode": QwenPlusMultiangleCameraNode,
    "QwenLoraMultiangleCameraNode": QwenLoraMultiangleCameraNode,
    "QwenMultiangleLightningNode":QwenMultiangleLightningNode,
    "EditPromptNode":EditPromptNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Any2Number": "Luy-Any2Number",
    "Any2String": "Luy-Any2String",
    "LuyEmptyLatentImage": "Luy-创建空Latent",
    "LuyLoadLatent": "Luy-加载Latent",
    "LuySaveLatent": "Luy-保存Latent",
    "ImagePathScanner": "Luy-读取文件夹下图片路径",
    "BatchImageLoader": "Luy-批量读取文件夹下图片",
    "SingleImageLoader": "Luy-单张图片加载",
    "StringArrayIndexer": "Luy-读取数组值",
    "PromptSelectorNode": "Luy-提示词Web选择器",
    "PromptGenerator":"Luy-画图提示词",
    "Wan22PromptSelector":"Luy-Wan2.2提示词",
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
    "ShowCanvasImage":"Luy-画布图片显示",
    "MultiFrameVideo":"Luy-多帧视频处理",
    "FirstEndFrameDeal":"Luy-首尾帧处理",
    "VisClipCopyImageReference":"Luy-视觉参考",
    "LuyWanImageToVideoSVIPro":"Luy-图像转视频SVIPro",
    "LuyWanImageToVideoSVIPro2":"Luy-图像转视频SVIPro2",
    "LuyWanFirstLastFrameToVideo2":"Luy-首尾帧转视频(支持历史Latent无缝衔接)",
    "LuyWanFirstLastFrameToVideo":"Luy-首尾帧转视频",
    "QwenMultiangleCameraNode": "Luy-镜头视角控制（柯基版）",
    "QwenPlusMultiangleCameraNode": "Luy-镜头视角控制（魔改版）",
    "QwenLoraMultiangleCameraNode": "Luy-镜头视角控制（Lora标准版）",
    "QwenMultiangleLightningNode":"Luy-多角度光照控制节点",
    "EditPromptNode":"Luy-自定义提示词"
}

