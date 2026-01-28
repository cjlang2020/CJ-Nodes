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
    CATEGORY = "luy/提示词工具"

    def get_final_prompt(self, final_prompt):
        """
        核心处理函数：返回完整提示词 + 仅英文提示词
        """
        try:
            # 1. 清理原始提示词格式（去除多余逗号和空格）
            clean_prompt = final_prompt.strip().replace(",,", ",").rstrip(",")

            # 2. 过滤中文：保留英文、数字、标点和空格，移除所有中文字符
            # 正则匹配所有中文字符（包括繁体）并替换为空
            english_only_prompt = re.sub(r'[\u4e00-\u9fff\u3400-\u4dbf\u{20000}-\u{2a6df}\u{2a700}-\u{2b73f}\u{2b740}-\u{2b81f}\u{2b820}-\u{2ceaf}\u{2ceb0}-\u{2ebef}\u{30000}-\u{3134f}]', '', clean_prompt)
            # 清理过滤后多余的空格和逗号
            english_only_prompt = re.sub(r'\s+', ' ', english_only_prompt).strip()
            english_only_prompt = english_only_prompt.replace(",,", ",").rstrip(",").lstrip(",")

            logger.info(f"提示词处理完成 - 完整长度: {len(clean_prompt)} | 英文长度: {len(english_only_prompt)}")
            # 返回两个结果：完整提示词 + 仅英文提示词
            return (clean_prompt, english_only_prompt)

        except Exception as e:
            # 异常处理：两个输出都返回空字符串
            logger.error(f"提示词处理异常: {str(e)}")
            return ("", "")

# ComfyUI标准节点注册
NODE_CLASS_MAPPINGS = {
    "PromptPickerNode": PromptPickerNode
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptPickerNode": "Luy-SDXL提示词选择器"
}