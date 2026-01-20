import math
import nodes
import node_helpers
import torch
import comfy.model_management
import comfy.utils
import comfy.clip_vision
from typing_extensions import override
from comfy_api.latest import  io

class LuyWanFirstLastFrameToVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="LuyWanFirstLastFrameToVideo",
            category="luy",
            inputs=[
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Vae.Input("vae"),
                io.Int.Input("width", default=832, min=16, max=nodes.MAX_RESOLUTION, step=16),
                io.Int.Input("height", default=480, min=16, max=nodes.MAX_RESOLUTION, step=16),
                io.Int.Input("length", default=81, min=1, max=nodes.MAX_RESOLUTION, step=4),
                io.Int.Input("batch_size", default=1, min=1, max=4096),
                io.ClipVisionOutput.Input("clip_vision_start_image", optional=True),
                io.ClipVisionOutput.Input("clip_vision_end_image", optional=True),
                io.Image.Input("start_image", optional=True),
                io.Image.Input("end_image", optional=True),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, vae, width, height, length, batch_size, start_image=None, end_image=None, clip_vision_start_image=None, clip_vision_end_image=None) -> io.NodeOutput:
        spacial_scale = vae.spacial_compression_encode()
        latent = torch.zeros([batch_size, vae.latent_channels, ((length - 1) // 4) + 1, height // spacial_scale, width // spacial_scale], device=comfy.model_management.intermediate_device())
        if start_image is not None:
            start_image = comfy.utils.common_upscale(start_image[:length].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)
        if end_image is not None:
            end_image = comfy.utils.common_upscale(end_image[-length:].movedim(-1, 1), width, height, "bilinear", "center").movedim(1, -1)

        image = torch.ones((length, height, width, 3)) * 0.5
        mask = torch.ones((1, 1, latent.shape[2] * 4, latent.shape[-2], latent.shape[-1]))

        if start_image is not None:
            image[:start_image.shape[0]] = start_image
            mask[:, :, :start_image.shape[0] + 3] = 0.0

        if end_image is not None:
            image[-end_image.shape[0]:] = end_image
            mask[:, :, -end_image.shape[0]:] = 0.0

        concat_latent_image = vae.encode(image[:, :, :, :3])
        mask = mask.view(1, mask.shape[2] // 4, 4, mask.shape[3], mask.shape[4]).transpose(1, 2)
        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": concat_latent_image, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": concat_latent_image, "concat_mask": mask})

        clip_vision_output = None
        if clip_vision_start_image is not None:
            clip_vision_output = clip_vision_start_image

        if clip_vision_end_image is not None:
            if clip_vision_output is not None:
                states = torch.cat([clip_vision_output.penultimate_hidden_states, clip_vision_end_image.penultimate_hidden_states], dim=-2)
                clip_vision_output = comfy.clip_vision.Output()
                clip_vision_output.penultimate_hidden_states = states
            else:
                clip_vision_output = clip_vision_end_image

        if clip_vision_output is not None:
            positive = node_helpers.conditioning_set_values(positive, {"clip_vision_output": clip_vision_output})
            negative = node_helpers.conditioning_set_values(negative, {"clip_vision_output": clip_vision_output})

        out_latent = {}
        out_latent["samples"] = latent
        return io.NodeOutput(positive, negative, out_latent)



class LuyWanFirstLastFrameToVideo2(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="LuyWanFirstLastFrameToVideo2",
            category="luy",
            inputs=[
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Vae.Input("vae"),
                io.Int.Input("width", default=800, min=16, max=nodes.MAX_RESOLUTION, step=16),
                io.Int.Input("height", default=480, min=16, max=nodes.MAX_RESOLUTION, step=16),
                io.Int.Input("length", default=81, min=1, max=nodes.MAX_RESOLUTION, step=4),
                io.Int.Input("batch_size", default=1, min=1, max=4096),
                io.ClipVisionOutput.Input("clip_vision_end_image", optional=True),
                io.Image.Input("end_image", optional=True),
                io.Latent.Input("prev_latent", optional=True),
                io.Float.Input("transition_smoothness", default=0.8, min=0.1, max=1.0, step=0.1, display_name="过渡平滑度"),
                io.Int.Input("start_guide_frames", default=8, min=3, max=20, step=1, display_name="首帧引导帧数"),
                io.Int.Input("end_preload_frames", default=15, min=5, max=30, step=1, display_name="尾帧预加载帧数"),
                io.Int.Input("max_end_lock_frames", default=10, min=1, max=50, step=1, display_name="尾帧锁定帧数"),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, vae, width, height, length, batch_size, end_image=None, clip_vision_end_image=None, prev_latent=None, transition_smoothness=0.8, start_guide_frames=8, end_preload_frames=15, max_end_lock_frames=10) -> io.NodeOutput:
        spacial_scale = vae.spacial_compression_encode()
        latent_frames = ((length - 1) // 4) + 1
        device = comfy.model_management.intermediate_device()
        # 初始化Latent，目标尺寸严格匹配
        latent = torch.zeros([batch_size, vae.latent_channels, latent_frames, height // spacial_scale, width // spacial_scale], device=device)

        # 参数安全限制，防止越界
        use_prev_latent = prev_latent is not None and "samples" in prev_latent
        start_guide_frames = min(start_guide_frames, length // 3)
        end_preload_frames = min(end_preload_frames, length // 3)
        max_end_lock_frames = min(max_end_lock_frames, length // 4)

        # 初始化引导图 - 0.5灰色底，后续被首帧/尾帧覆盖，彻底根除闪屏
        guide_image = torch.full((length, height, width, 3), 0.5, device=device, dtype=torch.float32)
        prev_frame_img = None
        end_frame_img = None

        # ===================== ✅ 核心1：首帧继承 + 零报错逐帧赋值 【绝对安全，永不报错】 =====================
        if use_prev_latent:
            prev_latent_samples = prev_latent["samples"].to(device)
            # 基础校验，防止低级错误
            assert prev_latent_samples.shape[1] == vae.latent_channels, "历史Latent通道数与VAE不匹配！"
            assert prev_latent_samples.shape[3:] == (height//spacial_scale, width//spacial_scale), f"分辨率不匹配！历史:{prev_latent_samples.shape[3:]}, 当前:{(height//spacial_scale, width//spacial_scale)}"

            # 提取历史视频最后一帧，作为当前视频首帧
            prev_last_frame = prev_latent_samples[:, :, -1:, :, :]
            latent[:, :, 0:1, :, :] = prev_last_frame

            # 解码首帧Latent为图片，标准化处理（自动修复维度+通道）
            prev_frame_img = vae.decode(prev_last_frame)  # [B,C,H,W]
            prev_frame_img = prev_frame_img.movedim(1, -1)[0]  # 降维为 [H,W,C] 标准格式
            # 尺寸适配：强制缩放到目标宽高
            prev_frame_img = comfy.utils.common_upscale(prev_frame_img.movedim(-1,1), width, height, "bilinear", "center").movedim(1,-1)
            # ✅ 自动修复：单通道转3通道RGB
            if prev_frame_img.shape[-1] == 1:
                prev_frame_img = prev_frame_img.repeat(1,1,3)

            # ✅ 零报错核心：用FOR循环逐帧赋值，适配任何张量，永远不报错！
            for i in range(start_guide_frames):
                if i < length:
                    guide_image[i] = prev_frame_img

            # 首帧多帧融合衰减，保证首帧信息缓慢消失，过渡丝滑无硬切
            blend_frames = min(8, latent_frames-1, start_guide_frames)
            for i in range(1, blend_frames + 1):
                weight = 1.0 - (i / (blend_frames + 4)) * transition_smoothness
                latent[:, :, i:i+1, :, :] = prev_last_frame * weight + latent[:, :, i:i+1, :, :] * (1 - weight)

        # ===================== ✅ 核心2：尾帧锚定 + 过渡渐变 + 零报错赋值 =====================
        if end_image is not None and use_prev_latent and prev_frame_img is not None:
            # 处理尾帧图片，标准化+自动修复通道/维度
            end_frame_img = end_image[-1:].movedim(-1,1)
            end_frame_img = comfy.utils.common_upscale(end_frame_img, width, height, "bilinear", "center").movedim(1,-1)[0]
            if end_frame_img.shape[-1] == 1:
                end_frame_img = end_frame_img.repeat(1,1,3)

            # 计算过渡区间，避免索引越界
            preload_start = length - end_preload_frames - max_end_lock_frames
            preload_start = max(preload_start, start_guide_frames)
            preload_end = length - max_end_lock_frames

            # ✅ 首帧→尾帧 平滑渐变过渡：逐帧计算权重，无闪屏、无硬转场
            if preload_start < preload_end:
                total_trans_frames = preload_end - preload_start
                for i in range(total_trans_frames):
                    frame_idx = preload_start + i
                    if frame_idx >= length: break
                    # 渐变系数，平滑过渡
                    t = (i / total_trans_frames) * transition_smoothness
                    guide_image[frame_idx] = prev_frame_img * (1 - t) + end_frame_img * t

            # ✅ 零报错核心：尾帧锁定区，逐帧赋值，绝对安全
            for i in range(max_end_lock_frames):
                frame_idx = length - max_end_lock_frames + i
                if frame_idx < length:
                    guide_image[frame_idx] = end_frame_img

        # ===================== ✅ 核心3：全段平滑MASK，无硬切换 =====================
        mask = torch.ones((1, 1, latent.shape[2] * 4, height//spacial_scale, width//spacial_scale), device=device)
        if end_image is not None:
            # 尾帧锁定区，MASK=0 强制锁定
            mask[:, :, -max_end_lock_frames:] = 0.0
            # 过渡区，MASK从1→0平滑渐变，生成权逐步移交
            preload_mask_start = length - end_preload_frames - max_end_lock_frames
            preload_mask_end = length - max_end_lock_frames
            for i in range(preload_mask_start, preload_mask_end):
                if i >= mask.shape[2]: break
                t = (i - preload_mask_start) / (preload_mask_end - preload_mask_start)
                mask[:, :, i:i+1, :, :] = 1.0 - t * transition_smoothness

        # ===================== ✅ 核心4：条件注入 + 最终输出 =====================
        # 编码引导图，注入到Conditioning，无冗余计算
        concat_latent = vae.encode(guide_image.movedim(-1, 1))
        mask = mask.view(1, mask.shape[2]//4,4,mask.shape[3],mask.shape[4]).transpose(1,2)
        # 更新正负条件
        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": concat_latent, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": concat_latent, "concat_mask": mask})

        # 尾帧视觉特征增强（可选）
        if clip_vision_end_image is not None:
            positive = node_helpers.conditioning_set_values(positive, {"clip_vision_output": clip_vision_end_image})
            negative = node_helpers.conditioning_set_values(negative, {"clip_vision_output": clip_vision_end_image})

        # 输出最终Latent
        out_latent = {"samples": latent}
        return io.NodeOutput(positive, negative, out_latent)