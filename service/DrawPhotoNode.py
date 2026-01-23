import torch
import numpy as np
from PIL import Image, ImageDraw
import json
import base64
from io import BytesIO
import logging

# 配置日志（输出到控制台+显示详细级别）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MouseDrawNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "canvas_width": ("INT", {"default": 512, "min": 128, "max": 2048}),
                "canvas_height": ("INT", {"default": 512, "min": 128, "max": 2048}),
            },
            "hidden": {
                "draw_data": "STRING",
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("draw_image",)
    FUNCTION = "generate_image"
    CATEGORY = "Luy"

    def generate_image(self, canvas_width, canvas_height, draw_data="empty"):
        """
        完全参照ImageDrawNode的张量转换逻辑，生成手绘图像并输出标准ComfyUI张量
        """
        try:
            # ========== 步骤1：强制标准化输入参数 ==========
            canvas_width = max(128, min(2048, int(canvas_width)))
            canvas_height = max(128, min(2048, int(canvas_height)))
            logger.info(f"【步骤1】标准化后画布尺寸 - 宽：{canvas_width}，高：{canvas_height}")

            # ========== 步骤2：初始化画布（RGB格式） ==========
            img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            logger.info(f"【步骤2】初始画布创建完成 - 模式：{img.mode}，尺寸：{img.size}，初始背景色：白色(255,255,255)")

            # ========== 步骤3：解析并绘制路径 ==========
            logger.info(f"【步骤3】draw_data原始值：{draw_data[:500]}...")  # 只打印前500字符避免过长
            logger.info(f"【步骤3】draw_data是否为空：{draw_data == 'empty' or not draw_data.strip()}")

            if draw_data != "empty" and draw_data.strip():
                try:
                    # 解析JSON
                    data = json.loads(draw_data)
                    logger.info(f"【步骤3-1】draw_data解析为JSON成功，数据结构：{json.dumps(data, indent=2)[:1000]}...")

                    # 解析背景色（带容错）
                    bg_hex = data.get("bg_color", "#ffffff").lstrip('#')
                    logger.info(f"【步骤3-2】原始背景色HEX：{bg_hex}")
                    if len(bg_hex) not in (3, 6):
                        bg_hex = "ffffff"
                        logger.warning(f"【步骤3-2】背景色HEX长度异常，重置为：{bg_hex}")
                    if len(bg_hex) == 3:
                        bg_hex = bg_hex * 2
                        logger.info(f"【步骤3-2】背景色HEX补全为6位：{bg_hex}")

                    try:
                        bg_r = int(bg_hex[0:2], 16)
                        bg_g = int(bg_hex[2:4], 16)
                        bg_b = int(bg_hex[4:6], 16)
                        logger.info(f"【步骤3-2】背景色转换为RGB：({bg_r}, {bg_g}, {bg_b})")
                    except ValueError as e:
                        bg_r, bg_g, bg_b = 255, 255, 255
                        logger.error(f"【步骤3-2】背景色转换失败：{e}，重置为白色(255,255,255)")

                    # 重新创建画布
                    img = Image.new("RGB", (canvas_width, canvas_height), (bg_r, bg_g, bg_b))
                    draw = ImageDraw.Draw(img)
                    logger.info(f"【步骤3-2】重新创建画布 - 背景色RGB：({bg_r}, {bg_g}, {bg_b})，画布尺寸：{img.size}")

                    # 绘制路径
                    paths = data.get("paths", [])
                    logger.info(f"【步骤3-3】获取到路径数量：{len(paths)}")

                    for idx, path in enumerate(paths):
                        logger.info(f"【步骤3-3】处理第{idx+1}条路径，原始数据：{path}")
                        points = path.get("points", [])
                        logger.info(f"【步骤3-3】第{idx+1}条路径的原始点数量：{len(points)}")

                        if len(points) < 2:
                            logger.warning(f"【步骤3-3】第{idx+1}条路径点数量不足2个，跳过")
                            continue

                        # 解析画笔属性
                        color_hex = path.get("color", "#000000").lstrip('#')
                        logger.info(f"【步骤3-3】第{idx+1}条路径原始颜色HEX：{color_hex}")
                        if len(color_hex) not in (3, 6):
                            color_hex = "000000"
                            logger.warning(f"【步骤3-3】第{idx+1}条路径颜色HEX异常，重置为：{color_hex}")
                        if len(color_hex) == 3:
                            color_hex = color_hex * 2
                            logger.info(f"【步骤3-3】第{idx+1}条路径颜色HEX补全为6位：{color_hex}")

                        try:
                            r = int(color_hex[0:2], 16)
                            g = int(color_hex[2:4], 16)
                            b = int(color_hex[4:6], 16)
                            logger.info(f"【步骤3-3】第{idx+1}条路径颜色转换为RGB：({r}, {g}, {b})")
                        except ValueError as e:
                            r, g, b = 0, 0, 0
                            logger.error(f"【步骤3-3】第{idx+1}条路径颜色转换失败：{e}，重置为黑色(0,0,0)")
                        color = (r, g, b)

                        try:
                            size = max(1, min(100, int(path.get("size", 5))))
                            logger.info(f"【步骤3-3】第{idx+1}条路径画笔尺寸：{size}")
                        except (ValueError, TypeError) as e:
                            size = 5
                            logger.error(f"【步骤3-3】第{idx+1}条路径画笔尺寸转换失败：{e}，重置为5")

                        is_eraser = path.get("is_eraser", False)
                        logger.info(f"【步骤3-3】第{idx+1}条路径是否为橡皮擦：{is_eraser}")
                        if is_eraser:
                            color = (bg_r, bg_g, bg_b)
                            logger.info(f"【步骤3-3】第{idx+1}条路径为橡皮擦，颜色重置为背景色：({bg_r}, {bg_g}, {bg_b})")

                        # 处理坐标点
                        int_points = []
                        for p_idx, p in enumerate(points):
                            try:
                                x = float(p[0]) if isinstance(p, (list, tuple)) else 0
                                y = float(p[1]) if isinstance(p, (list, tuple)) else 0
                                int_x = int(round(x))
                                int_y = int(round(y))
                                int_points.append((int_x, int_y))
                                logger.info(f"【步骤3-3】第{idx+1}条路径第{p_idx+1}个点 - 原始：{p} → 转换后：({int_x}, {int_y})")
                            except (ValueError, TypeError, IndexError) as e:
                                logger.error(f"【步骤3-3】第{idx+1}条路径第{p_idx+1}个点转换失败：{e}，跳过")
                                continue

                        logger.info(f"【步骤3-3】第{idx+1}条路径有效坐标点数量：{len(int_points)}")
                        if len(int_points) < 2:
                            logger.warning(f"【步骤3-3】第{idx+1}条路径有效点不足2个，跳过绘制")
                            continue

                        # 绘制线条
                        draw_count = 0
                        for i in range(1, len(int_points)):
                            x1, y1 = int_points[i-1]
                            x2, y2 = int_points[i]
                            # 边界检查
                            x1 = max(0, min(canvas_width-1, x1))
                            y1 = max(0, min(canvas_height-1, y1))
                            x2 = max(0, min(canvas_width-1, x2))
                            y2 = max(0, min(canvas_height-1, y2))
                            logger.debug(f"【步骤3-3】绘制线段：({x1}, {y1}) → ({x2}, {y2})，颜色：{color}，宽度：{size}")
                            draw.line([(x1, y1), (x2, y2)], fill=color, width=size)
                            draw.ellipse([(x2 - size//2, y2 - size//2),
                                          (x2 + size//2, y2 + size//2)], fill=color)
                            draw_count += 1
                        logger.info(f"【步骤3-3】第{idx+1}条路径绘制完成，共绘制{draw_count}条线段")

                except json.JSONDecodeError as e:
                    logger.error(f"【步骤3】draw_data JSON解析失败：{e}")
                    img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
                except Exception as e:
                    logger.error(f"【步骤3】绘图解析失败：{str(e)}", exc_info=True)
                    # 失败后重置为纯白画布
                    img = Image.new("RGB", (canvas_width, canvas_height), (255, 255, 255))
            else:
                logger.warning(f"【步骤3】draw_data为空或为默认值'empty'，仅显示初始白色画布")

            # ========== 步骤4：完全参照ImageDrawNode的张量转换逻辑（核心修改） ==========
            # 1. PIL Image → numpy数组（和参考代码一致）
            image_np = np.array(img)
            logger.info(f"【步骤4-1】PIL转Numpy数组 - 形状：{image_np.shape}，数据类型：{image_np.dtype}")
            logger.info(f"【步骤4-1】数组前5行前5列的RGB值示例：\n{image_np[:5, :5, :]}")
            logger.info(f"【步骤4-1】数组像素值范围：min={image_np.min()}, max={image_np.max()}")

            # 2. 强制保证数据类型为uint8（参考代码的核心逻辑）
            if image_np.dtype != np.uint8:
                image_np = image_np.astype(np.uint8)
                logger.info(f"【步骤4-2】数组类型转换为uint8，新类型：{image_np.dtype}")
            else:
                logger.info(f"【步骤4-2】数组类型已是uint8，无需转换")

            # 3. 转换为浮点数并归一化到[0,1]（和参考代码完全一致）
            image_np = image_np.astype(np.float32) / 255.0
            logger.info(f"【步骤4-3】数组归一化后 - 形状：{image_np.shape}，数据类型：{image_np.dtype}")
            logger.info(f"【步骤4-3】归一化后前5行前5列值示例：\n{image_np[:5, :5, :]}")
            logger.info(f"【步骤4-3】归一化后像素值范围：min={image_np.min()}, max={image_np.max()}")

            # 4. 兼容灰度图/RGBA（参考代码的关键容错）
            if len(image_np.shape) == 2:  # 灰度图转RGB
                image_np = np.stack([image_np, image_np, image_np], axis=-1)
                logger.info(f"【步骤4-4】灰度图转换为RGB，新形状：{image_np.shape}")
            elif image_np.shape[-1] == 4:  # RGBA去掉Alpha通道
                image_np = image_np[:, :, :3]
                logger.info(f"【步骤4-4】RGBA转RGB，去掉Alpha通道，新形状：{image_np.shape}")
            else:
                logger.info(f"【步骤4-4】数组已是RGB格式，形状：{image_np.shape}，无需转换")

            # 5. 仅增加批次维度（参考代码的核心：不做permute！）
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)
            logger.info(f"【步骤4-5】转换为Tensor并增加批次维度 - 形状：{image_tensor.shape}，数据类型：{image_tensor.dtype}")
            logger.info(f"【步骤4-5】Tensor前5行前5列值示例：\n{image_tensor[0, :5, :5, :]}")
            logger.info(f"【步骤4-5】Tensor像素值范围：min={image_tensor.min().item()}, max={image_tensor.max().item()}")

            # 6. 最终校验
            logger.info(f"【步骤4-6】最终输出张量信息 - 维度：{image_tensor.shape}，类型：{image_tensor.dtype}")

            # 额外：保存调试图像到本地，直观查看
            try:
                debug_img = Image.fromarray((image_np * 255).astype(np.uint8))
                debug_img.save("mouse_draw_debug.png")
                logger.info(f"【调试】已保存调试图像到当前目录：mouse_draw_debug.png")
            except Exception as e:
                logger.error(f"【调试】保存调试图像失败：{e}")

            return (image_tensor,)

        except Exception as e:
            # 异常时返回红色错误图（和参考代码的异常处理逻辑一致）
            error_msg = f"生成手绘图像出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            error_image = torch.ones((1, 100, 100, 3), dtype=torch.float32)
            error_image[0, :, :, 1:] = 0  # 红色背景
            logger.info(f"【异常处理】返回红色错误图，张量形状：{error_image.shape}")
            return (error_image,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "MouseDrawNode": MouseDrawNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MouseDrawNode": "Mouse Draw Node"
}