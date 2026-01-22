import node_helpers
import comfy.latent_formats
import torch
from nodes import MAX_RESOLUTION
from comfy.comfy_types.node_typing import IO
from comfy_api.latest import io
from comfy import model_management

class LuyWanImageToVideoSVIPro(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="LuyWanImageToVideoSVIPro",
            category="luy",
            inputs=[
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Int.Input("length", default=81, min=1, max=MAX_RESOLUTION, step=4),
                io.Latent.Input("anchor_samples"),
                io.Latent.Input("prev_samples", optional=True),
                io.Int.Input("motion_latent_count", default=1, min=0, max=128, step=1),
                io.Latent.Input("target_photo_samples", optional=True),
                io.Float.Input("target_photo_weight", default=1.0, min=0.0, max=10.0, step=0.1),
                io.Float.Input("final_frame_strength", default=1.0, min=0.8, max=1.0, step=0.01),
                io.Float.Input("anchor_strength", default=2.0, min=1.0, max=5.0, step=0.1),
                io.Float.Input("anchor_protect_ratio", default=0.5, min=0.2, max=0.8, step=0.05),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, length, motion_latent_count, anchor_samples, prev_samples=None, target_photo_samples=None, target_photo_weight=1.0, final_frame_strength=1.0, anchor_strength=2.0, anchor_protect_ratio=0.5) -> io.NodeOutput:
        anchor_latent = anchor_samples["samples"].clone()

        B, C, T, H, W = anchor_latent.shape
        total_latents = (length - 1) // 4 + 1
        empty_latent = torch.zeros([B, 16, total_latents, H, W], device=model_management.intermediate_device())

        device = anchor_latent.device
        dtype = anchor_latent.dtype

        anchor_latent = anchor_latent * anchor_strength

        if prev_samples is None or motion_latent_count == 0:
            padding_size = total_latents - anchor_latent.shape[2]
            image_cond_latent = anchor_latent
        else:
            motion_latent = prev_samples["samples"][:, :, -motion_latent_count:].clone()
            motion_latent = motion_latent * 0.8
            padding_size = total_latents - anchor_latent.shape[2] - motion_latent.shape[2]
            image_cond_latent = torch.cat([anchor_latent, motion_latent], dim=2)

        padding = torch.zeros(1, C, padding_size, H, W, dtype=dtype, device=device)
        padding = comfy.latent_formats.Wan21().process_out(padding)
        image_cond_latent = torch.cat([image_cond_latent, padding], dim=2)

        if target_photo_samples is not None:
            target_latent = target_photo_samples["samples"].clone()
            if target_latent.shape[2] > 1:
                target_latent = target_latent[:, :, 0:1, :, :]
            target_latent = target_latent.to(device=device, dtype=dtype)
            if target_latent.shape[1] != C:
                target_latent = target_latent.repeat(1, C // target_latent.shape[1], 1, 1, 1)

            protect_frames = int(total_latents * anchor_protect_ratio)
            time_weights = torch.zeros(total_latents, device=device, dtype=dtype)
            time_weights[protect_frames:] = torch.linspace(0.0, target_photo_weight, total_latents - protect_frames, device=device, dtype=dtype)
            time_weights[-1] = final_frame_strength * target_photo_weight
            final_10_percent = max(1, int(total_latents * 0.1))
            time_weights[-final_10_percent:] = final_frame_strength * target_photo_weight

            time_weights = time_weights.reshape(1, 1, total_latents, 1, 1)

            target_latent_expanded = target_latent.repeat(1, 1, total_latents, 1, 1)
            norm_time_weights = torch.clamp(time_weights, 0.0, target_photo_weight) / target_photo_weight
            image_cond_latent = image_cond_latent * (1 - norm_time_weights) + target_latent_expanded * norm_time_weights

        mask = torch.ones((1, 1, empty_latent.shape[2], H, W), device=device, dtype=dtype)
        mask[:, :, :1] = 0.0

        protect_frames = int(total_latents * anchor_protect_ratio)
        mask[:, :, 1:protect_frames] = 1.5
        mask[:, :, -1:] = 1.2

        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": image_cond_latent, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": image_cond_latent, "concat_mask": mask})

        out_latent = {}
        out_latent["samples"] = empty_latent
        return io.NodeOutput(positive, negative, out_latent)