import node_helpers
import comfy.utils
import math
from comfy_api.latest import ComfyExtension, io
import comfy.utils
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class QwenEditAddLlamaTemplate(BaseNode):
    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "vae": ("VAE",),
            },
            "optional": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "image3": ("IMAGE",),
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入提示词...",
                    "rows": 5
                }),
                "llama_template": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入llama_template...",
                    "rows": 3
                }),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("positive",)
    FUNCTION = "execute"
    CATEGORY = "luy/千问编辑"

    def execute(self,image1=None, image2=None, image3=None,clip=None,vae=None,prompt="",llama_template=""):
        ref_latents = []
        images = [image1, image2, image3]
        images_vl = []
        if llama_template=="":
            llama_template = "<|im_start|>system 1. First, carefully analyze Picture 1 and Picture 2:- For Picture 1: Identify the position, angle, and contour of the face (including hairline, jawline).- For Picture 2: Extract detailed facial features (eyes, nose, mouth, skin tone, facial expression).2. Follow the user's instruction to 'migrate Picture 2's face to Picture 1's face':- Replace Picture 1's facial features with Picture 2's, while keeping Picture 1's original face position, angle, and surrounding context (e.g., hair, background) unchanged.- Ensure the migrated face looks natural (consistent lighting, skin texture blending).<|im_end|><|im_start|>user{}<|im_end|><|im_start|>assistant"
        image_prompt = ""

        for i, image in enumerate(images):
            if image is not None:
                samples = image.movedim(-1, 1)
                total = int(384 * 384)

                scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
                width = round(samples.shape[3] * scale_by)
                height = round(samples.shape[2] * scale_by)

                s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
                images_vl.append(s.movedim(1, -1))
                if vae is not None:
                    total = int(1024 * 1024)
                    scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
                    width = round(samples.shape[3] * scale_by / 8.0) * 8
                    height = round(samples.shape[2] * scale_by / 8.0) * 8

                    s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
                    ref_latents.append(vae.encode(s.movedim(1, -1)[:, :, :, :3]))

                image_prompt += "Picture {}: <|vision_start|><|image_pad|><|vision_end|>".format(i + 1)
        print("image_prompt + prompt=="+image_prompt +">>>>"+ prompt)
        print("llama_template=="+llama_template)
        tokens = clip.tokenize(image_prompt + prompt, images=images_vl, llama_template=llama_template)
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        if len(ref_latents) > 0:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"reference_latents": ref_latents}, append=True)
        return io.NodeOutput(conditioning)