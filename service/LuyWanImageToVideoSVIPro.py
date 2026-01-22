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
            description="基于SVI的图像转视频节点，支持参考图片、上一段视频latent和尾帧图片的多重约束。没有上一段视频时，anchor_samples就是首帧；无尾帧时画面根据提示词自由发挥",
            inputs=[
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Int.Input("length", default=81, min=1, max=MAX_RESOLUTION, step=4),
                io.Int.Input("real_frame", default=4, min=1, max=8, step=1,display_name="每latent帧实际对应视频帧数，即有效帧间隔"),
                io.Latent.Input("anchor_samples",display_name="参考照片"),
                io.Latent.Input("prev_samples", optional=True,display_name="上一段Latent"),
                io.Int.Input("motion_latent_count", default=1, min=0, max=128, step=1,display_name="上一段Latent参考帧数"),
                io.Latent.Input("target_photo_samples", optional=True,display_name="尾帧图片"),
                io.Float.Input("target_photo_weight", default=5.0, min=0.0, max=20.0, step=0.1,display_name="尾帧全局强度(0~20)"),
                io.Float.Input("final_frame_strength", default=1.0, min=0.8, max=2.0, step=0.01,display_name="最后一帧强度(0.8~2)"),
                io.Float.Input("target_mask_strength", default=0.3, min=0.0, max=1.0, step=0.05,display_name="尾帧mask强度(0~1)"),
                io.Float.Input("target_start_ratio", default=0.5, min=0.2, max=0.8, step=0.05,display_name="尾帧开始过渡比例(0.2~0.8)"),
                io.Float.Input("anchor_strength", default=1.2, min=0.0, max=3.0, step=0.1,display_name="首帧参考强度(0~3)"),
                io.Float.Input("anchor_protect_ratio", default=0.3, min=0.1, max=0.6, step=0.05,display_name="首帧约束比(N%帧参考)"),
                io.Float.Input("anchor_decay_rate", default=0.8, min=0.0, max=0.95, step=0.01,display_name="首帧衰减率(0完全不参考，0.95缓慢衰减)"),
                io.Float.Input("anchor_global_weight", default=0.5, min=0.0, max=1.0, step=0.05,display_name="衔接帧全局强度(0~1)"),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, length,real_frame, motion_latent_count, anchor_samples, prev_samples=None, target_photo_samples=None, target_photo_weight=5.0, final_frame_strength=1.0, anchor_strength=1.2, anchor_protect_ratio=0.3, anchor_decay_rate=0.8, anchor_global_weight=0.5, target_mask_strength=0.3, target_start_ratio=0.5) -> io.NodeOutput:
        # 克隆参考图latent，避免原数据被修改
        anchor_latent = anchor_samples["samples"].clone()
        B, C, T, H, W = anchor_latent.shape
        # 计算总latent帧数（按real_frame帧步长换算）
        total_latents = (length - 1) // real_frame + 1
        # 初始化空latent作为输出基底
        empty_latent = torch.zeros([B, 16, total_latents, H, W], device=model_management.intermediate_device())

        device = anchor_latent.device
        dtype = anchor_latent.dtype

        # ========== 边界保护 ==========
        protect_frames = int(total_latents * anchor_protect_ratio)
        protect_frames = max(1, min(protect_frames, total_latents - 1))

        # 1. 处理anchor：动态衰减的全局参考
        anchor_latent_expanded = anchor_latent.repeat(1, 1, total_latents, 1, 1)
        anchor_weights = torch.ones(total_latents, device=device, dtype=dtype) * anchor_strength

        if total_latents > protect_frames:
            decay_frames = total_latents - protect_frames
            decay_weights = anchor_strength * (anchor_decay_rate ** torch.arange(1, decay_frames + 1, device=device, dtype=dtype))
            anchor_weights[protect_frames:] = decay_weights

        anchor_weights = anchor_weights.reshape(1, 1, total_latents, 1, 1)
        anchor_latent_expanded = anchor_latent_expanded * anchor_weights

        # 2. 处理prev_samples：首帧逻辑
        if prev_samples is not None and motion_latent_count > 0:
            motion_latent = prev_samples["samples"][:, :, -motion_latent_count:].clone()
            motion_latent = motion_latent * 0.8
            padding_size = max(0, total_latents - motion_latent.shape[2])
            image_cond_latent = motion_latent
        else:
            padding_size = max(0, total_latents - anchor_latent.shape[2])
            image_cond_latent = anchor_latent

        # 填充空白latent
        if padding_size > 0:
            padding = torch.zeros(1, C, padding_size, H, W, dtype=dtype, device=device)
            padding = comfy.latent_formats.Wan21().process_out(padding)
            image_cond_latent = torch.cat([image_cond_latent, padding], dim=2)
        if image_cond_latent.shape[2] > total_latents:
            image_cond_latent = image_cond_latent[:, :, :total_latents, :, :]

        # 保存原始主体帧（prev/anchor），用于后续融合
        base_latent = image_cond_latent.clone()

        # 3. 处理target_photo_samples：有则约束尾帧，无则完全放开
        target_applied = False
        if target_photo_samples is not None:
            target_applied = True
            target_latent = target_photo_samples["samples"].clone()
            # 确保target是单帧
            if target_latent.shape[2] > 1:
                target_latent = target_latent[:, :, 0:1, :, :]
            target_latent = target_latent.to(device=device, dtype=dtype)
            # 匹配通道数
            if target_latent.shape[1] != C:
                target_latent = target_latent.repeat(1, C // target_latent.shape[1], 1, 1, 1)
            # 扩展target到全序列
            target_latent_expanded = target_latent.repeat(1, 1, image_cond_latent.shape[2], 1, 1)

            # 重构target权重逻辑
            current_total = image_cond_latent.shape[2]
            target_start_frame = int(current_total * target_start_ratio)
            target_start_frame = max(1, min(target_start_frame, current_total - 2))

            # 初始化target权重
            time_weights = torch.zeros(current_total, device=device, dtype=dtype)

            # 权重渐变：从target_start_frame开始，快速上升到target_photo_weight
            if current_total > target_start_frame:
                transition_frames = current_total - target_start_frame
                base_weights = torch.linspace(0.0, 1.0, transition_frames, device=device, dtype=dtype)
                base_weights = torch.pow(base_weights, 0.8)
                time_weights[target_start_frame:] = base_weights * target_photo_weight

            # 最终帧强制拉满强度
            final_frame_idx = current_total - 1
            time_weights[final_frame_idx] = final_frame_strength * target_photo_weight
            # 最后20%帧固定最大权重
            final_20_percent = max(2, int(current_total * 0.2))
            time_weights[-final_20_percent:] = final_frame_strength * target_photo_weight

            # 重塑权重维度
            time_weights = time_weights.reshape(1, 1, current_total, 1, 1)
            time_weights = torch.clamp(time_weights, 0.0, target_photo_weight)

            # 加权融合target和base_latent
            total_weight = 1.0 + time_weights
            base_weight = 1.0 / total_weight
            target_weight = time_weights / total_weight
            image_cond_latent = base_latent * base_weight + target_latent_expanded * target_weight
        else:
            # ========== 核心修改：无尾帧时，完全放开约束 ==========
            # 1. 直接使用base_latent，不做任何尾帧相关融合
            image_cond_latent = base_latent
            # 2. 降低anchor_global_weight的影响，让提示词主导（原逻辑是强制融合anchor）
            anchor_global_weight = 0.1  # 大幅降低首帧全局约束，让提示词发挥作用

        # 4. 融合anchor全局参考（无尾帧时已降低anchor权重）
        if image_cond_latent.shape != anchor_latent_expanded.shape:
            anchor_latent_expanded = anchor_latent_expanded[:, :, :image_cond_latent.shape[2], :, :]
        image_cond_latent = image_cond_latent * (1 - anchor_global_weight) + anchor_latent_expanded * anchor_global_weight

        # 5. 重构mask逻辑
        current_total = image_cond_latent.shape[2]
        mask = torch.ones((1, 1, current_total, H, W), device=device, dtype=dtype)

        # 首帧约束（仅保留基础首帧约束，保证首帧不跑偏）
        if prev_samples is not None and motion_latent_count > 0:
            mask[:, :, :1] = 0.1  # 有上一段视频时，首帧轻微约束
        else:
            mask[:, :, :1] = 0.2  # 无衔接时，首帧轻度约束（避免完全跑偏）

        # 保护帧内约束（弱化约束，让提示词主导）
        current_protect_frames = int(current_total * anchor_protect_ratio)
        current_protect_frames = max(1, min(current_protect_frames, current_total - 1))
        if current_protect_frames > 1:
            start_mask = 0.2 if (prev_samples is not None and motion_latent_count > 0) else 0.3
            # 权重从低到高更快，快速放开约束
            mask_weights = torch.linspace(start_mask, 0.95, current_protect_frames - 1, device=device, dtype=dtype)
            mask_weights = mask_weights.reshape(1, 1, -1, 1, 1)
            mask[:, :, 1:current_protect_frames] = mask_weights

        # ========== 核心修改：无尾帧时，保护帧后完全放开mask约束 ==========
        if current_protect_frames < current_total:
            if target_applied:
                # 有尾帧时保留原逻辑
                mask[:, :, current_protect_frames:] = 1.0
            else:
                # 无尾帧时，mask设为1.0（完全放开），让模型按提示词生成
                mask[:, :, current_protect_frames:] = 1.0

        # 仅在有尾帧时优化尾帧mask
        if target_applied and current_total >= 1:
            final_20_percent = max(2, int(current_total * 0.2))
            mask_weights_tail = torch.linspace(0.8, target_mask_strength, final_20_percent, device=device, dtype=dtype)
            mask_weights_tail = mask_weights_tail.reshape(1, 1, -1, 1, 1)
            mask[:, :, -final_20_percent:] = mask_weights_tail

        # 注入约束到正负条件
        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": image_cond_latent, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": image_cond_latent, "concat_mask": mask})

        # 构建输出latent
        out_latent = {}
        out_latent["samples"] = empty_latent
        return io.NodeOutput(positive, negative, out_latent)