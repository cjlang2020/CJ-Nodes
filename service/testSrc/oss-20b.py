from llama_cpp import Llama

def load_and_use_model(model_path):
    # 加载模型
    # n_ctx: 上下文窗口大小，根据需求调整（越大占用内存越多）
    # n_threads: 推理使用的线程数，建议设为 CPU 核心数
    # n_gpu_layers: 加载到 GPU 的层数（需要支持 CUDA 的版本）
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=8,
        n_gpu_layers=20  # 调整为合适的值，0 表示仅使用 CPU
    )

    # 提示词
    prompt = "请解释什么是人工智能？"

    # 生成响应
    # max_tokens: 最大生成 tokens 数
    # stop: 停止符，遇到这些字符串停止生成
    # temperature: 温度参数，越高生成越随机（0-1）
    output = llm(
        prompt=prompt,
        max_tokens=512,
        stop=["\n\n", "用户："],
        temperature=0.7
    )

    # 提取并返回生成的文本
    generated_text = output["choices"][0]["text"]
    return prompt + generated_text

if __name__ == "__main__":
    # 模型文件路径（替换为你的模型实际路径）
    model_path = "D:/AI/comfyui_models/unet/gpt-oss-20b-Q4_0.gguf"

    try:
        result = load_and_use_model(model_path)
        print("生成结果：")
        print(result)
    except Exception as e:
        print(f"发生错误：{e}")
