import torch
import logging
import re

# 配置日志
logger = logging.getLogger(__name__)

class PromptPickerNode:
    @classmethod
    def INPUT_TYPES(cls):
        """定义节点输入参数（ComfyUI标准方法）"""
        return {
            "required": {
                # 多行提示词输入框（核心输出）
                "final_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "点击下方标签添加/移除提示词...",
                    "dynamicPrompts": False  # 禁用动态提示词解析，避免冲突
                }),
            }
        }

    # 定义输出类型和名称：新增english_prompt输出端口
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "english_prompt")
    # 核心处理函数名
    FUNCTION = "get_final_prompt"
    # 节点分类
    CATEGORY = "luy/提示词"

    def get_final_prompt(self, final_prompt):
        """
        核心处理函数：返回完整提示词 + 仅英文提示词
        修复Unicode转义不完整问题
        """
        try:
            # 1. 清理原始提示词格式（去除多余逗号和空格）
            clean_prompt = final_prompt.strip().replace(",,", ",").rstrip(",")

            # 2. 过滤中文：使用Python兼容的Unicode范围写法（修复核心）
            # 仅匹配简体中文（\u4e00-\u9fff），避免复杂的扩展Unicode导致转义错误
            # 正则说明：
            # \u4e00-\u9fff：覆盖所有简体中文字符
            # [^\x00-\x7f]：可选 - 匹配所有非ASCII字符（如果需要过滤所有非英文）
            english_only_prompt = re.sub(r'[\u4e00-\u9fff]', '', clean_prompt)

            # 3. 清理过滤后多余的空格和逗号
            english_only_prompt = re.sub(r'\s+', ' ', english_only_prompt).strip()
            english_only_prompt = english_only_prompt.replace(",,", ",").rstrip(",").lstrip(",")

            logger.info(f"提示词处理完成 - 完整长度: {len(clean_prompt)} | 英文长度: {len(english_only_prompt)}")
            # 返回两个结果：完整提示词 + 仅英文提示词
            return (clean_prompt, english_only_prompt)

        except Exception as e:
            # 异常处理：两个输出都返回空字符串，打印详细错误
            logger.error(f"提示词处理异常: {str(e)} | 输入内容: {final_prompt[:50]}")
            return ("", "")

# ComfyUI标准节点注册
NODE_CLASS_MAPPINGS = {
    "PromptPickerNode": PromptPickerNode
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptPickerNode": "提示词选择器 (点击添加/移除)"
}