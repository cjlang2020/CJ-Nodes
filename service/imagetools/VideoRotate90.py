from __future__ import annotations
import torch
import numpy as np
from PIL import Image


class VideoRotate90:
    """
    视频旋转90度节点
    - 输入：视频（IMAGE类型的帧序列）
    - 参数：旋转方向（True=右旋转90°，False=左旋转90°）
    - 输出：旋转后的视频（尺寸会改变，如832x480变成480x832）
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video": ("IMAGE", {"tooltip": "输入的视频帧序列"}),
                "rotate_right": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True=右旋转90°（顺时针），False=左旋转90°（逆时针）"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "rotate_video"

    OUTPUT_NODE = False

    CATEGORY = "luy/视频处理"
    DESCRIPTION = "将视频每帧旋转90度，右旋转(默认)为顺时针方向旋转90度"

    def rotate_video(self, video: torch.Tensor, rotate_right: bool = True) -> tuple[torch.Tensor,]:
        """
        旋转视频帧

        Args:
            video: 输入视频张量，形状为 (batch, height, width, channels)
            rotate_right: True=右旋转90°(顺时针), False=左旋转90°(逆时针)

        Returns:
            旋转后的视频张量
        """
        # 检查输入张量维度
        if video.dim() != 4:
            raise ValueError(f"输入视频应该是4D张量 (batch, height, width, channels)，实际维度: {video.dim()}")

        batch_size, height, width, channels = video.shape
        print(f"[VideoRotate90] 输入: {batch_size} 帧, 尺寸 {width}x{height}")

        # 转换为numpy处理 (范围0-255)
        frames_np = (video.cpu().numpy() * 255).astype(np.uint8)

        rotated_frames = []
        for i in range(batch_size):
            # 获取单帧 (height, width, channels)
            frame = frames_np[i]

            # 转换为PIL Image进行旋转
            pil_image = Image.fromarray(frame)

            if rotate_right:
                # 右旋转90度 = 顺时针90度
                rotated_pil = pil_image.rotate(-90, expand=True)
            else:
                # 左旋转90度 = 逆时针90度
                rotated_pil = pil_image.rotate(90, expand=True)

            # 转回numpy (注意：expand=True会自动扩展尺寸)
            rotated_frame = np.array(rotated_pil, dtype=np.uint8)
            rotated_frames.append(rotated_frame)

        # 获取新的尺寸
        new_height, new_width = rotated_frames[0].shape[:2]
        print(f"[VideoRotate90] 输出: {batch_size} 帧, 尺寸 {new_width}x{new_height}")

        # 转换为tensor并归一化到0-1
        rotated_tensor = torch.from_numpy(np.stack(rotated_frames)).float() / 255.0

        # 确保设备一致
        if video.is_cuda:
            rotated_tensor = rotated_tensor.to(video.device)

        return (rotated_tensor,)


class VideoRotate90Alt:
    """
    视频旋转90度节点（使用张量操作，更快）
    - 输入：视频（IMAGE类型的帧序列）
    - 参数：旋转方向（True=右旋转90°，False=左旋转90°）
    - 输出：旋转后的视频（尺寸会改变）
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video": ("IMAGE", {"tooltip": "输入的视频帧序列"}),
                "rotate_right": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "True=右旋转90°（顺时针），False=左旋转90°（逆时针）"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "rotate_video_tensor"

    OUTPUT_NODE = False

    CATEGORY = "luy/视频处理"
    DESCRIPTION = "将视频每帧旋转90度（张量版本）"

    def rotate_video_tensor(self, video: torch.Tensor, rotate_right: bool = True) -> tuple[torch.Tensor,]:
        """
        使用PyTorch张量操作旋转视频帧

        Args:
            video: 输入视频张量，形状为 (batch, height, width, channels)
            rotate_right: True=右旋转90°(顺时针), False=左旋转90°(逆时针)

        Returns:
            旋转后的视频张量
        """
        if video.dim() != 4:
            raise ValueError(f"输入视频应该是4D张量 (batch, height, width, channels)，实际维度: {video.dim()}")

        batch_size, height, width, channels = video.shape
        print(f"[VideoRotate90-Alt] 输入: {batch_size} 帧, 尺寸 {width}x{height}")

        if rotate_right:
            # 顺时针90度 = transpose + flip horizontal
            # 先转置 (width -> height)
            rotated = video.permute(0, 2, 1, 3)
            # 再水平翻转
            rotated = torch.flip(rotated, dims=[2])
        else:
            # 逆时针90度 = transpose + flip vertical
            rotated = video.permute(0, 2, 1, 3)
            rotated = torch.flip(rotated, dims=[1])

        new_height, new_width = rotated.shape[1], rotated.shape[2]
        print(f"[VideoRotate90-Alt] 输出: {batch_size} 帧, 尺寸 {new_width}x{new_height}")

        return (rotated,)