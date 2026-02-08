import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

MODEL_PATH = "D:/AI/comfyui_models/LLM/GLM-OCR"

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "url": "D:/1.png"},
            {"type": "text", "text": "Text Recognition:"}
        ],
    }
]

processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH,
    dtype="auto",
    device_map="auto",
)

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
).to(model.device)

inputs.pop("token_type_ids", None)

generated_ids = model.generate(
    **inputs,
    max_new_tokens=8192
)

output_text = processor.decode(
    generated_ids[0][inputs["input_ids"].shape[1]:],
    skip_special_tokens=False
)

print(output_text)
