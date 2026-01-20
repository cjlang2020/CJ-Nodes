import numpy as np
from PIL import Image
import base64
import io
import hashlib
import torch
_cache = {}
_max_cache_size = 50


class QwenMultiangleCameraNode:
    """
    3D Camera Angle Control Node
    Provides a 3D scene to adjust camera angles and outputs a formatted prompt string
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "horizontal_angle": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 360,
                    "step": 1,
                    "display": "slider"
                }),
                "vertical_angle": ("INT", {
                    "default": 0,
                    "min": -30,
                    "max": 90,
                    "step": 1,
                    "display": "slider"
                }),
                "zoom": ("FLOAT", {
                    "default": 5.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            },
            "optional": {
                "image": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "luy/镜头控制"
    OUTPUT_NODE = True

    def generate_prompt(self, horizontal_angle, vertical_angle, zoom, image=None, unique_id=None):
        h_angle = horizontal_angle % 360
        if h_angle < 22.5 or h_angle >= 337.5:
            h_direction = "front view"
        elif h_angle < 67.5:
            h_direction = "front-right view"
        elif h_angle < 112.5:
            h_direction = "right side view"
        elif h_angle < 157.5:
            h_direction = "back-right view"
        elif h_angle < 202.5:
            h_direction = "back view"
        elif h_angle < 247.5:
            h_direction = "back-left view"
        elif h_angle < 292.5:
            h_direction = "left side view"
        else:
            h_direction = "front-left view"

        if vertical_angle < -15:
            v_direction = "low angle"
        elif vertical_angle < 15:
            v_direction = "eye level"
        elif vertical_angle < 45:
            v_direction = "high angle"
        elif vertical_angle < 75:
            v_direction = "bird's eye view"
        else:
            v_direction = "top-down view"

        if zoom < 2:
            distance = "wide shot"
        elif zoom < 4:
            distance = "medium-wide shot"
        elif zoom < 6:
            distance = "medium shot"
        elif zoom < 8:
            distance = "medium close-up"
        else:
            distance = "close-up"

        prompt = f"{h_direction}, {v_direction}, {distance}"
        prompt += f" (horizontal: {horizontal_angle}, vertical: {vertical_angle}, zoom: {zoom:.1f})"

        # Convert image to base64 for frontend display
        image_base64 = ""
        if image is not None:
            img_tensor = image[0] if len(image.shape) == 4 else image
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            image_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"ui": {"image_base64": [image_base64]}, "result": (prompt,)}

    @classmethod
    def IS_CHANGED(cls, horizontal_angle, vertical_angle, zoom, image=None, unique_id=None):
        import time
        return time.time()

class QwenPlusMultiangleCameraNode:
    """
    3D Camera Angle Control Node
    Provides a 3D scene to adjust camera angles and outputs a formatted prompt string
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "horizontal_angle": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 360,
                    "step": 1,
                    "display": "slider"
                }),
                "vertical_angle": ("INT", {
                    "default": 0,
                    "min": -30,
                    "max": 90,
                    "step": 1,
                    "display": "slider"
                }),
                "zoom": ("FLOAT", {
                    "default": 5.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            },
            "optional": {
                "image": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "luy/镜头控制"
    OUTPUT_NODE = True

    def generate_prompt(self, horizontal_angle, vertical_angle, zoom, image=None, unique_id=None):
        h_angle = horizontal_angle % 360
        if h_angle < 22.5 or h_angle >= 337.5:
            h_direction = "front view"
        elif h_angle < 67.5:
            h_direction = "front-right view"
        elif h_angle < 112.5:
            h_direction = "right side view"
        elif h_angle < 157.5:
            h_direction = "back-right view"
        elif h_angle < 202.5:
            h_direction = "back view"
        elif h_angle < 247.5:
            h_direction = "back-left view"
        elif h_angle < 292.5:
            h_direction = "left side view"
        else:
            h_direction = "front-left view"

        if vertical_angle < -15:
            v_direction = "low angle"
        elif vertical_angle < 15:
            v_direction = "eye level"
        elif vertical_angle < 45:
            v_direction = "high angle"
        elif vertical_angle < 75:
            v_direction = "bird's eye view"
        else:
            v_direction = "top-down view"

        if zoom < 2:
            distance = "wide shot"
        elif zoom < 4:
            distance = "medium-wide shot"
        elif zoom < 6:
            distance = "medium shot"
        elif zoom < 8:
            distance = "medium close-up"
        else:
            distance = "close-up"

        prompt = f"{h_direction}, {v_direction}, {distance}"
        prompt += f" (horizontal: {horizontal_angle}, vertical: {vertical_angle}, zoom: {zoom:.1f})"

        # Convert image to base64 for frontend display
        image_base64 = ""
        if image is not None:
            img_tensor = image[0] if len(image.shape) == 4 else image
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            image_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"ui": {"image_base64": [image_base64]}, "result": (prompt,)}

    @classmethod
    def IS_CHANGED(cls, horizontal_angle, vertical_angle, zoom, image=None, unique_id=None):
        import time
        return time.time()


class QwenLoraMultiangleCameraNode:
    """
    3D Camera Angle Control Node
    Provides a 3D scene to adjust camera angles and outputs a formatted prompt string
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "horizontal_angle": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 360,
                    "step": 1,
                    "display": "slider"
                }),
                "vertical_angle": ("INT", {
                    "default": 0,
                    "min": -30,
                    "max": 90,
                    "step": 1,
                    "display": "slider"
                }),
                "zoom": ("FLOAT", {
                    "default": 5.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            },
            "optional": {
                "image": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "luy/镜头控制"
    OUTPUT_NODE = True

    def generate_prompt(self, horizontal_angle, vertical_angle, zoom, image=None, unique_id=None):
        h_angle = horizontal_angle % 360
        if h_angle < 22.5 or h_angle >= 337.5:
            h_direction = "front view"
        elif h_angle < 67.5:
            h_direction = "front-right view quarter view"
        elif h_angle < 112.5:
            h_direction = "right side view"
        elif h_angle < 157.5:
            h_direction = "back-right view quarter view"
        elif h_angle < 202.5:
            h_direction = "back view"
        elif h_angle < 247.5:
            h_direction = "back-left view quarter view"
        elif h_angle < 292.5:
            h_direction = "left side view"
        else:
            h_direction = "front-left view quarter view"

        if vertical_angle < -15:
            v_direction = "low-angle shot"
        elif vertical_angle < 15:
            v_direction = "eye-level shot"
        elif vertical_angle < 45:
            v_direction = "elevated shot"
        else:
            v_direction = "high-angle shot"

        if zoom < 1:
            distance = "close-up"
        elif zoom < 5:
            distance = "medium shot"
        else:
            distance = "wide shot"

        prompt = f"<sks> {h_direction} {v_direction} {distance}"

        # Convert image to base64 for frontend display
        image_base64 = ""
        if image is not None:
            img_tensor = image[0] if len(image.shape) == 4 else image
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            image_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"ui": {"image_base64": [image_base64]}, "result": (prompt,)}

    @classmethod
    def IS_CHANGED(cls, horizontal_angle, vertical_angle, zoom, image=None, unique_id=None):
        import time
        return time.time()




class QwenMultiangleLightningNode:
    """
    Lighting Control Node - Extreme Stability Edition
    Strictly maintains scene and character while only adjusting the lighting profile.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "light_azimuth": ("INT", {
                    "default": 0, "min": 0, "max": 360, "step": 1, "display": "slider"
                }),
                "light_elevation": ("INT", {
                    "default": 30, "min": -90, "max": 90, "step": 1, "display": "slider"
                }),
                "light_intensity": ("FLOAT", {
                    "default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1, "display": "slider"
                }),
                "light_color_hex": ("COLOR", {"default": "#FFFFFF"}),
                "show_light": ("BOOLEAN", {
                    "default": False, "display": "checkbox"
                }),
                "cinematic_mode": ("BOOLEAN", {
                    "default": True, "display": "checkbox"
                }),
            },
            "optional": {
                "image": ("IMAGE",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("lighting_prompt",)
    FUNCTION = "generate_lighting_prompt"
    CATEGORY = "luy/镜头控制"
    OUTPUT_NODE = True

    def _compute_image_hash(self, image):
        if image is None: return None
        try:
            if hasattr(image, 'cpu'):
                img_np = image[0].cpu().numpy() if len(image.shape) == 4 else image.cpu().numpy()
            else:
                img_np = image.numpy()[0] if hasattr(image, 'numpy') and len(image.shape) == 4 else image
            return hashlib.md5(img_np.tobytes()).hexdigest()
        except:
            return str(hash(str(image)))

    def generate_lighting_prompt(self, light_azimuth, light_elevation, light_intensity, light_color_hex, cinematic_mode=True, image=None, unique_id=None):
        cache_key = str(unique_id) if unique_id else "default"
        image_hash = self._compute_image_hash(image)
        cached = _cache.get(cache_key, {})

        if (cached.get('azimuth') == light_azimuth and
            cached.get('elevation') == light_elevation and
            cached.get('intensity') == light_intensity and
            cached.get('color') == light_color_hex and
            cached.get('cinematic') == cinematic_mode and
            cached.get('image_hash') == image_hash):
            return cached['result']

        # 1. 映射光照方位描述
        az = light_azimuth % 360
        if az < 22.5 or az >= 337.5: pos_desc = "light hitting from the front"
        elif az < 67.5: pos_desc = "light hitting from the front-right side"
        elif az < 112.5: pos_desc = "light hitting from the right (90 degrees)"
        elif az < 157.5: pos_desc = "light hitting from the back-right"
        elif az < 202.5: pos_desc = "backlighting, light from behind"
        elif az < 247.5: pos_desc = "light hitting from the back-left"
        elif az < 292.5: pos_desc = "light hitting from the left (90 degrees)"
        else: pos_desc = "light hitting from the front-left side"

        # 2. 映射光照高度（避免使用俯仰角相关词汇）
        if light_elevation <= -60: elev_desc = "extreme low-angle light source, strong bottom-up shadow"
        elif light_elevation < -30: elev_desc = "low-level light source, bottom-up shadow"
        elif light_elevation < 20: elev_desc = "horizontal light source"
        elif light_elevation < 60: elev_desc = "high-positioned light source"
        else: elev_desc = "top-down ceiling light source"

        # 3. 强度描述
        if light_intensity < 3.0: int_desc = "soft ambient"
        elif light_intensity < 7.0: int_desc = "bright directional"
        else: int_desc = "strong dramatic contrast"

        # --- 核心修改：极致场景与镜头锁定 ---
        # 加入了 SCENE LOCK 和 CONSTANT BACKGROUND 等强力提示词
        global_constraints = (
            "SCENE LOCK, CONSTANT BACKGROUND, FIXED SCENERY. " # 锁定场景和背景
            "STATIC SHOT, FIXED VIEWPOINT, NO CAMERA MOVEMENT. " # 锁定镜头
            "maintaining character consistency, "
            "keeping the same character pose and action, "
            "maintaining the same composition, "
            "RELIGHTING ONLY: only the light rays and shadows change, the scene remains untouched. " # 明确重塑光影任务
        )

        color_desc = f"colored light (hex: {light_color_hex})"
        detail_prompt = f"{int_desc} {color_desc}, {pos_desc}, {elev_desc}"

        if cinematic_mode:
            prompt = f"{global_constraints}professional cinematic relighting, {detail_prompt}, raytraced shadows, realistic global illumination"
        else:
            prompt = f"{global_constraints}{detail_prompt}"

        # 预览图处理
        image_base64 = ""
        if image is not None:
            try:
                i = 255. * image[0].cpu().numpy()
                img_np = np.clip(i, 0, 255).astype(np.uint8)
                pil_image = Image.fromarray(img_np)
                buffer = io.BytesIO()
                pil_image.save(buffer, format="PNG")
                image_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            except: pass

        result = {"ui": {"image_base64": [image_base64]}, "result": (prompt,)}

        _cache[cache_key] = {
            'azimuth': light_azimuth, 'elevation': light_elevation,
            'intensity': light_intensity, 'color': light_color_hex,
            'cinematic': cinematic_mode, 'image_hash': image_hash,
            'result': result
        }

        return result