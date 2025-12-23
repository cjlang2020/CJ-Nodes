from transformers import AutoProcessor, Glm4vForConditionalGeneration
import torch
import os
from PIL import Image

# 模型路径（建议用 raw 字符串避免转义）
MODEL_PATH = r"D:/AI/comfyui_models/LLM/GLM-4.6V-Flash"
# 图片路径（重点：用 raw 字符串 + 绝对路径）
IMAGE_PATH = r"D:/Image/test1.png"

# ========== 第一步：验证并加载本地图片 ==========
# 检查图片文件是否存在
if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(f"图片文件不存在：{IMAGE_PATH}")
# 用 PIL 打开图片（转为处理器可识别的 PIL.Image 对象）
try:
    image = Image.open(IMAGE_PATH).convert("RGB")  # 强制转为 RGB 避免格式问题
except Exception as e:
    raise ValueError(f"图片加载失败：{e}")

# ========== 第二步：构造正确的 messages 格式 ==========
# 关键：GLM-4.6V 处理本地图片时，需将 image 内容直接传入，而非通过 url 传路径
messages = [
    {
        "role": "user",
        "content": [
            # 替换：url 字段改为直接传 PIL.Image 对象
            {"type": "image", "image": image},
            {"type": "text", "text": "describe this image"}
        ],
    }
]

# ========== 第三步：加载处理器和模型 ==========
# 加载处理器（禁用本地文件缓存，避免路径冲突）
processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    local_files_only=True,  # 强制加载本地模型，避免联网
    trust_remote_code=True  # GLM-4.6V 需开启该参数
)
# 加载模型（优化设备映射和显存占用）
model = Glm4vForConditionalGeneration.from_pretrained(
    pretrained_model_name_or_path=MODEL_PATH,
    torch_dtype=torch.float16,  # 显式指定 float16，减少显存占用
    device_map="cuda:0",
    trust_remote_code=True,
    local_files_only=True
)

# ========== 第四步：处理输入并生成回复 ==========
# 关键：apply_chat_template 直接接收 PIL.Image 对象，而非路径字符串
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
).to(model.device)

# 移除不必要的字段（避免模型报错）
inputs.pop("token_type_ids", None)

# 生成回复（优化生成参数）
generated_ids = model.generate(
    **inputs,
    max_new_tokens=1024,  # 8192 可能超出显存，先缩小测试
    do_sample=True,       # 开启采样，提升回复质量
    temperature=0.7,      # 采样温度，越低越精准
    top_p=0.9,
    eos_token_id=processor.tokenizer.eos_token_id
)

# 解码输出（跳过特殊 token，只保留文本）
output_text = processor.decode(
    generated_ids[0][inputs["input_ids"].shape[1]:],
    skip_special_tokens=True  # 改为 True，去掉 <s>/</s> 等特殊符号
)

print("生成结果：")
print(output_text)