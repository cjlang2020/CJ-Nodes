import torch
from diffusers import LattePipeline

def main():
    model_id = "D:/AI/comfyui_models/LLM/NewBie-image-Exp0.1"

    # Load pipeline
    pipe = LattePipeline.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
    ).to("cuda")
  # use float16 if your GPU does not support bfloat16

    prompt = "1girl"

    image = pipe(
        prompt,
        height=1024,
        width=1024,
        num_inference_steps=28,
    ).images[0]

    image.save("newbie_sample.png")
    print("Saved to newbie_sample.png")

if __name__ == "__main__":
    main()
