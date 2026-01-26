class PainterPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt_1": ("STRING", {"multiline": True, "default": ""}),
            "prompt_2": ("STRING", {"multiline": True, "default": ""}),
            "prompt_3": ("STRING", {"multiline": True, "default": ""}),
        },
            "optional": {
                "optional_prompt_list": ("LIST",)
            }
        }

    RETURN_TYPES = ("LIST", "STRING")
    RETURN_NAMES = ("prompt_list", "prompt_strings")
    OUTPUT_IS_LIST = (False, True)
    FUNCTION = "run"
    CATEGORY = "Painter/Prompt"

    def run(self, **kwargs):
        prompts = []

        if "optional_prompt_list" in kwargs:
            for l in kwargs["optional_prompt_list"]:
                prompts.append(l)

        for k in sorted(kwargs.keys()):
            v = kwargs[k]
            if isinstance(v, str) and v != '':
                prompts.append(v)

        return (prompts, prompts)


NODE_CLASS_MAPPINGS = {
    "PainterPrompt": PainterPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PainterPrompt": "Painter Prompt",
}
