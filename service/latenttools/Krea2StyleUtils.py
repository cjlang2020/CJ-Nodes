from __future__ import annotations

import math
from typing import List, Tuple, Optional

import torch


SEMANTIC_STYLE_INSTRUCTIONS_SINGLE = {
    "轻微": (
        "Use the attached reference image as a subtle style guide. Borrow only the broad color palette, "
        "surface texture, lighting mood, and visual rhythm. Do not copy the depicted subject."
    ),
    "平衡": (
        "Use the attached reference image as a style guide. Transfer its visual language, color palette, "
        "material texture, brushwork, lighting, composition rhythm, and overall mood. Do not copy the "
        "depicted subject unless the target prompt asks for it."
    ),
    "强烈": (
        "Use the attached reference image as a strong style guide. Strongly adopt its visual language, "
        "color palette, material texture, brushwork, lighting, composition rhythm, and overall mood, while "
        "keeping the target prompt as the subject and scene."
    ),
}

SEMANTIC_STYLE_INSTRUCTIONS_MULTI = {
    "轻微": (
        "Use the attached reference images as subtle style guides. Borrow only the broad color palettes, "
        "surface textures, lighting moods, and visual rhythms from the combined references. "
        "Blend the styles harmoniously. Do not copy the depicted subjects."
    ),
    "平衡": (
        "Use the attached reference images as style guides. Transfer their combined visual language, "
        "color palettes, material textures, brushwork, lighting, composition rhythms, and overall moods "
        "into a harmonious blend. Do not copy the depicted subjects unless the target prompt asks for it."
    ),
    "强烈": (
        "Use the attached reference images as strong style guides. Strongly adopt their combined visual "
        "language, color palettes, material textures, brushwork, lighting, composition rhythms, and overall "
        "moods into a bold, unified style, while keeping the target prompt as the subject and scene."
    ),
}

SEMANTIC_STYLE_INSTRUCTIONS = SEMANTIC_STYLE_INSTRUCTIONS_SINGLE


def _input_meta(display_name, tooltip, **extra):
    meta = {"display_name": display_name, "tooltip": tooltip}
    meta.update(extra)
    return meta


def _split_image_batch(image: torch.Tensor) -> List[torch.Tensor]:
    if image.shape[0] > 1:
        return [image[i:i+1] for i in range(image.shape[0])]
    return [image]


