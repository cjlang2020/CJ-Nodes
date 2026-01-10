import torch
import comfy.model_management
import comfy.utils
import node_helpers

class VisClipCopyImageReference:
    """
    纯图片参考节点（兼容4/16通道VAE）
    适配SD1.5(4通道)和SDXL(16通道)，解决Latent维度不匹配问题
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "positive": ("CONDITIONING",),          # 正向提示词条件
                "negative": ("CONDITIONING",),          # 负向提示词条件
                "vae": ("VAE",),                        # VAE模型（自动适配4/16通道）
                "ref_image": ("IMAGE",),                # 参考图片（必填）
                "width": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 4096, "step": 8}),
                "reference_strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3.0, "step": 0.05}),
                "latent_blend": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("positive", "negative", "latent")
    CATEGORY = "conditioning/image_reference"
    FUNCTION = "execute"

    def execute(self, positive, negative, vae, ref_image, width, height, reference_strength=1.0, latent_blend=0.8):
        """
        核心修复：自动适配VAE通道数，解决维度不匹配问题
        """
        # 1. 预处理参考图片
        ref_image = ref_image[:1]  # 仅取第一张参考图
        ref_image_scaled = comfy.utils.common_upscale(
            ref_image.movedim(-1, 1),
            width, height,
            upscale_method="lanczos",
            crop="disabled"
        ).movedim(1, -1)

        # 2. 编码参考图为Latent，并获取通道数
        ref_latent = vae.encode(ref_image_scaled[:, :, :, :3])
        latent_channels = ref_latent.shape[1]  # 自动获取VAE通道数（4或16）

        # 3. 初始化基础Latent（关键：匹配参考Latent的通道数）
        device = ref_latent.device  # 统一设备，避免维度/设备不匹配
        base_latent = torch.zeros([
            1,                      # batch_size=1
            latent_channels,        # 自动适配4/16通道
            height // 8,
            width // 8
        ], device=device, dtype=ref_latent.dtype)

        # 4. 确保Latent尺寸完全匹配
        if ref_latent.shape[2:] != base_latent.shape[2:]:
            # 只缩放空间维度，保持通道数不变
            ref_latent = comfy.utils.common_upscale(
                ref_latent,
                base_latent.shape[3], base_latent.shape[2],
                upscale_method="bicubic",
                crop="center"
            )

        # 5. 参考强度+Latent融合（现在维度完全匹配）
        ref_latent = ref_latent * reference_strength
        blended_latent = base_latent * (1 - latent_blend) + ref_latent * latent_blend
        blended_latent = torch.clamp(blended_latent, -6, 6)

        # 6. 多维度注入参考特征
        positive = node_helpers.conditioning_set_values(
            positive, {"reference_latents": [blended_latent]}, append=True
        )
        positive = node_helpers.conditioning_set_values(
            positive, {"concat_latent": blended_latent}, append=True
        )
        positive = node_helpers.conditioning_set_values(
            positive, {"image_ref": blended_latent}, append=False
        )

        # 7. 负向条件处理
        negative = node_helpers.conditioning_set_values(
            negative, {
                "reference_latents": [torch.zeros_like(blended_latent)],
                "concat_latent": torch.zeros_like(blended_latent),
                "image_ref": torch.zeros_like(blended_latent)
            }, append=False
        )

        # 8. 输出融合后的Latent
        out_latent = {"samples": blended_latent}

        return (positive, negative, out_latent)