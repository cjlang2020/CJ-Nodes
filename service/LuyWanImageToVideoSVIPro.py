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
                io.Float.Input("target_photo_weight", default=8.0, min=0.0, max=20.0, step=0.1,display_name="尾帧全局强度(0~20)"),
                io.Float.Input("final_frame_strength", default=1.0, min=0.8, max=2.0, step=0.01,display_name="最后一帧强度(0.8~2)"),
                io.Float.Input("target_mask_strength", default=0.4, min=0.0, max=1.0, step=0.05,display_name="尾帧mask强度(0~1)"),
                io.Float.Input("target_start_ratio", default=0.5, min=0.2, max=0.8, step=0.05,display_name="尾帧开始过渡比例(0.2~0.8)"),
                io.Float.Input("anchor_strength", default=1.0, min=0.0, max=3.0, step=0.1,display_name="首帧参考强度(0~3)"),
                io.Float.Input("anchor_protect_ratio", default=0.4, min=0.1, max=0.6, step=0.05,display_name="首帧约束比(N%帧参考)"),
                io.Float.Input("anchor_decay_rate", default=0.90, min=0.0, max=0.95, step=0.01,display_name="首帧衰减率(0完全不参考，0.95缓慢衰减)"),
                io.Float.Input("anchor_global_weight", default=0.3, min=0.0, max=1.0, step=0.05,display_name="衔接帧全局强度(0~1)"),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, length,real_frame, motion_latent_count, anchor_samples, prev_samples=None, target_photo_samples=None, target_photo_weight=8.0, final_frame_strength=1.0, anchor_strength=1.0, anchor_protect_ratio=0.4, anchor_decay_rate=0.90, anchor_global_weight=0.3, target_mask_strength=0.4, target_start_ratio=0.5) -> io.NodeOutput:
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

        # 1. 处理anchor：动态衰减的全局参考（优化首帧衰减逻辑，解决2-5帧灰蒙蒙）
        anchor_latent_expanded = anchor_latent.repeat(1, 1, total_latents, 1, 1)
        anchor_weights = torch.ones(total_latents, device=device, dtype=dtype) * anchor_strength

        if total_latents > protect_frames:
            decay_frames = total_latents - protect_frames
            decay_weights = anchor_strength * (anchor_decay_rate ** torch.arange(1, decay_frames + 1, device=device, dtype=dtype))

            # 关键修复：第2-5帧（索引1-4）强制保留50%的首帧强度，避免断崖式下降
            early_frames = min(4, decay_frames)  # 覆盖第2-5帧
            if early_frames > 0:
                # 前4帧衰减放缓，保留基础强度
                early_decay = anchor_strength * 0.5 * (anchor_decay_rate ** torch.arange(1, early_frames + 1, device=device, dtype=dtype))
                decay_weights[:early_frames] = early_decay

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

        # 3. 处理target_photo_samples：有则约束尾帧，无则完全放开（优化尾帧闪烁）
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

            # 重构target权重逻辑 - 平滑过渡版本
            current_total = image_cond_latent.shape[2]
            target_start_frame = int(current_total * target_start_ratio)
            target_start_frame = max(1, min(target_start_frame, current_total - 2))

            # 初始化target权重
            time_weights = torch.zeros(current_total, device=device, dtype=dtype)

            # 权重渐变：使用平滑的非线性过渡，避免突变
            if current_total > target_start_frame:
                transition_frames = current_total - target_start_frame
                # 使用更平滑的非线性曲线
                base_weights = torch.linspace(0.0, 1.0, transition_frames, device=device, dtype=dtype)
                base_weights = torch.pow(base_weights, 0.6)

                # 计算最终帧目标权重
                final_target_weight = final_frame_strength * target_photo_weight
                # 对最后20%帧做平滑过渡
                final_20_percent = max(2, int(current_total * 0.2))
                final_start_idx = current_total - final_20_percent

                # 主过渡段（target_start_frame 到 final_start_idx）
                main_transition_frames = final_start_idx - target_start_frame
                if main_transition_frames > 0:
                    time_weights[target_start_frame:final_start_idx] = base_weights[:main_transition_frames] * target_photo_weight

                # 最后20%帧的平滑提升
                if final_20_percent > 0 and final_start_idx > target_start_frame:
                    start_weight = base_weights[main_transition_frames-1] * target_photo_weight if main_transition_frames > 0 else 0.0
                    tail_weights = start_weight + (final_target_weight - start_weight) * torch.pow(torch.linspace(0.0, 1.0, final_20_percent), 0.7)
                    time_weights[final_start_idx:] = tail_weights

            # 权重裁剪，确保不超过合理范围
            time_weights = torch.clamp(time_weights, 0.0, target_photo_weight * 1.2)
            time_weights = time_weights.reshape(1, 1, current_total, 1, 1)

            # 加权融合优化：添加epsilon避免除零，增加微小噪声防灰屏
            epsilon = 1e-6
            total_weight = 1.0 + time_weights + epsilon
            base_weight = 1.0 / total_weight
            target_weight = time_weights / total_weight

            noise = torch.randn_like(base_latent) * 0.001
            image_cond_latent = (base_latent + noise) * base_weight + target_latent_expanded * target_weight

            # 最后帧额外平滑：与前一帧做插值
            if current_total > 1:
                last_frame = image_cond_latent[:, :, -1:, :, :]
                prev_frame = image_cond_latent[:, :, -2:-1, :, :]
                smooth_last_frame = last_frame * 0.95 + prev_frame * 0.05
                image_cond_latent[:, :, -1:, :, :] = smooth_last_frame
        else:
            # 无尾帧时，完全放开约束
            image_cond_latent = base_latent
            anchor_global_weight = 0.1  # 大幅降低首帧全局约束

        # 4. 融合anchor全局参考
        if image_cond_latent.shape != anchor_latent_expanded.shape:
            anchor_latent_expanded = anchor_latent_expanded[:, :, :image_cond_latent.shape[2], :, :]
        image_cond_latent = image_cond_latent * (1 - anchor_global_weight) + anchor_latent_expanded * anchor_global_weight

        # 5. 重构mask逻辑（优化第6帧突变问题）
        current_total = image_cond_latent.shape[2]
        mask = torch.ones((1, 1, current_total, H, W), device=device, dtype=dtype)

        # 首帧约束
        if prev_samples is not None and motion_latent_count > 0:
            mask[:, :, :1] = 0.1  # 有上一段视频时，首帧轻微约束
        else:
            mask[:, :, :1] = 0.4  # 提升起始mask值，减少突变

        # 保护帧内约束（弱化约束，让提示词主导）
        current_protect_frames = int(current_total * anchor_protect_ratio)
        current_protect_frames = max(1, min(current_protect_frames, current_total - 1))
        if current_protect_frames > 1:
            start_mask = 0.4 if (prev_samples is not None and motion_latent_count > 0) else 0.5
            # 权重从低到高平滑过渡
            mask_weights = torch.linspace(start_mask, 0.95, current_protect_frames - 1, device=device, dtype=dtype)
            mask_weights = mask_weights.reshape(1, 1, -1, 1, 1)
            mask[:, :, 1:current_protect_frames] = mask_weights

        # 保护帧后mask处理（解决第6帧突变）
        if current_protect_frames < current_total:
            if target_applied:
                # 保护帧最后1帧（第6帧）做平滑过渡，避免直接跳到1.0
                if current_protect_frames >=1:
                    mask[:, :, current_protect_frames:current_protect_frames+1] = 0.98
                # 保护帧后到尾帧前的mask
                mask_end_idx = current_total - max(2, int(current_total * 0.2)) if current_total > 2 else current_protect_frames + 1
                if current_protect_frames +1 < mask_end_idx:
                    mask[:, :, current_protect_frames+1:mask_end_idx] = 1.0

                # 尾帧mask平滑过渡
                final_20_percent = max(2, int(current_total * 0.2))
                mask_weights_tail = torch.linspace(0.95, target_mask_strength, final_20_percent, device=device, dtype=dtype)
                mask_weights_tail = 0.95 - (0.95 - target_mask_strength) * torch.pow(torch.linspace(0.0, 1.0, final_20_percent), 0.8)
                mask_weights_tail = mask_weights_tail.reshape(1, 1, -1, 1, 1)
                mask[:, :, -final_20_percent:] = mask_weights_tail
            else:
                # 无尾帧时，保护帧最后1帧平滑过渡
                if current_protect_frames >=1:
                    mask[:, :, current_protect_frames:current_protect_frames+1] = 0.98
                mask[:, :, current_protect_frames+1:] = 1.0

        # 注入约束到正负条件
        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": image_cond_latent, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": image_cond_latent, "concat_mask": mask})

        # 构建输出latent
        out_latent = {}
        out_latent["samples"] = empty_latent
        return io.NodeOutput(positive, negative, out_latent)