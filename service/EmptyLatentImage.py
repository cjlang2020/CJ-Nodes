import comfy.model_management
import nodes
import torch
import torchvision.transforms as T

class EmptyLatentImage:
    def __init__(self):
        self.device = comfy.model_management.intermediate_device()

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "width": ("INT", {"default": 768, "min": 16, "max": nodes.MAX_RESOLUTION, "step": 16}),
            "height": ("INT", {"default": 1360, "min": 16, "max": nodes.MAX_RESOLUTION, "step": 16}),
            "宽高反转": ("BOOLEAN", {"default": False, "label_on": "Yes", "label_off": "No"}),
            "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096})
        }}
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "generate"

    CATEGORY = "luy"

    def generate(self, width, height, batch_size=1, 宽高反转=False):
        # 如果启用宽高反转，则交换宽高值
        if 宽高反转:
            width, height = height, width

        latent = torch.zeros([batch_size, 16, height // 8, width // 8], device=self.device)
        return ({"samples":latent}, )