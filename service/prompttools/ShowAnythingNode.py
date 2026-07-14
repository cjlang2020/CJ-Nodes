import json


class ShowAnything:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
                "use_edited": ("BOOLEAN", {"default": False, "label_on": "保留编辑", "label_off": "显示输入"}),
            },
            "optional": {
                "anything": ("*",),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "extra_pnginfo": "EXTRA_PNGINFO",
            }
        }

    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("output",)
    FUNCTION = "show"
    CATEGORY = "luy/提示词"
    OUTPUT_NODE = True

    def show(self, text, use_edited, anything=None, unique_id=None, extra_pnginfo=None):
        if use_edited:
            return (text,)

        values = []
        if anything is not None:
            if isinstance(anything, str):
                values.append(anything)
            elif isinstance(anything, (int, float, bool)):
                values.append(str(anything))
            elif isinstance(anything, list):
                for val in anything:
                    if isinstance(val, str):
                        values.append(val)
                    elif isinstance(val, (int, float, bool)):
                        values.append(str(val))
                    else:
                        try:
                            values.append(json.dumps(val, indent=4, ensure_ascii=False))
                        except Exception:
                            try:
                                values.append(str(val))
                            except Exception:
                                pass
            else:
                try:
                    values.append(json.dumps(anything, indent=4, ensure_ascii=False))
                except Exception:
                    try:
                        values.append(str(anything))
                    except Exception:
                        raise Exception("source exists, but could not be serialized.")

        display_text = "\n".join(values) if len(values) > 1 else (values[0] if values else "")

        if extra_pnginfo and isinstance(extra_pnginfo, dict) and "workflow" in extra_pnginfo:
            _uid = unique_id[0] if isinstance(unique_id, list) else unique_id
            node = next((x for x in extra_pnginfo["workflow"]["nodes"] if str(x["id"]) == _uid), None)
            if node:
                node["widgets_values"] = [display_text, use_edited]

        return (anything,)
