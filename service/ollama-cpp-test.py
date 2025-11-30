import os
import json
import torch
from llama_cpp import Llama, llama_rope_scaling_type  # 导入rope scaling类型枚举
from PIL import Image
import numpy as np

class Qwen3GGUFNode:
    """ComfyUI节点：加载Qwen3-4B GGUF模型进行文本生成"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": ("STRING", {
                    "default": "./models/qwen3-4b-chat.Q4_K_M.gguf",
                    "tooltip": "GGUF模型文件路径"
                }),
                "prompt": ("STRING", {
                    "default": "你好，请介绍一下自己",
                    "multiline": True,
                    "tooltip": "用户提示词"
                }),
                "max_tokens": ("INT", {
                    "default": 1024,
                    "min": 1,
                    "max": 4096,
                    "step": 1,
                    "tooltip": "最大生成token数"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "tooltip": "生成温度"
                }),
                "top_p": ("FLOAT", {
                    "default": 0.95,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "Top-p采样参数"
                }),
                "top_k": ("INT", {
                    "default": 40,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "Top-k采样参数"
                }),
                "repeat_penalty": ("FLOAT", {
                    "default": 1.1,
                    "min": 1.0,
                    "max": 2.0,
                    "step": 0.01,
                    "tooltip": "重复惩罚系数"
                }),
                "n_threads": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": os.cpu_count() or 8,
                    "step": 1,
                    "tooltip": "CPU线程数"
                }),
                "n_gpu_layers": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "GPU加速层数"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate_response"
    CATEGORY = "LLM/Qwen3"
    DESCRIPTION = "使用Qwen3-4B GGUF模型进行文本生成，不包含思考模式"

    def __init__(self):
        self.llm = None
        self.current_model_path = None

    def _load_model(self, model_path, n_threads, n_gpu_layers):
        """加载或重用模型实例"""
        if self.current_model_path == model_path and self.llm is not None:
            return self.llm

        # 关闭现有模型
        if self.llm is not None:
            self.llm.close()
            self.llm = None

        # 加载新模型 - 修复rope_scaling_type参数
        try:
            # 尝试使用枚举值设置rope_scaling_type
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
                # 修复：使用整数枚举值而不是字符串
                rope_scaling_type=llama_rope_scaling_type.LLAMA_ROPE_SCALING_TYPE_YARN,
                rope_freq_base=10000.0,
                rope_freq_scale=0.5,
            )
        except (AttributeError, TypeError):
            # 如果枚举不可用，使用兼容模式
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False,
                # 旧版本兼容：使用整数或省略rope_scaling_type
                rope_freq_base=10000.0,
                rope_freq_scale=0.5,
            )

        self.current_model_path = model_path
        return self.llm

    def _format_prompt(self, prompt):
        """格式化Qwen3的prompt，不包含思考模式"""
        return f"<|im_start|>system\n你是一个有帮助的助手，直接回答问题，不要开启思考模式<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

    def generate_response(self, model_path, prompt, max_tokens, temperature, top_p, top_k, repeat_penalty, n_threads, n_gpu_layers):
        """生成响应"""
        # 加载模型
        llm = self._load_model(model_path, n_threads, n_gpu_layers)

        # 格式化提示词
        formatted_prompt = self._format_prompt(prompt)

        # 生成响应
        output = llm.create_completion(
            prompt=formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=["<|im_end|>"],
            echo=False
        )

        # 提取并清理响应文本
        response_text = output["choices"][0]["text"].strip()

        return (response_text,)


# 节点映射配置
NODE_CLASS_MAPPINGS = {
    "Qwen3GGUFNode": Qwen3GGUFNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Qwen3GGUFNode": "Qwen3-4B GGUF 文本生成"
}


# 如果作为独立文件运行，提供测试功能
if __name__ == "__main__":
    # 创建节点实例并测试
    node = Qwen3GGUFNode()

    # 测试参数
    test_params = {
        "model_path": "D:/AI/comfyui_models/LLM/Qwen3-0.6B-Q4_K_M.gguf",
        "prompt": "你好，请介绍一下自己，不要使用思考模式",
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "n_threads": 8,
        "n_gpu_layers": 0,
    }

    try:
        # 生成响应
        result = node.generate_response(**test_params)
        print("生成结果：")
        print(result[0])
    except Exception as e:
        print(f"错误: {e}")
        print("\n请确保：")
        print("1. 模型文件路径正确")
        print("2. llama-cpp-python版本最新")
        print("3. 已安装必要的依赖")
