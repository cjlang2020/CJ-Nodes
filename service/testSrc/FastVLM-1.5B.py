import torch
from PIL import Image
from transformers import AutoTokenizer, AutoModelForCausalLM
MID = "D:/AI/comfyui_models/FastVLM-1.5B"
IMAGE_TOKEN_INDEX = -200  # what the model code looks for
# Load
tok = AutoTokenizer.from_pretrained(MID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MID,
    dtype="auto",
    device_map="cuda:0",
    trust_remote_code=True,
)
messages = [
    {"role": "user", "content": "<image>\n用中文简要描述这张图片风格、布局、存在的元素等。"}
]
rendered = tok.apply_chat_template(
    messages, add_generation_prompt=True, tokenize=False
)
pre, post = rendered.split("<image>", 1)
pre_ids  = tok(pre,  return_tensors="pt", add_special_tokens=False).input_ids
post_ids = tok(post, return_tensors="pt", add_special_tokens=False).input_ids
img_tok = torch.tensor([[IMAGE_TOKEN_INDEX]], dtype=pre_ids.dtype)
input_ids = torch.cat([pre_ids, img_tok, post_ids], dim=1).to(model.device)
attention_mask = torch.ones_like(input_ids, device=model.device)
img = Image.open("C:/Users/Lang/Pictures/cpmfyui_output/ComfyUI_00077_.png").convert("RGB")
px = model.get_vision_tower().image_processor(images=img, return_tensors="pt")["pixel_values"]
px = px.to(model.device, dtype=model.dtype)
with torch.no_grad():
    out = model.generate(
        inputs=input_ids,
        attention_mask=attention_mask,
        images=px,
        max_new_tokens=512,
    )
print(tok.decode(out[0], skip_special_tokens=True))
