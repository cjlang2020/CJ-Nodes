from llama_cpp import Llama

def load_gguf_model(model_path):
    """
    加载GGUF格式的大语言模型

    参数:
        model_path: GGUF模型文件的路径

    返回:
        加载好的Llama模型实例
    """
    try:
        # 加载模型，指定上下文窗口大小
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,  # 上下文窗口大小，根据模型能力和内存调整
            n_threads=8,  # 用于推理的线程数
            n_gpu_layers=40  # 加载到GPU的层数，0表示仅使用CPU
        )
        print(f"模型 {model_path} 加载成功！")
        return llm
    except Exception as e:
        print(f"模型加载失败: {e}")
        return None

def generate_text(llm, prompt, max_tokens=100, temperature=0.7):
    """
    使用加载的模型生成文本

    参数:
        llm: 加载好的Llama模型实例
        prompt: 输入提示词
        max_tokens: 最大生成 tokens 数
        temperature: 温度参数，控制生成的随机性

    返回:
        生成的文本
    """
    if llm is None:
        print("请先加载模型")
        return ""

    try:
        output = llm(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["\n", "用户:"],  # 停止条件
            echo=True  # 是否在输出中包含提示词
        )
        return output["choices"][0]["text"]
    except Exception as e:
        print(f"文本生成失败: {e}")
        return ""

if __name__ == "__main__":
    # 替换为你的GGUF模型文件路径
    MODEL_PATH = "D:/AI/comfyui_models/unet/gpt-oss-20b-Q4_0.gguf"

    # 加载模型
    llm_model = load_gguf_model(MODEL_PATH)

    # 如果模型加载成功，进行文本生成
    if llm_model:
        user_prompt = "请解释什么是人工智能？"
        print("输入提示:", user_prompt)

        generated_text = generate_text(
            llm=llm_model,
            prompt=user_prompt,
            max_tokens=300,
            temperature=0.8
        )

        print("\n生成结果:")
        print(generated_text)
