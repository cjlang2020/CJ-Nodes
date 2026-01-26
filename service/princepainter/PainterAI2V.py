import math
import nodes
import node_helpers
import torch
import comfy.model_management
import comfy.utils
import comfy.latent_formats
import comfy.clip_vision
import json
import numpy as np
from typing import Tuple, TypedDict
from typing_extensions import override
from comfy_api.latest import ComfyExtension, io
import logging

class PainterAI2V(io.ComfyNode):
    """Painted InfiniteTalk for Wan2.2 dual-model with adjustable FPS sync and first/last frame support"""
    
    class DCValues(TypedDict):
        mode: str
        audio_encoder_output_2: io.AudioEncoderOutput.Type
        mask_1: io.Mask.Type
        mask_2: io.Mask.Type

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="PainterAI2V",
            category="conditioning/video_models",
            inputs=[
                io.DynamicCombo.Input("mode", options=[
                    io.DynamicCombo.Option("single_speaker", []),
                    io.DynamicCombo.Option("two_speakers", [
                        io.AudioEncoderOutput.Input("audio_encoder_output_2", optional=True),
                        io.Mask.Input("mask_1", optional=True, tooltip="Mask for the first speaker, required if using two audio inputs."),
                        io.Mask.Input("mask_2", optional=True, tooltip="Mask for the second speaker, required if using two audio inputs."),
                    ]),
                ]),
                io.Model.Input("model_high_noise", display_name="high_model", tooltip="Wan2.2 high noise model (steps 0-2)"),
                io.Model.Input("model_low_noise", display_name="low_model", tooltip="Wan2.2 low noise model (steps 2-4)"),
                io.ModelPatch.Input("model_patch", tooltip="InfiniteTalk patch model"),
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Vae.Input("vae"),
                io.Int.Input("width", default=832, min=16, max=nodes.MAX_RESOLUTION, step=16),
                io.Int.Input("height", default=480, min=16, max=nodes.MAX_RESOLUTION, step=16),
                io.Int.Input("length", default=81, min=1, max=nodes.MAX_RESOLUTION, step=4),
                io.Float.Input("video_fps", default=20.0, min=1.0, max=120.0, step=0.01, tooltip="Video output frame rate - audio lip-sync will match this"),
                io.ClipVisionOutput.Input("clip_vision_output", optional=True),
                io.Image.Input("start_image", optional=True),
                io.Image.Input("end_image", optional=True),
                io.AudioEncoderOutput.Input("audio_encoder_output_1", display_name="audio_encoder"),
                io.Int.Input("motion_frame", default=9, min=1, max=33, step=1, tooltip="Number of previous frames to use as motion context."),
                io.Float.Input("audio_scale", default=1.0, min=-10.0, max=10.0, step=0.01),
                io.Image.Input("previous_frames", optional=True),
            ],
            outputs=[
                io.Model.Output(display_name="high_model"),
                io.Model.Output(display_name="low_model"),
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
                io.Int.Output(display_name="trim_image"),
            ],
        )

    @classmethod
    def execute(cls, mode: DCValues, model_high_noise, model_low_noise, model_patch, positive, negative, vae, width, height, length, video_fps, audio_encoder_output_1, motion_frame,
                start_image=None, end_image=None, previous_frames=None, audio_scale=None, clip_vision_output=None, audio_encoder_output_2=None, mask_1=None, mask_2=None) -> io.NodeOutput:

        # Validate inputs
        if previous_frames is not None and previous_frames.shape[0] < motion_frame:
            raise ValueError("Not enough previous frames provided.")

        if mode["mode"] == "two_speakers":
            audio_encoder_output_2 = mode["audio_encoder_output_2"]
            mask_1 = mode["mask_1"]
            mask_2 = mode["mask_2"]

        if audio_encoder_output_2 is not None:
            if mask_1 is None or mask_2 is None:
                raise ValueError("Masks must be provided if two audio encoder outputs are used.")

        ref_masks = None
        if mask_1 is not None and mask_2 is not None:
            if audio_encoder_output_2 is None:
                raise ValueError("Second audio encoder output must be provided if two masks are used.")
            ref_masks = torch.cat([mask_1, mask_2])

        # Prepare latent
        latent = torch.zeros([1, 16, ((length - 1) // 4) + 1, height // 8, width // 8], device=comfy.model_management.intermediate_device())
        
        # Process start and end images
        concat_latent_image = None
        if start_image is not None:
            start_image = comfy.utils.common_upscale(start_image[:length].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
        if end_image is not None:
            end_image = comfy.utils.common_upscale(end_image[-length:].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)

        # Create image tensor with middle frames as gray
        image = torch.ones((length, height, width, 3), device=comfy.model_management.intermediate_device(), dtype=torch.float32) * 0.5
        mask = torch.ones((1, 1, latent.shape[2] * 4, latent.shape[-2], latent.shape[-1]), device=image.device, dtype=image.dtype)

        if start_image is not None:
            image[:start_image.shape[0]] = start_image
            mask[:, :, :start_image.shape[0] + 3] = 0.0

        if end_image is not None:
            image[-end_image.shape[0]:] = end_image
            mask[:, :, -end_image.shape[0]:] = 0.0

        # Encode and set conditioning
        concat_latent_image = vae.encode(image[:, :, :, :3])
        mask = mask.view(1, mask.shape[2] // 4, 4, mask.shape[3], mask.shape[4]).transpose(1, 2)
        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": concat_latent_image, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": concat_latent_image, "concat_mask": mask})

        # Process clip vision
        if clip_vision_output is not None:
            positive = node_helpers.conditioning_set_values(positive, {"clip_vision_output": clip_vision_output})
            negative = node_helpers.conditioning_set_values(negative, {"clip_vision_output": clip_vision_output})

        # Process audio
        encoded_audio_list = []
        seq_lengths = []

        for audio_encoder_output in [audio_encoder_output_1, audio_encoder_output_2]:
            if audio_encoder_output is None:
                continue
            all_layers = audio_encoder_output["encoded_audio_all_layers"]
            encoded_audio = torch.stack(all_layers, dim=0).squeeze(1)[1:]  # shape: [num_layers, T, 512]
            
            # KEY FIX: Use dynamic video_fps instead of hardcoded 25
            encoded_audio = cls.linear_interpolation(encoded_audio, input_fps=50, output_fps=video_fps).movedim(0, 1) # shape: [T, num_layers, 512]
            encoded_audio_list.append(encoded_audio)
            seq_lengths.append(encoded_audio.shape[0])

        # Pad / combine audio
        multi_audio_type = "add"
        if len(encoded_audio_list) > 1:
            if multi_audio_type == "para":
                max_len = max(seq_lengths)
                padded = []
                for emb in encoded_audio_list:
                    if emb.shape[0] < max_len:
                        pad = torch.zeros(max_len - emb.shape[0], *emb.shape[1:], dtype=emb.dtype, device=emb.device)
                        emb = torch.cat([emb, pad], dim=0)
                    padded.append(emb)
                encoded_audio_list = padded
            elif multi_audio_type == "add":
                total_len = sum(seq_lengths)
                full_list = []
                offset = 0
                for emb, seq_len in zip(encoded_audio_list, seq_lengths):
                    full = torch.zeros(total_len, *emb.shape[1:], dtype=emb.dtype, device=emb.device)
                    full[offset:offset+seq_len] = emb
                    full_list.append(full)
                    offset += seq_len
                encoded_audio_list = full_list

        # Process masks
        token_ref_target_masks = None
        if ref_masks is not None:
            token_ref_target_masks = torch.nn.functional.interpolate(
                ref_masks.unsqueeze(0), size=(latent.shape[-2] // 2, latent.shape[-1] // 2), mode='nearest')[0]
            token_ref_target_masks = (token_ref_target_masks > 0).view(token_ref_target_masks.shape[0], -1)

        # Process motion frames
        if previous_frames is not None:
            motion_frames = comfy.utils.common_upscale(previous_frames[-motion_frame:].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
            frame_offset = previous_frames.shape[0] - motion_frame
            audio_start = frame_offset
            audio_end = audio_start + length
            motion_frames_latent = vae.encode(motion_frames[:, :, :, :3])
            trim_image = motion_frame
        else:
            audio_start = trim_image = 0
            audio_end = length
            motion_frames_latent = concat_latent_image[:, :, :1]

        # Patch both models
        def patch_model(model, model_name):
            model_patched = model.clone()
            
            # Project audio features
            from comfy.ldm.wan.model_multitalk import project_audio_features
            audio_embed = project_audio_features(model_patch.model.audio_proj, encoded_audio_list, audio_start, audio_end).to(model_patched.model_dtype())
            model_patched.model_options["transformer_options"]["audio_embeds"] = audio_embed

            # Add outer sample wrapper
            from comfy.ldm.wan.model_multitalk import InfiniteTalkOuterSampleWrapper
            model_patched.add_wrapper_with_key(
                comfy.patcher_extension.WrappersMP.OUTER_SAMPLE,
                f"infinite_talk_outer_sample_{model_name}",
                InfiniteTalkOuterSampleWrapper(
                    motion_frames_latent,
                    model_patch,
                    is_extend=previous_frames is not None,
                ))
            
            # Add cross-attention patch
            from comfy.ldm.wan.model_multitalk import MultiTalkCrossAttnPatch
            model_patched.set_model_patch(MultiTalkCrossAttnPatch(model_patch, audio_scale), "attn2_patch")
            
            # Add attention map patch if masks provided
            if token_ref_target_masks is not None:
                from comfy.ldm.wan.model_multitalk import MultiTalkGetAttnMapPatch
                model_patched.set_model_patch(MultiTalkGetAttnMapPatch(token_ref_target_masks), "attn1_patch")
                
            return model_patched

        # Patch both high and low noise models
        model_high_noise_patched = patch_model(model_high_noise, "high_noise")
        model_low_noise_patched = patch_model(model_low_noise, "low_noise")

        out_latent = {}
        out_latent["samples"] = latent
        return io.NodeOutput(model_high_noise_patched, model_low_noise_patched, positive, negative, out_latent, trim_image)

    @staticmethod
    def linear_interpolation(features, input_fps, output_fps):
        """Interpolate audio features from input_fps to output_fps"""
        features = features.transpose(1, 2).to(torch.float32)  # [num_layers, 512, T]
        output_len = int(features.shape[2] / float(input_fps) * output_fps)
        output_features = torch.nn.functional.interpolate(
            features, size=output_len, align_corners=True, mode='linear')
        return output_features.transpose(1, 2).to(features.dtype)  # [num_layers, output_len, 512]


class PainterAI2VExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PainterAI2V]

async def comfy_entrypoint() -> PainterAI2VExtension:
    return PainterAI2VExtension()
