import torch
import comfy.model_management
import comfy.utils
import node_helpers
from comfy_api.latest import io, ComfyExtension
from typing_extensions import override

class FirstEndFrameDeal(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="FirstEndFrameDeal",
            category="luy",
            inputs=[
                # 输入ID改为 unique 名称（避免和输出重复）
                io.Conditioning.Input("pos_input"),
                io.Conditioning.Input("neg_input"),
                io.Vae.Input("vae"),
                io.Int.Input("width", default=832, min=16, max=4096, step=16),
                io.Int.Input("height", default=480, min=16, max=4096, step=16),
                io.Int.Input("length", default=81, min=1, max=4096, step=4),
                io.Float.Input("motion_amplitude", default=1.15, min=1.0, max=2.0, step=0.05),
                io.Image.Input("start_image"),
                io.Image.Input("end_image"),
            ],
            outputs=[
                # 输出ID保持原有名称
                io.Conditioning.Output("positive"),
                io.Conditioning.Output("negative"),
                io.Latent.Output("latent"),
            ]
        )

    @classmethod
    def execute(cls, pos_input, neg_input, vae, width, height, length, motion_amplitude, start_image, end_image) -> io.NodeOutput:
        # 1. 零latent初始化（4步LoRA核心）
        latent_shape = (1, 16, ((length - 1) // 4) + 1, height // 8, width // 8)
        latent = torch.zeros(latent_shape, device=comfy.model_management.intermediate_device())

        # 2. 首尾帧预处理
        # 首帧
        start_img = start_image[:1]
        start_img = comfy.utils.common_upscale(start_img.movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
        # 末帧
        end_img = end_image[:1]
        end_img = comfy.utils.common_upscale(end_img.movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)

        # 3. 首尾帧线性过渡序列
        alpha = torch.linspace(0.0, 1.0, length, device=start_img.device).view(length, 1, 1, 1)
        image_seq = (1 - alpha) * start_img + alpha * end_img
        image_seq[0] = start_img[0]  # 强制首帧保真
        image_seq[-1] = end_img[0]   # 强制末帧保真

        # 4. VAE编码 + mask构建
        concat_latent = vae.encode(image_seq[:, :, :, :3])
        # mask：首尾帧强约束（0），中间帧软约束（0.2）
        mask = torch.ones((1, 1, latent_shape[2], concat_latent.shape[-2], concat_latent.shape[-1]), device=start_img.device)
        mask[:, :, 0] = 0.0  # 首帧
        mask[:, :, -1] = 0.0 # 末帧
        mask = mask * 0.2     # 中间帧软约束强度

        # 5. 运动增强（PainterI2V核心算法）
        if motion_amplitude > 1.0:
            base_latent = concat_latent[:, :, 0:1]
            other_latents = concat_latent[:, :, 1:]
            diff = other_latents - base_latent
            diff_centered = diff - diff.mean(dim=(1,3,4), keepdim=True)
            scaled_latent = base_latent + diff_centered * motion_amplitude + diff.mean(dim=(1,3,4), keepdim=True)
            concat_latent = torch.cat([base_latent, torch.clamp(scaled_latent, -6, 6)], dim=2)

        # 6. 注入条件 + 参考帧增强（注意输入变量名改为pos_input/neg_input）
        positive = node_helpers.conditioning_set_values(pos_input, {
            "concat_latent_image": concat_latent,
            "concat_mask": mask,
            "reference_latents": [vae.encode(start_img[:, :, :, :3]), vae.encode(end_img[:, :, :, :3])]
        }, append=True)
        negative = node_helpers.conditioning_set_values(neg_input, {
            "concat_latent_image": concat_latent,
            "concat_mask": mask,
            "reference_latents": [torch.zeros_like(vae.encode(start_img[:, :, :, :3])), torch.zeros_like(vae.encode(end_img[:, :, :, :3]))]
        }, append=True)

        # 7. 输出零latent
        return io.NodeOutput(positive, negative, {"samples": latent})

class FirstEndFrameDealExtension(ComfyExtension):
    @override
    async def get_node_list(self):
        return [FirstEndFrameDeal]

async def comfy_entrypoint():
    return FirstEndFrameDealExtension()