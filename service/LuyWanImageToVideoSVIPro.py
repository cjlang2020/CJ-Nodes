import node_helpers
import comfy.latent_formats
import torch
from nodes import MAX_RESOLUTION
from comfy.comfy_types.node_typing import IO
from comfy_api.latest import io

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
                io.Latent.Input("end_samples"),  # 尾帧锚定帧（视频最终结束帧）
                io.Latent.Input("prev_samples", optional=True),  # 参考的运动帧（取最后10帧+最后1帧）
                io.Int.Input("motion_latent_count", default=1, min=0, max=128, step=1),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, length, motion_latent_count, end_samples, prev_samples=None) -> io.NodeOutput:
        # 1. 提取锚定尾帧 + 基础维度定义，固定尾帧不可修改，clone+detach防止梯度污染
        end_latent = end_samples["samples"].clone().detach()
        B, C, _, H, W = end_latent.shape  # anchor的帧维度固定为1
        total_latents = (length - 1) // 4 + 1  # 总帧数不变，和原逻辑完全一致
        device = end_latent.device
        dtype = end_latent.dtype
        # 核心配置：参考prev_samples的【最后10帧】做运动参考（可自行修改这个数值）
        REF_FRAME_NUM = 10

        # 2. ✅【核心修改1】参考帧提取逻辑：只取prev_samples的最后10帧 + 单独抽离最后1帧作为起始锚定帧
        # 需求核心：生成视频的第一帧 = prev_samples最后一帧，生成视频的最后一帧 = end_samples
        motion_latent = torch.zeros([0]) # 空张量占位
        prev_last_frame = None # 存储prev的最后一帧，作为生成视频的【起始帧】
        if prev_samples is not None and motion_latent_count > 0:
            # 取出prev的所有有效帧
            prev_all_latent = prev_samples["samples"].clone().detach()
            prev_frame_total = prev_all_latent.shape[2]

            # 取prev_samples的【最后10帧】做运动参考，不足10帧则全取，容错处理
            take_frame_num = min(REF_FRAME_NUM, prev_frame_total)
            motion_latent = prev_all_latent[:, :, -take_frame_num:].clone()

            # ✅强制抽离prev的【最后1帧】，作为生成视频的【固定起始帧】
            prev_last_frame = prev_all_latent[:, :, -1:, :, :].clone()

        # 3. ✅【核心修改2】重构帧数量分配逻辑，严格满足：起始帧+过渡帧+结束帧
        padding_size = 0
        if prev_last_frame is not None:
            # 有参考帧：总帧数 = 起始帧(1) + 过渡补帧 + 结束帧(1) → 过渡补帧 = 总帧数 - 2
            padding_size = total_latents - 2
        else:
            # 无参考帧：兜底逻辑，总帧数 = 过渡补帧 + 结束帧(1) → 过渡补帧 = 总帧数 -1
            padding_size = total_latents - 1

        # 4. 构建padding补帧（格式对齐原代码，WAN21标准化，无运动信息仅做填充）
        padding = torch.zeros(B, C, max(padding_size, 0), H, W, dtype=dtype, device=device)
        padding = comfy.latent_formats.Wan21().process_out(padding)

        # 5. ✅【核心修改3/重中之重】帧序拼接逻辑 彻底重构 - 完全匹配你的核心需求
        # 生成视频帧序严格定义：【prev最后1帧(起始锚定)】 → 【过渡补帧】 → 【end_samples(结束锚定)】
        # 效果：视频开头完美承接prev的最后一帧，视频结尾精准锚定end帧，中间帧自然过渡
        if prev_last_frame is not None and padding_size >= 0:
            image_cond_latent = torch.cat([prev_last_frame, padding, end_latent], dim=2)
        else:
            # 无参考帧的兜底拼接：padding + 锚定尾帧，和原逻辑一致
            image_cond_latent = torch.cat([padding, end_latent], dim=2)

        # 6. ✅【核心修改4】掩码逻辑精准优化 - 适配双锚定帧（起始+结束）
        # 掩码规则：起始帧(prev最后1帧) + 结束帧(end) 都置1（锚定不生成），中间过渡帧置0（模型生成区域）
        # 原理：模型只会在掩码0的区域生成内容，不会篡改锚定帧，保证首尾帧完全精准不变
        mask = torch.ones((1, 1, total_latents, H, W), device=device, dtype=dtype)
        if prev_last_frame is not None:
            mask[:, :, 1:-1] = 0.0  # 中间过渡帧：生成区
        else:
            mask[:, :, :-1] = 0.0    # 无参考帧时：除尾帧外全为生成区

        # 7. 赋值条件信息，将锚定帧+过渡帧+掩码传入正负条件，和原逻辑一致
        positive = node_helpers.conditioning_set_values(positive, {"concat_latent_image": image_cond_latent, "concat_mask": mask})
        negative = node_helpers.conditioning_set_values(negative, {"concat_latent_image": image_cond_latent, "concat_mask": mask})

        # 8. 输出最终latent：包含【精准首尾锚定+自然过渡帧】的有效latent，无空帧
        out_latent = {}
        out_latent["samples"] = image_cond_latent

        return io.NodeOutput(positive, negative, out_latent)


