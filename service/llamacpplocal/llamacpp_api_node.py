"""
LlamaCpp API 本地服务连接节点
通过HTTP API连接本地llama.cpp服务器，支持图片输入
"""
import os
import io
import json
import base64
import requests
import numpy as np
import torch
from PIL import Image
import folder_paths


# 提示词模板目录（T目录：文本模板，V目录：视觉模板）
AITOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "aitools")
T_DIR = os.path.join(AITOOLS_DIR, "T")  # 文本提示词模板
V_DIR = os.path.join(AITOOLS_DIR, "V")  # 视觉提示词模板（图片分析）

# 预设提示词字典
preset_prompts = {}


def load_prompts():
    """加载T和V目录下的所有提示词模板"""
    global preset_prompts
    preset_prompts = {}

    # 加载T目录（文本模板）
    if os.path.exists(T_DIR) and os.path.isdir(T_DIR):
        for filename in os.listdir(T_DIR):
            if filename.endswith(".txt") and not filename.startswith(('.', '~')):
                filepath = os.path.join(T_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # 标记为T目录模板
                        preset_prompts[f"[T] {filename}"] = f.read().strip()
                except Exception as e:
                    print(f"[LlamaCppAPI] 加载T目录提示词失败 {filename}: {str(e)[:50]}")

    # 加载V目录（视觉/图片分析模板）
    if os.path.exists(V_DIR) and os.path.isdir(V_DIR):
        for filename in os.listdir(V_DIR):
            if filename.endswith(".txt") and not filename.startswith(('.', '~')):
                filepath = os.path.join(V_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # 标记为V目录模板
                        preset_prompts[f"[V] {filename}"] = f.read().strip()
                except Exception as e:
                    print(f"[LlamaCppAPI] 加载V目录提示词失败 {filename}: {str(e)[:50]}")

    return list(preset_prompts.keys()) if preset_prompts else ["请放入提示词文件"]


# 初始化加载
preset_tags = load_prompts()


def image_to_base64(image_tensor):
    """
    将ComfyUI的IMAGE tensor转换为base64字符串
    IMAGE tensor格式: [batch, height, width, channels] 或 [height, width, channels]
    值范围: 0.0-1.0 float
    """
    # 处理不同维度的tensor
    if isinstance(image_tensor, torch.Tensor):
        # 移除batch维度（如果存在）
        if image_tensor.ndim == 4:
            image_tensor = image_tensor[0]

        # 转换为numpy数组，范围从0-1转为0-255
        img_array = np.clip(255.0 * image_tensor.cpu().numpy(), 0, 255).astype(np.uint8)
    else:
        img_array = image_tensor

    # 创建PIL图像并转换为base64
    pil_image = Image.fromarray(img_array)
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG", quality=85)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_base64


def scale_image_tensor(image_tensor, max_size=512):
    """
    缩放图像tensor到指定最大尺寸
    """
    if isinstance(image_tensor, torch.Tensor):
        if image_tensor.ndim == 4:
            image_tensor = image_tensor[0]
        img_array = np.clip(255.0 * image_tensor.cpu().numpy(), 0, 255).astype(np.uint8)
    else:
        img_array = image_tensor

    pil_image = Image.fromarray(img_array)
    w, h = pil_image.size
    scale = min(max_size / max(w, h), 1.0)
    new_w, new_h = int(w * scale), int(h * scale)

    if scale < 1.0:
        pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    return pil_image


class LlamaCppAPINode:
    """
    连接本地llama.cpp HTTP API服务的节点
    支持OpenAI兼容的API格式，支持图片输入
    """

    @classmethod
    def INPUT_TYPES(s):
        # 刷新提示词列表
        tags = load_prompts()
        return {
            "required": {
                "url": ("STRING", {
                    "default": "http://127.0.0.1:9900/v1",
                    "multiline": False,
                    "tooltip": "llama.cpp服务器API地址"
                }),
                "preset_prompt": (tags, {
                    "default": tags[0] if tags else "",
                    "tooltip": "选择预设提示词模板"
                }),
                "custom_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入自定义提示词...",
                    "tooltip": "自定义提示词，会追加到模板后面"
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 1,
                    "max": 4096,
                    "step": 1,
                    "tooltip": "生成的最大token数量"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "生成温度，越高越随机"
                }),
            },
            "optional": {
                "images": ("IMAGE", {
                    "tooltip": "输入图片（可选），支持多张图片"
                }),
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "系统提示词（可选）"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "step": 1,
                    "tooltip": "随机种子，-1表示随机"
                }),
                "image_max_size": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 1024,
                    "step": 64,
                    "tooltip": "图片最大尺寸，超过会自动缩放"
                }),
                "max_frames": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": 64,
                    "step": 1,
                    "tooltip": "批量图片时最多处理的帧数"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output",)
    FUNCTION = "process"
    CATEGORY = "luy/AI"

    def process(self, url, preset_prompt, custom_prompt, max_tokens, temperature,
                images=None, system_prompt="", seed=-1, image_max_size=512, max_frames=8):
        """
        调用本地llama.cpp API服务，支持图片输入
        """
        # 构建完整提示词
        preset_content = preset_prompts.get(preset_prompt, "")

        if preset_content and custom_prompt:
            full_prompt = f"{preset_content}\n{custom_prompt}"
        elif preset_content:
            full_prompt = preset_content
        else:
            full_prompt = custom_prompt

        if not full_prompt.strip() and images is None:
            return ("错误：提示词和图片均为空，请至少提供一项",)

        # 构建消息内容
        user_content = []

        # 添加文本提示词
        if full_prompt.strip():
            user_content.append({
                "type": "text",
                "text": full_prompt
            })

        # 处理图片输入
        if images is not None:
            # 获取图片数量
            batch_size = images.shape[0] if images.ndim == 4 else 1

            # 限制处理的帧数
            if batch_size > max_frames:
                indices = np.linspace(0, batch_size - 1, max_frames, dtype=int)
                images_to_process = [images[i] if images.ndim == 4 else images for i in indices]
                print(f"[LlamaCppAPI] 批量图片共{batch_size}张，处理前{max_frames}张")
            else:
                images_to_process = [images[i] for i in range(batch_size)] if images.ndim == 4 else [images]

            for idx, image in enumerate(images_to_process):
                try:
                    # 缩放图片
                    pil_image = scale_image_tensor(image, image_max_size)

                    # 转换为base64
                    buffered = io.BytesIO()
                    pil_image.save(buffered, format="JPEG", quality=85)
                    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

                    # 添加图片到消息内容（OpenAI Vision格式）
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    })
                    print(f"[LlamaCppAPI] 成功处理图片 {idx + 1}/{len(images_to_process)}")
                except Exception as e:
                    print(f"[LlamaCppAPI] 图片处理失败: {str(e)[:50]}")
                    continue

        # 构建API请求
        messages = []

        if system_prompt.strip():
            messages.append({
                "role": "system",
                "content": system_prompt.strip()
            })

        messages.append({
            "role": "user",
            "content": user_content
        })

        # 构建请求体
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        if seed >= 0:
            payload["seed"] = seed

        # 确保URL格式正确
        api_url = url.rstrip('/')
        if not api_url.endswith('/chat/completions'):
            api_url = f"{api_url}/chat/completions"

        # 发送请求
        try:
            print(f"[LlamaCppAPI] 正在连接: {api_url}")
            print(f"[LlamaCppAPI] 消息内容: 文本{len([c for c in user_content if c['type']=='text'])}项, 图片{len([c for c in user_content if c['type']=='image_url'])}张")

            response = requests.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=payload,
                timeout=180  # 3分钟超时（图片处理可能较慢）
            )

            if response.status_code != 200:
                error_text = response.text[:300]
                return (f"API错误 ({response.status_code}): {error_text}",)

            # 解析响应
            result = response.json()

            # OpenAI兼容格式
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                # 清理输出
                content = content.lstrip(": ").lstrip().rstrip()
                return (content,)
            else:
                return (f"API响应格式错误: {json.dumps(result)[:200]}",)

        except requests.exceptions.ConnectionError:
            return (f"连接失败：无法连接到 {api_url}，请检查服务是否启动",)
        except requests.exceptions.Timeout:
            return (f"请求超时：服务器响应时间过长（图片处理可能较慢）",)
        except requests.exceptions.RequestException as e:
            return (f"请求异常：{str(e)[:150]}",)
        except json.JSONDecodeError as e:
            return (f"JSON解析失败：{str(e)[:100]}",)
        except Exception as e:
            return (f"未知错误：{str(e)[:150]}",)


class LlamaCppAPIRefreshPrompts:
    """刷新提示词模板列表的辅助节点"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "process"
    CATEGORY = "luy/AI"

    def process(self, any):
        global preset_tags
        preset_tags = load_prompts()
        count = len(preset_tags)
        return (f"已刷新提示词模板，当前共 {count} 个模板",)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "LlamaCppAPINode": LlamaCppAPINode,
    "LlamaCppAPIRefreshPrompts": LlamaCppAPIRefreshPrompts,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LlamaCppAPINode": "LlamaCpp本地API",
    "LlamaCppAPIRefreshPrompts": "刷新提示词模板",
}