def _resize_image_for_vision(
    style_image: torch.Tensor,
    vision_resolution: int,
    maintain_aspect_ratio: bool = True,
    padding_color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> torch.Tensor:
    """
    Resize image for vision encoder with optional aspect ratio maintenance.

    Args:
        style_image: Input image tensor (B, H, W, C)
        vision_resolution: Target resolution (width/height)
        maintain_aspect_ratio: If True, maintain aspect ratio and pad
        padding_color: Color for padding (R, G, B) in [0, 1] range

    Returns:
        Resized image tensor (B, H, W, C)
    """
    samples = style_image.movedim(-1, 1)  # (B, C, H, W)
    total_pixels = max(1, int(vision_resolution) * int(vision_resolution))
    source_pixels = max(1, int(samples.shape[2]) * int(samples.shape[3]))
    scale_by = math.sqrt(total_pixels / source_pixels)
    width = max(1, round(samples.shape[3] * scale_by))
    height = max(1, round(samples.shape[2] * scale_by))

    try:
        import comfy.utils
        samples = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
    except ModuleNotFoundError:
        import torch.nn.functional as F
        samples = F.interpolate(samples, size=(height, width), mode="area")

    if maintain_aspect_ratio:
        target_size = max(width, height)
        if width != target_size or height != target_size:
            padded = torch.zeros(
                (samples.shape[0], samples.shape[1], target_size, target_size),
                dtype=samples.dtype,
                device=samples.device,
            )
            for c in range(samples.shape[1]):
                padded[:, c, :, :] = padding_color[c]
            x_offset = (target_size - width) // 2
            y_offset = (target_size - height) // 2
            padded[:, :, y_offset:y_offset + height, x_offset:x_offset + width] = samples
            samples = padded

    return samples.movedim(1, -1)[:, :, :, :3]


def _generate_style_instruction(
    style_strength: str,
    custom_instruction: str = "",
    style_weight: float = 1.0,
    num_images: int = 1,
) -> str:
    """
    Generate style instruction based on strength, weight, and number of images.
    """
    instruction = (custom_instruction or "").strip()
    if not instruction:
        if num_images > 1:
            instruction = SEMANTIC_STYLE_INSTRUCTIONS_MULTI.get(
                style_strength, SEMANTIC_STYLE_INSTRUCTIONS_MULTI["轻微"]
            )
        else:
            instruction = SEMANTIC_STYLE_INSTRUCTIONS_SINGLE.get(
                style_strength, SEMANTIC_STYLE_INSTRUCTIONS_SINGLE["轻微"]
            )

    if style_weight != 1.0:
        if style_weight < 0.5:
            prefix = "Very subtly "
        elif style_weight < 1.0:
            prefix = "Subtly "
        elif style_weight < 1.5:
            prefix = ""
        else:
            prefix = "Strongly "

        if prefix:
            instruction = prefix + instruction[0].lower() + instruction[1:]

    return instruction


class Krea2StyleSemanticConditioningImproved:
    DESCRIPTION = (
        "Krea2 风格语义条件节点（改进版）：支持多图参考、数值强度控制、宽高比保持。"
        "把参考图通过 Krea2/Qwen3-VL 的图像 token 路径送进 CONDITIONING。"
        "多张参考图各自独立编码，tokenizer 自动为每张图分配独立的 <|image_pad|> 槽位，实现多风格融合。"
        "它不修改 diffusion 模型，也不会注入 latent token。"
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP", _input_meta(
                    "CLIP",
                    "加载类型应为 krea2 的文本编码器。节点会调用 clip.tokenize(..., images=[参考图])。"
                )),
                "style_image": ("IMAGE", _input_meta(
                    "风格参考图",
                    "进入 Qwen3-VL 图像编码路径的参考图。适合提供色彩、材质、笔触、光影和整体视觉语言。"
                )),
                "prompt": ("STRING", _input_meta(
                    "正面提示词",
                    "目标图像的文字描述。参考图只作为风格语义输入，不建议在这里重复描述参考图主体。",
                    multiline=True,
                    dynamic_prompts=True
                )),
                "style_strength": (["轻微", "平衡", "强烈"], _input_meta(
                    "语义风格强度",
                    "通过提示词措辞控制参考图影响：轻微更保守，强烈更主动；不是采样器里的数学强度。",
                    default="轻微"
                )),
                "vision_resolution": ("INT", _input_meta(
                    "视觉编码分辨率",
                    "参考图送入 Qwen3-VL 前按总像素缩放到此边长平方。384 较稳，512 保留更多细节但更慢。",
                    default=384,
                    min=128,
                    max=1024,
                    step=32
                )),
            },
            "optional": {
                "custom_instruction": ("STRING", _input_meta(
                    "自定义风格指令",
                    "可选。留空使用上方强度预设；填写后会替代预设指令，仍会附加目标提示词。",
                    default="",
                    multiline=True
                )),
                "style_weight": ("FLOAT", _input_meta(
                    "风格权重",
                    "数值控制风格强度：0.0=几乎无影响，1.0=默认，2.0=极强影响。",
                    default=1.0,
                    min=0.0,
                    max=2.0,
                    step=0.1
                )),
                "maintain_aspect_ratio": ("BOOLEAN", _input_meta(
                    "保持宽高比",
                    "是否保持参考图宽高比，不足部分用黑色填充。",
                    default=True
                )),
                "style_image_2": ("IMAGE", _input_meta(
                    "风格参考图 2",
                    "第二张参考图（可选）。用于混合多种风格。"
                )),
                "style_image_3": ("IMAGE", _input_meta(
                    "风格参考图 3",
                    "第三张参考图（可选）。用于混合多种风格。"
                )),
            },
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("条件",)
    FUNCTION = "encode"
    CATEGORY = "luy/Krea2"

    def encode(
        self,
        clip,
        style_image,
        prompt,
        style_strength="轻微",
        vision_resolution=384,
        custom_instruction="",
        style_weight=1.0,
        maintain_aspect_ratio=True,
        style_image_2=None,
        style_image_3=None,
    ):
        # Collect all style images, splitting any batched tensors
        # so each individual image becomes a separate element.
        # This ensures the tokenizer creates one <|image_pad|> slot per image.
        raw_images = []
        for img in [style_image, style_image_2, style_image_3]:
            if img is not None:
                raw_images.extend(_split_image_batch(img))

        # Resize each individual image for the vision encoder
        processed_images = []
        for img in raw_images:
            processed = _resize_image_for_vision(
                img,
                vision_resolution,
                maintain_aspect_ratio=maintain_aspect_ratio
            )
            processed_images.append(processed)

        num_images = len(processed_images)

        # Generate instruction (multi-image aware)
        instruction = _generate_style_instruction(
            style_strength,
            custom_instruction,
            style_weight,
            num_images=num_images,
        )

        # Build per-image text labels so the model can reference each one
        image_ref_lines = []
        for i in range(num_images):
            image_ref_lines.append(f"Image {i + 1}:")
        image_ref_block = "\n".join(image_ref_lines)

        # The tokenizer template prepends <|vision_start|><|image_pad|><|vision_end|>
        # blocks before our text. The actual image data is injected into each
        # <|image_pad|> slot in order — one per element in processed_images.
        text = f"{instruction}\n\n{image_ref_block}\n\nTarget prompt: {prompt}"

        tokens = clip.tokenize(text, images=processed_images)

        return (clip.encode_from_tokens_scheduled(tokens),)


NODE_CLASS_MAPPINGS = {
    "Krea2StyleSemanticConditioningImproved": Krea2StyleSemanticConditioningImproved,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2StyleSemanticConditioningImproved": "Krea2 风格语义条件（改进版）",
}