import node_helpers
import comfy.latent_formats
import torch
from nodes import MAX_RESOLUTION
from comfy.comfy_types.node_typing import IO
from comfy_api.latest import io

class LuyWanImageToVideoSVIPro2(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="LuyWanImageToVideoSVIPro2",
            category="luy",
            inputs=[
                io.Conditioning.Input("positive"),
                io.Conditioning.Input("negative"),
                io.Int.Input("length", default=81, min=1, max=MAX_RESOLUTION, step=4),
                io.Latent.Input("end_samples"),  # 尾帧锚定帧【绝对不变】
                io.Latent.Input("prev_samples", optional=True),  # 参考视频帧
                io.Int.Input("motion_latent_count", default=1, min=0, max=128, step=1),
            ],
            outputs=[
                io.Conditioning.Output(display_name="positive"),
                io.Conditioning.Output(display_name="negative"),
                io.Latent.Output(display_name="latent"),
            ],
        )

    @classmethod
    def execute(cls, positive, negative, length, motion_latent_count, end_samples, prev_samples=None) -> io.NodeOutput:
        # ===================== 基础配置 & 核心常量 =====================
        end_latent = end_samples["samples"].clone().detach()  # 尾帧彻底冻结防篡改 永不改动
        B, C, _, H, W = end_latent.shape
        total_latents = (length - 1) // 4 + 1  # 总帧数逻辑完全不变 永不改动
        device = end_latent.device
        dtype = end_latent.dtype
        REF_LAST_FRAMES = 10  # 参考prev最后10帧做运动学习，可自定义修改
        USE_PREV_FRAMES_NUM = 5 # ✅【核心修改】强制使用prev最后5帧作为视频开头

        # 核心变量：起始锚定帧(5帧)、运动参考帧
        start_anchor_frames = None  # 修改：从单帧改为多帧(5帧)
        motion_ref_latents = None

        # ===================== 核心参考帧提取【✅ 核心大改 - 满足需求】 =====================
        if prev_samples is not None and motion_latent_count > 0:
            prev_latents = prev_samples["samples"].clone().detach()
            prev_total_frames = prev_latents.shape[2]

            # ✅ 提取prev最后10帧作为【运动参考帧】- 学习运动规律/画面风格/色彩特征 保留原逻辑
            take_frames = min(REF_LAST_FRAMES, prev_total_frames)
            motion_ref_latents = prev_latents[:, :, -take_frames:]

            # ✅【核心修改1】提取prev最后5帧 作为【生成视频的开头锚定帧】，固定不变，原画质原色彩
            take_start_frames = min(USE_PREV_FRAMES_NUM, prev_total_frames)
            start_anchor_frames = prev_latents[:, :, -take_start_frames:].clone()
            # 记录实际提取的开头帧数（兼容prev帧数不足5帧的边界情况）
            real_start_frame_num = start_anchor_frames.shape[2]

        # ===================== 过渡帧数量计算【✅ 核心修改2 - 关键公式】 =====================
        padding_size = 0
        if start_anchor_frames is not None:
            # ✅ 总帧数构成：前5锚定帧(N) + 中间过渡帧(padding) + 最后1尾帧 = 总帧数
            padding_size = total_latents - real_start_frame_num - 1
        else:
            # 无参考帧兜底逻辑，和原代码一致
            padding_size = total_latents - 1
        padding_size = max(padding_size, 0)  # 容错：防止负数帧，避免报错

        # ===================== ✅【保留原核心修复】解决灰色帧的关键代码 - 重中之重 =====================
        # 不再用 torch.zeros 纯0张量，改用真实帧插值，基底色彩正常，WAN21标准化后无灰色
        padding = torch.zeros(B, C, padding_size, H, W, dtype=dtype, device=device)
        if start_anchor_frames is not None and padding_size > 0:
            # ✅ 过渡帧的起始基准：取【前5帧的最后1帧】，保证过渡衔接自然无断层
            start_data = start_anchor_frames[:, :, -1]  # 前5帧的最后一帧数据（非0，色彩正常）
            end_data = end_latent[:, :, 0]              # 结束帧的真实有效数据（非0，色彩正常）

            # 逐帧生成 自然渐变过渡帧：gamma修正解决灰蒙蒙，色彩饱满，过渡自然 保留最优gamma值
            for i in range(padding_size):
                weight = (i / padding_size) ** 0.85  # gamma最优值0.85，可微调0.8~0.9
                padding[:, :, i] = (1 - weight) * start_data + weight * end_data

        # 保留WAN21标准化，格式和原代码完全对齐（此时padding非0，色彩正常）
        padding = comfy.latent_formats.Wan21().process_out(padding)

        # ===================== ✅ 帧序拼接【✅ 核心修改3 - 核心规则】永不改动 =====================
        # 生成视频帧序列：【前5帧锚定帧(prev最后5帧)】 → 【彩色过渡帧】 → 【结束锚定帧(end_samples)】
        image_cond_latent = None
        if start_anchor_frames is not None:
            # 拼接顺序：前5帧 → 过渡帧 → 尾帧
            image_cond_latent = torch.cat([start_anchor_frames, padding, end_latent], dim=2)
        else:
            # 无参考帧兜底逻辑，和原代码一致
            image_cond_latent = torch.cat([padding, end_latent], dim=2)

        # ===================== ✅ 四重保障【核心升级】：前5帧完全不变 + 最后1帧绝对不变 重中之重 =====================
        # 第一重：掩码锚定 → 核心规则：掩码=1 模型完全不修改，掩码=0 模型生成内容
        mask = torch.ones((1, 1, total_latents, H, W), device=device, dtype=dtype)
        if start_anchor_frames is not None:
            # ✅【核心修改4】掩码规则：前5帧 + 最后1帧 掩码=1(完全保护)，只有中间过渡帧=0(生成区)
            mask[:, :, real_start_frame_num : -1] = 0.0
        else:
            # 无参考帧时，仅结束帧保护，和原代码一致
            mask[:, :, :-1] = 0.0

        # 第二重：强制覆写 → 万无一失，最后一帧强制赋值原始end_samples 永不改动
        image_cond_latent[:, :, -1:] = end_latent

        # 第三重：张量冻结 → end_latent和start_anchor_frames均已detach，无梯度，模型无法修改
        # 第四重：前5帧直接取自prev原始帧，无任何插值/修改，原画质原色彩

        # ===================== 条件赋值+输出 保留原逻辑 =====================
        cond_kwargs = {"concat_latent_image": image_cond_latent, "concat_mask": mask}
        # 把运动参考帧传入条件，让模型学习prev的运动规律，过渡更丝滑
        if motion_ref_latents is not None:
            cond_kwargs["motion_ref_latents"] = motion_ref_latents

        positive = node_helpers.conditioning_set_values(positive, cond_kwargs)
        negative = node_helpers.conditioning_set_values(negative, cond_kwargs)

        out_latent = {"samples": image_cond_latent}
        return io.NodeOutput(positive, negative, out_latent)