
import requests
from torch import device
from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image

path_model="D:/AI/comfyui_models/LLM/Florence-2-large-PromptGen-v2.0"

model = AutoModelForCausalLM.from_pretrained(path_model, trust_remote_code=True)
processor = AutoProcessor.from_pretrained(path_model, trust_remote_code=True)

prompt = "<MORE_DETAILED_CAPTION>"

url = "D:/Image/test1.png"
image = Image.open(url)

inputs = processor(text=prompt, images=image, return_tensors="pt").to(device)

generated_ids = model.generate(
    input_ids=inputs["input_ids"],
    pixel_values=inputs["pixel_values"],
    max_new_tokens=1024,
    do_sample=False,
    num_beams=3
)
generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

parsed_answer = processor.post_process_generation(generated_text, task=prompt, image_size=(image.width, image.height))

print(parsed_answer)