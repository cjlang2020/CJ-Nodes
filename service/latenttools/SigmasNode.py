import torch
import math


class SigmasDefinition:
    """
    自定义Sigma区间定义节点
    控制不同sigma区间的插值密度和方式
    """

    INTERPOLATION_MODES = ["Linear", "Logarithmic", "Exponential", "Sigmoid", "Cosine"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "v_height": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "1.0→0.8 区间插值个数（大结构、运动方向）"
                }),
                "v_middle": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "0.8→0.3 区间插值个数（运动细节、过渡）"
                }),
                "v_low": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "0.3→0.0 区间插值个数（纹理、细节）"
                }),
                "interpolation": (cls.INTERPOLATION_MODES, {
                    "default": "Linear",
                    "tooltip": "插值方式：Linear均匀 | Logarithmic前密后疏 | Exponential前疏后密 | Sigmoid/S曲线两端慢中间快 | Cosine平滑过渡"
                }),
            }
        }

    RETURN_TYPES = ("SIGMAS", "*")
    RETURN_NAMES = ("sigmas", "tensor")
    FUNCTION = "generate"
    CATEGORY = "luy/sigmas"

    def _interpolate(self, a, b, n, mode):
        """在区间[a, b]之间插入n个点"""
        if n == 0:
            return []

        points = []
        for i in range(1, n + 1):
            t = i / (n + 1)  # t ∈ (0, 1)

            if mode == "Linear":
                value = a + (b - a) * t

            elif mode == "Logarithmic":
                # 对数插值：前密后疏
                if t <= 0:
                    value = a
                else:
                    value = a + (b - a) * math.log(1 + t) / math.log(2)

            elif mode == "Exponential":
                # 指数插值：前疏后密
                value = a + (b - a) * (math.exp(t) - 1) / (math.exp(1) - 1)

            elif mode == "Sigmoid":
                # Sigmoid S曲线：两端慢中间快
                sigmoid_t = 1 / (1 + math.exp(-10 * (t - 0.5)))
                value = a + (b - a) * sigmoid_t

            elif mode == "Cosine":
                # 余弦插值：平滑过渡
                value = a + (b - a) * (1 - math.cos(t * math.pi)) / 2

            else:
                value = a + (b - a) * t  # 默认线性

            points.append(value)

        return points

    def generate(self, v_height, v_middle, v_low, interpolation):
        # 4个锚点
        anchor_high = 1.0
        anchor_mid_high = 0.8
        anchor_mid_low = 0.3
        anchor_low = 0.0

        # 构建sigmas列表
        sigmas = [anchor_high]

        # 1.0 → 0.8 区间插值
        sigmas.extend(self._interpolate(anchor_high, anchor_mid_high, v_height, interpolation))
        sigmas.append(anchor_mid_high)

        # 0.8 → 0.3 区间插值
        sigmas.extend(self._interpolate(anchor_mid_high, anchor_mid_low, v_middle, interpolation))
        sigmas.append(anchor_mid_low)

        # 0.3 → 0.0 区间插值
        sigmas.extend(self._interpolate(anchor_mid_low, anchor_low, v_low, interpolation))
        sigmas.append(anchor_low)

        # 转换为torch.Tensor
        sigmas_tensor = torch.tensor(sigmas, dtype=torch.float32)

        return (sigmas_tensor, sigmas_tensor)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "SigmasDefinition": SigmasDefinition,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SigmasDefinition": "Luy-Sigmas定义",
}
