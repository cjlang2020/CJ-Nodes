import torch
import comfy.utils
import comfy.model_management

class PainterLongVideo:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "positive": ("CONDITIONING", ),
                "negative": ("CONDITIONING", ),
                "vae": ("VAE", ),
                "width": ("INT", {"default": 832, "min": 16, "max": 8192, "step": 16}),
                "height": ("INT", {"default": 480, "min": 16, "max": 8192, "step": 16}),
                "length": ("INT", {"default": 81, "min": 1, "max": 1000, "step": 1}),
                "batch_size": ("INT", {"default": 1, "min": 1, "max": 4096}),
                "motion_frames": ("INT", {"default": 5, "min": 1, "max": 20}),
                "motion_amplitude": ("FLOAT", {"default": 1.15, "min": 1.0, "max": 2.0, "step": 0.05}),
            },
            "optional": {
                "previous_video": ("IMAGE",),          # 现在是可选
                "initial_reference_image": ("IMAGE",),
                "clip_vision_output": ("CLIP_VISION_OUTPUT",),
                "start_image": ("IMAGE",),             # 首帧
                "end_image": ("IMAGE",),               # 尾帧
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT")
    RETURN_NAMES = ("positive", "negative", "latent")
    FUNCTION = "execute"
    CATEGORY = "luy/视频生成"
    DISPLAY_NAME = "PainterLongVideo"

    def execute(
        self,
        positive,
        negative,
        vae,
        width,
        height,
        length,
        batch_size,
        motion_frames,
        motion_amplitude=1.15,
        previous_video=None,
        initial_reference_image=None,
        clip_vision_output=None,
        start_image=None,
        end_image=None,
    ):
        device = comfy.model_management.intermediate_device()
        latent_timesteps = ((length - 1) // 4) + 1
        latent = torch.zeros([batch_size, 16, latent_timesteps, height // 8, width // 8], device=device)

        # ---------- 1. 收集开关 ----------
        has_prev = previous_video is not None
        has_start = start_image is not None
        has_end   = end_image   is not None

        # ---------- 2. 无输入直接报错 ----------
        if not has_prev and not has_start and not has_end:
            raise RuntimeError("PainterLongVideo: 必须接入 previous_video、start_image、end_image 中的至少一个！")

        # ---------- 3. 构造统一的 image / mask ----------
        # 默认值：灰色画布
        image = torch.full((length, height, width, 3), 0.5, device=device, dtype=torch.float32)
        mask  = torch.ones((1, 1, latent_timesteps * 4, height // 8, width // 8), device=device, dtype=torch.float32)

        # ---------- 4. 按优先级分支 ----------
        if has_start or has_end:
            # 分支 A/B：只要接了 start 或 end，就以「首尾帧」逻辑为准
            if has_start:
                start_img = comfy.utils.common_upscale(
                    start_image[:length].movedim(-1, 1), width, height, "bilinear", "center"
                ).movedim(1, -1)
                actual_start_len = min(start_img.shape[0], length)
                image[:actual_start_len] = start_img[:actual_start_len]
                mask[:, :, :actual_start_len + 3] = 0.0   # 保护首帧（含缓冲）
            else:
                # 没给 start，但给了 end → 把 previous_video 最后一帧当首帧
                if has_prev:
                    last_frame = previous_video[-1:].clone()
                    last_frame_resized = comfy.utils.common_upscale(
                        last_frame.movedim(-1, 1), width, height, "bilinear", "center"
                    ).movedim(1, -1)
                    image[0] = last_frame_resized[0]
                    mask[:, :, :1 + 3] = 0.0
                # 如果既没有 start 也没有 prev，却走到这里，说明只接了 end，也允许继续

            if has_end:
                end_img = comfy.utils.common_upscale(
                    end_image[-length:].movedim(-1, 1), width, height, "bilinear", "center"
                ).movedim(1, -1)
                actual_end_len = min(end_img.shape[0], length)
                image[-actual_end_len:] = end_img[-actual_end_len:]
                mask[:, :, -actual_end_len:] = 0.0

            concat_latent_image = vae.encode(image[:, :, :, :3])
            mask = mask.view(1, mask.shape[2] // 4, 4, mask.shape[3], mask.shape[4]).transpose(1, 2)

            # 运动参考：优先用 previous_video（如果给了）
            ref_motion_latent = None
            if has_prev and previous_video.shape[0] >= 2:
                ref_motion = previous_video[-min(73, previous_video.shape[0]):].clone()
                ref_motion = comfy.utils.common_upscale(
                    ref_motion.movedim(-1, 1), width, height, "bilinear", "center"
                ).movedim(1, -1)
                if ref_motion.shape[0] < 73:
                    gray_fill = torch.ones([73, height, width, 3], device=device, dtype=ref_motion.dtype) * 0.5
                    gray_fill[-ref_motion.shape[0]:] = ref_motion
                    ref_motion = gray_fill
                ref_motion_latent_temp = vae.encode(ref_motion[:, :, :, :3])
                ref_motion_latent = ref_motion_latent_temp[:, :, -19:]

        else:
            # 分支 C：只接了 previous_video，走原逻辑
            last_frame = previous_video[-1:].clone()
            last_frame_resized = comfy.utils.common_upscale(
                last_frame.movedim(-1, 1), width, height, "bilinear", "center"
            ).movedim(1, -1)

            image_seq = torch.full(
                (length, height, width, last_frame_resized.shape[-1]),
                0.5, device=last_frame_resized.device, dtype=last_frame_resized.dtype
            )
            image_seq[0] = last_frame_resized[0]
            concat_latent_image = vae.encode(image_seq[:, :, :, :3])

            mask = torch.ones((1, 1, latent_timesteps, height // 8, width // 8),
                              device=device, dtype=last_frame_resized.dtype)
            mask[:, :, 0] = 0.0

            # 运动幅度增强
            if motion_amplitude > 1.0:
                base_latent = concat_latent_image[:, :, 0:1]
                gray_latent = concat_latent_image[:, :, 1:]
                diff = gray_latent - base_latent
                diff_mean = diff.mean(dim=(1, 3, 4), keepdim=True)
                diff_centered = diff - diff_mean
                scaled_latent = base_latent + diff_centered * motion_amplitude + diff_mean
                scaled_latent = torch.clamp(scaled_latent, -6, 6)
                concat_latent_image = torch.cat([base_latent, scaled_latent], dim=2)

            # 运动参考帧
            ref_motion = previous_video[-motion_frames:].clone()
            if ref_motion.shape[0] > 73:
                ref_motion = ref_motion[-73:]
            ref_motion_resized = comfy.utils.common_upscale(
                ref_motion.movedim(-1, 1), width, height, "bilinear", "center"
            ).movedim(1, -1)
            if ref_motion_resized.shape[0] < 73:
                gray_fill = torch.ones([73, height, width, 3], device=ref_motion_resized.device,
                                       dtype=ref_motion_resized.dtype) * 0.5
                gray_fill[-ref_motion_resized.shape[0]:] = ref_motion_resized
                ref_motion_resized = gray_fill
            ref_motion_latent_temp = vae.encode(ref_motion_resized[:, :, :, :3])
            ref_motion_latent = ref_motion_latent_temp[:, :, -19:]

        # ---------- 5. 构造 reference_latents ----------
        ref_latents = []
        # (a) 上一段最后一帧（始终添加）
        last_frame_for_ref = previous_video[-1:] if has_prev else image[0:1]
        last_frame_for_ref = comfy.utils.common_upscale(
            last_frame_for_ref.movedim(-1, 1), width, height, "bilinear", "center"
        ).movedim(1, -1)
        last_latent = vae.encode(last_frame_for_ref[:, :, :, :3])
        ref_latents.append(last_latent)

        # (b) 初始参考图（如有）
        if initial_reference_image is not None:
            init_img = initial_reference_image[:1]
            init_img_resized = comfy.utils.common_upscale(
                init_img.movedim(-1, 1), width, height, "bilinear", "center"
            ).movedim(1, -1)
            init_latent = vae.encode(init_img_resized[:, :, :, :3])
            ref_latents.append(init_latent)

        # ---------- 6. conditioning 注入 ----------
        def inject_conditioning(cond, values_dict):
            new_cond = []
            for c_tensor, c_dict in cond:
                new_dict = c_dict.copy()
                new_dict.update(values_dict)
                new_cond.append([c_tensor, new_dict])
            return new_cond

        def append_conditioning(cond, key, value_list):
            new_cond = []
            for c_tensor, c_dict in cond:
                new_dict = c_dict.copy()
                if key in new_dict:
                    new_dict[key] = new_dict[key] + value_list
                else:
                    new_dict[key] = value_list
                new_cond.append([c_tensor, new_dict])
            return new_cond

        shared_values = {
            "concat_latent_image": concat_latent_image,
            "concat_mask": mask,
        }
        if ref_motion_latent is not None:
            shared_values["reference_motion"] = ref_motion_latent

        pos_out = inject_conditioning(positive, shared_values)
        neg_out = inject_conditioning(negative, shared_values)

        pos_out = append_conditioning(pos_out, "reference_latents", ref_latents)
        neg_ref_latents = [torch.zeros_like(r) for r in ref_latents]
        neg_out = append_conditioning(neg_out, "reference_latents", neg_ref_latents)

        if clip_vision_output is not None:
            pos_out = inject_conditioning(pos_out, {"clip_vision_output": clip_vision_output})
            neg_out = inject_conditioning(neg_out, {"clip_vision_output": clip_vision_output})

        latent_out = {"samples": latent}
        return (pos_out, neg_out, latent_out)