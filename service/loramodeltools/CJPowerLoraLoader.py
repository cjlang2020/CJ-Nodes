import json
import os
import folder_paths
import comfy.sd
import comfy.utils


def read_metadata(file_path):
    with open(file_path, "rb") as f:
        header = f.read(8)
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        return json.loads(header_data).get("__metadata__", {})


class CJPowerLoraLoader:
    def __init__(self):
        self.loaded_loras = {}

    @classmethod
    def INPUT_TYPES(cls):
        all_loras = folder_paths.get_filename_list("loras")
        loras_json = json.dumps(all_loras, ensure_ascii=False)
        return {
            "required": {
                "model": ("MODEL",),
            },
            "optional": {
                "loras_data": ("STRING", {
                    "multiline": True,
                    "default": "[]",
                }),
                "loras_list": ("STRING", {
                    "multiline": True,
                    "default": loras_json,
                }),
            },
        }

    RETURN_TYPES = ("MODEL", "STRING")
    RETURN_NAMES = ("model", "lora_trigger_text")
    OUTPUT_TOOLTIPS = ("应用所有LoRA后的模型", "所有启用的LoRA触发词，用逗号拼接")
    FUNCTION = "load_loras"
    CATEGORY = "luy/模型加载"
    DESCRIPTION = "支持动态添加多个LoRA，自动拼接每个LoRA的内置触发词"

    def load_loras(self, model, loras_data="[]", loras_list=""):
        try:
            data = json.loads(loras_data)
        except json.JSONDecodeError:
            data = []

        trigger_words = []
        for item in data:
            if not item.get("on"):
                continue
            strength = item.get("strength", 0)
            if strength == 0:
                continue
            lora_name = item.get("lora", "")
            if not lora_name:
                continue

            lora_file = self._find_lora(lora_name)
            if lora_file is None:
                continue

            lora_path = folder_paths.get_full_path("loras", lora_file)
            if not lora_path or not os.path.isfile(lora_path):
                continue

            if lora_path in self.loaded_loras:
                lora = self.loaded_loras[lora_path]
            else:
                lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
                self.loaded_loras[lora_path] = lora

            model, _ = comfy.sd.load_lora_for_models(model, None, lora, strength, 0)

            try:
                meta = read_metadata(lora_path)
                if "lora_keywords" in meta and meta["lora_keywords"]:
                    trigger_words.append(meta["lora_keywords"])
            except Exception:
                pass

        trigger_text = ", ".join(filter(None, trigger_words))
        return (model, trigger_text)

    def _find_lora(self, name):
        lora_paths = folder_paths.get_filename_list("loras")
        if name in lora_paths:
            return name
        name_no_ext = os.path.splitext(name)[0]
        for lp in lora_paths:
            if lp == name_no_ext or os.path.splitext(lp)[0] == name_no_ext:
                return lp
            if os.path.basename(lp) == name or os.path.splitext(os.path.basename(lp))[0] == name_no_ext:
                return lp
        return None

    @classmethod
    def IS_CHANGED(cls, model, loras_data="[]", loras_list=""):
        return loras_data


try:
    from aiohttp import web
    import server
    if server.PromptServer.instance is not None:
        @server.PromptServer.instance.routes.get("/cj-nodes/loras-list")
        async def get_loras_list(request):
            loras = folder_paths.get_filename_list("loras")
            return web.json_response(loras)
except Exception:
    pass
