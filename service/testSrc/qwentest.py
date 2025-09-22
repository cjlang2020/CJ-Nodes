from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "D:/AI/comfyui_models/LLM/Qwen3-0.6B-FP8"

# 加载tokenizer和模型
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="cuda:0"
)

# 准备模型输入
prompt = "帮我写一段修真界战斗画面的描述词，我要用提示词生成图片，描写尽量详细，丰富,只输出提示词，不要输出其它内容。"
messages = [
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False  # 切换思考模式和非思考模式，默认为True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

# 文本生成（添加参数调整）
generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=32768,  # 最大生成token数
    # 生成参数调整
    temperature=0.7,       # 温度参数，控制随机性（0-1，值越低越确定）
    top_p=0.2,             # 核采样概率，控制候选词范围（0-1，值越小候选词越少）
    top_k=50,              # 只从概率最高的k个词中选择（0表示不限制）
    do_sample=True,        # 启用采样生成（否则使用贪心解码）
    repetition_penalty=1.1 # 重复惩罚，减少重复内容（>1时生效）
)

# 处理生成结果
output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

# 解析思考内容（如果有）
try:
    # 查找思考模式结束标记
    index = len(output_ids) - output_ids[::-1].index(151668)
except ValueError:
    index = 0

content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")
print("content:", content)
