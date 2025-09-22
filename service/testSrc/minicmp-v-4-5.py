from PIL import Image
from llama_cpp import Llama
import base64
from io import BytesIO
from ctransformers import AutoModelForCausalLM
from PIL import Image
import base64
from io import BytesIO
# 加载GGUF模型
#model_path = "D:/AI/comfyui_models/LLM/GGUF/MiniCPM-v-4/MiniCPM-V-4_5-Q4_0.gguf"  # 替换为实际的GGUF文件名
# 加载模型
llm = AutoModelForCausalLM.from_pretrained(
    "D:/AI/comfyui_models/LLM/GGUF/MiniCPM-v-4",
    model_file="MiniCPM-V-4_5-Q4_0.gguf",
    model_type="minicpm",  # 可能需要根据实际情况调整
    context_length=2048,
    gpu_layers=50  # 调整为适合你GPU的层数
)

# 处理图片：转换为base64编码
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

image = Image.open('D:/Image/test1.png').convert('RGB')
image_b64 = image_to_base64(image)

# 构建包含图片的提示
question = "描述一下这个图片?"
prompt = f"""<image>{image_b64}</image>
{question}"""

# 生成回答
output = llm(
    prompt=prompt,
    max_tokens=512,
    stream=True,
    stop=["</s>"]
)

# 流式输出回答
generated_text = ""
for chunk in output:
    chunk_text = chunk["choices"][0]["text"]
    generated_text += chunk_text
    print(chunk_text, flush=True, end='')