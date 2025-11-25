import torch

from torchvision.io import decode_image, ImageReadMode
from torchvision.transforms.v2 import ToDtype, ToPILImage

from ultrazoom.model import UltraZoom
from ultrazoom.control import ControlVector


model_name = "D:/AI/comfyui_models/LLM/UltraZoom-2X-Ctrl"
image_path = "C:/Users/Lang/Pictures/Comfyui/output/ComfyUI_00752_.png"

model = UltraZoom.from_pretrained(model_name)

image_to_tensor = ToDtype(torch.float32, scale=True)
tensor_to_pil = ToPILImage()

image = decode_image(image_path, mode=ImageReadMode.RGB)

x = image_to_tensor(image).unsqueeze(0)

c = ControlVector(
    gaussian_blur=0.5,      # Higher values indicate more degradation
    gaussian_noise=0.2,     # which increases the strength of the
    jpeg_compression=0.3    # enhancement [0, 1].
).to_tensor()

y_pred = model.upscale(x, c)

pil_image = tensor_to_pil(y_pred.squeeze(0))

pil_image.show()
