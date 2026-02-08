import torch  # 确保导入torch（若已导入可忽略）
import comfy.sd
import folder_paths

class LuyDualCLIPLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip_name1": (folder_paths.get_filename_list("text_encoders"), ),
                "clip_name2": (folder_paths.get_filename_list("text_encoders"), ),
                "type": (["sdxl", "sd3", "flux", "hunyuan_video", "hidream", "hunyuan_image", "hunyuan_video_15", "kandinsky5", "kandinsky5_image", "ltxv", "newbie", "ace"], ),
            },
            "optional": {
                # 关键修改1：添加gpu选项到device下拉列表
                "device": (["default", "cpu", "gpu"], {"advanced": True}),
            }
        }
    RETURN_TYPES = ("CLIP",)
    FUNCTION = "load_clip"
    CATEGORY = "luy"
    DESCRIPTION = "[Recipes]\n\nsdxl: clip-l, clip-g\nsd3: clip-l, clip-g / clip-l, t5 / clip-g, t5\nflux: clip-l, t5\nhidream: at least one of t5 or llama, recommended t5 and llama\nhunyuan_image: qwen2.5vl 7b and byt5 small\nnewbie: gemma-3-4b-it, jina clip v2"

    def load_clip(self, clip_name1, clip_name2, type, device="default"):
        clip_type = getattr(comfy.sd.CLIPType, type.upper(), comfy.sd.CLIPType.STABLE_DIFFUSION)
        clip_path1 = folder_paths.get_full_path_or_raise("text_encoders", clip_name1)
        clip_path2 = folder_paths.get_full_path_or_raise("text_encoders", clip_name2)

        model_options = {}
        # 关键修改2：新增gpu分支，配置cuda设备
        if device == "cpu":
            model_options["load_device"] = model_options["offload_device"] = torch.device("cpu")
        elif device == "gpu":
            # 优先使用cuda:0，若需指定多卡可改为cuda:1/cuda:2等
            model_options["load_device"] = model_options["offload_device"] = torch.device("cuda:0")
        # default分支不做任何配置，沿用ComfyUI原生逻辑

        clip = comfy.sd.load_clip(
            ckpt_paths=[clip_path1, clip_path2],
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
            clip_type=clip_type,
            model_options=model_options
        )
        return (clip,)

NODE_CLASS_MAPPINGS = {
    "LuyDualCLIPLoader": LuyDualCLIPLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LuyDualCLIPLoader": "Luy-DualCLIPLoader"
}