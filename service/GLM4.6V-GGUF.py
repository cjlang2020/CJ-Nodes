from llama_cpp import Llama
import os

# 配置参数
GGUF_MODEL_PATH = r"D:/AI/comfyui_models/LLM/GLM-4.6V-Flash.Q5_K_S.gguf"  # 替换为你的GGUF文件路径
IMAGE_PATH = r"D:/Image/test1.png"  # 仅作为文本描述传入，GGUF暂不支持直接加载图片
MAX_NEW_TOKENS = 1024
TEMPERATURE = 0.7
TOP_P = 0.9

# 1. 验证GGUF模型文件存在
if not os.path.exists(GGUF_MODEL_PATH):
    raise FileNotFoundError(f"GGUF模型文件不存在：{GGUF_MODEL_PATH}")

# 2. 初始化llama-cpp模型（适配GLM-4.6V）
llm = Llama(
    model_path=GGUF_MODEL_PATH,
    n_ctx=8192,  # 上下文窗口大小，匹配GLM-4.6V
    n_threads=8,  # CPU线程数（根据你的CPU调整）
    n_gpu_layers=-1,  # 全部层加载到GPU（-1），仅支持NVIDIA显卡
    verbose=False,  # 关闭冗余日志
)

# 3. 构造提示词（GLM-4.6V 对话格式）
prompt = f"""<|user|>
请描述这张图片：{IMAGE_PATH}
<|assistant|>"""

# 4. 生成回复
output = llm.create_completion(
    prompt=prompt,
    max_tokens=MAX_NEW_TOKENS,
    temperature=TEMPERATURE,
    top_p=TOP_P,
    stop=["<|user|>", "<|assistant|>"],  # 终止符，匹配GLM格式
    echo=False  # 不回显输入提示词
)

# 5. 输出结果
print("生成结果：")
print(output["choices"][0]["text"].strip())