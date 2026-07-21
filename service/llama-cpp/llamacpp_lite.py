import os
import sys
import json
import gc

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from base import (
    LLAMA_CPP_STORAGE, preset_prompts, preset_tags,
    load_text_presets, image_to_base64_jpeg, cqdm, _MTMD
)

_CACHE = {}

import folder_paths
import comfy.model_management as mm


def _load_lite_config():
    config_path = os.path.join(os.path.dirname(CURRENT_DIR), "aitools", "model_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        return cfg.get("lite_models", {})
    return {}


class llama_run_lite:
    @classmethod
    def INPUT_TYPES(s):
        lite_models = _load_lite_config()
        model_list = list(lite_models.keys())
        if not model_list:
            model_list = ["No models configured"]

        load_text_presets("V")

        return {
            "required": {
                "model": (model_list, {"default": model_list[0]}),
                "preset_prompt": (preset_tags, {"default": preset_tags[1] if len(preset_tags) > 1 else preset_tags[0]}),
                "custom_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "user_prompt"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
                "use_cache": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Use cached result from last run. Skips model inference and returns previous output."
                }),
                "use_inference": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Use LLM inference. If False, outputs the custom_prompt directly without calling the model."
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "images": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output", "user_prompt")
    FUNCTION = "run"
    CATEGORY = "luy/llama-cpp"

    def run(self, model, preset_prompt, custom_prompt, seed, use_cache, use_inference, unique_id, images=None):
        lite_models = _load_lite_config()
        cfg = lite_models.get(model)
        if cfg is None:
            raise ValueError(f"Model '{model}' not found in lite_models config")

        custom_config = {
            "model": cfg["model"],
            "mmproj": cfg.get("mmproj", ""),
            "chat_handler": cfg.get("chat_handler", "None"),
            "n_ctx": cfg.get("n_ctx", 8192),
            "vram_limit": -1,
            "image_min_tokens": 0,
            "image_max_tokens": 0,
            "draft_model_type": "None",
            "draft_ngram_size": 3,
            "draft_num_pred_tokens": 10,
            "enable_mtp": False,
        }

        if not LLAMA_CPP_STORAGE.llm or LLAMA_CPP_STORAGE.current_config != custom_config:
            LLAMA_CPP_STORAGE.load_model(custom_config)

        llama_model = LLAMA_CPP_STORAGE
        if not llama_model.llm:
            raise RuntimeError("The model has been unloaded or failed to load!")

        parameters = {
            "max_tokens": 2048,
            "top_k": 30,
            "top_p": 0.9,
            "min_p": 0.05,
            "typical_p": 1.0,
            "temperature": 0.8,
            "repeat_penalty": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 1.0,
            "mirostat_mode": 0,
            "mirostat_eta": 0.1,
            "mirostat_tau": 5.0,
        }
        if _MTMD:
            parameters.pop("presence_penalty", None)

        if images is not None:
            if hasattr(images, 'shape'):
                image_count = images.shape[0]
            else:
                image_count = len(images)
        else:
            image_count = 0

        inference_mode = "one by one" if image_count <= 1 else "images"

        if image_count == 0:
            system_prompt = "你是一名AI助手，擅长扩写用户的描述内容。"
        else:
            system_prompt = "你是一名图片分析专家，擅长将图片的内容详细描述出来。请使用中文回答。"

        messages = [{"role": "system", "content": system_prompt}]

        user_content = []
        if preset_prompt == "None":
            user_text = custom_prompt.strip()
        else:
            p = preset_prompts.get(preset_prompt, custom_prompt.strip())
            p = p.replace("{}", custom_prompt.strip())
            p = p.replace("@", "image")
            user_text = p
        user_content.append({"type": "text", "text": user_text})

        uid = unique_id.rpartition('.')[-1]

        if use_cache and uid in _CACHE:
            print(f"[llama-cpp_lite] Cache hit for node {uid}, skipping inference.")
            return _CACHE[uid]

        if not use_inference:
            print(f"[llama-cpp_lite] Inference disabled, returning custom_prompt directly.")
            return (custom_prompt.strip(), user_text)

        out1 = ""

        if images is not None and image_count > 0:
            if not hasattr(llama_model.chat_handler, "clip_model_path") or llama_model.chat_handler.clip_model_path is None:
                raise ValueError("Image input detected, but the loaded model is not configured with a mmproj module.")

            if inference_mode == "one by one":
                user_content.append({"type": "image_url", "image_url": {"url": ""}})
                messages.append({"role": "user", "content": user_content})

                for image in cqdm(images):
                    if mm.processing_interrupted():
                        raise mm.InterruptProcessingException()
                    data = image_to_base64_jpeg(image)
                    for item in user_content:
                        if item.get("type") == "image_url":
                            item["image_url"]["url"] = f"data:image/jpeg;base64,{data}"
                            break
                    output = llama_model.llm.create_chat_completion(messages=messages, seed=seed, **parameters)
                    out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
                    data = None
            else:
                for image in images:
                    data = image_to_base64_jpeg(image)
                    user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}})
                messages.append({"role": "user", "content": user_content})
                output = llama_model.llm.create_chat_completion(messages=messages, seed=seed, **parameters)
                out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
        else:
            messages.append({"role": "user", "content": user_content})
            output = llama_model.llm.create_chat_completion(messages=messages, seed=seed, **parameters)
            out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()

        del messages
        gc.collect()

        LLAMA_CPP_STORAGE.clean_state(uid)
        LLAMA_CPP_STORAGE.clean()

        _CACHE[uid] = (out1, user_text)
        return (out1, user_text)


NODE_CLASS_MAPPINGS = {"llama_run_lite": llama_run_lite}
NODE_DISPLAY_NAME_MAPPINGS = {"llama_run_lite": "Llama-cpp Run Lite"}
