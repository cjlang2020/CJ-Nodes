import json
from comfy.utils import common_upscale
import torchvision.transforms as T
import requests

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode
except ImportError:
    class BaseNode:
        pass

class LLMNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {
                    "multiline": False,
                    "default": "http://localhost:11434/api/generate"  # Ollama正确API地址
                }),
                "model_type": (["qwen3:0.6b", "qwen3:8b", "minicpm-v:8b"],),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "请输入你的问题..."
                }),
                "system_instruction": ("STRING", {
                    "multiline": True,
                    "default": "你是一个 helpful 的助手，请用中文回答问题。"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "call_llm"
    CATEGORY = "luy/ollama"

    def call_llm(self, url, model_type, prompt, system_instruction, temperature):
        """调用Ollama本地服务"""
        try:
            # 构建符合Ollama要求的请求体
            payload = {
                "model": model_type,
                "prompt": prompt,
                "system": system_instruction,  # 仅Ollama 0.1.26+支持单独的system参数
                "options": {
                    "temperature": temperature,
                    "num_ctx": 2048
                },
                "stream": False,  # 这里必须是布尔值False，不能是字符串
                "format": "json"  # 确保返回JSON格式
            }

            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=120  # 延长超时时间，避免模型处理超时
            )

            response.raise_for_status()  # 检查HTTP错误状态

            # 解析Ollama响应（与OpenAI格式不同）
            result = response.json()

            # Ollama的响应结果在response字段中
            if "response" in result:
                return (result["response"],)
            else:
                return (f"API返回格式异常: {str(result)}",)

        except requests.exceptions.RequestException as e:
            # 更详细的错误信息，包括响应内容
            error_msg = f"请求错误: {str(e)}"
            if hasattr(response, 'text'):
                error_msg += f"\n响应内容: {response.text}"
            return (error_msg,)
        except json.JSONDecodeError:
            return (f"解析响应失败，非JSON格式: {response.text}",)
        except Exception as e:
            return (f"发生错误: {str(e)}",)

