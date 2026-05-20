# llamacpp_text.py - 仅包含 llama_text_simple 类
# 共享代码已移至 base.py

import os
import sys

# 动态设置路径以支持 base.py 导入
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import gc

from base import (
    LLAMA_CPP_STORAGE, any_type, preset_prompts, preset_tags,
    load_text_presets, draft_model_types, _MTMD,
    BASE_NODE_CLASS_MAPPINGS, BASE_NODE_DISPLAY_NAME_MAPPINGS
)

import folder_paths


class llama_text_simple:
    @classmethod
    def INPUT_TYPES(s):
        all_llms = folder_paths.get_filename_list("LLM")
        model_list = [f for f in all_llms if "mmproj" not in f.lower()]
        load_text_presets("T")
        return {
            "required": {
                "model": (model_list,{"default": "Qwen3-VL-4B-Instruct-abliterated-Q5_K_M.gguf"}),
                "n_ctx": ("INT", {
                    "default": 8192,
                    "min": 2000, "max": 327680, "step": 128,
                    "tooltip": "Context length limit."
                }),
                "vram_limit": ("INT", {
                    "default": -1,
                    "min": -1, "max": 1024, "step": 1,
                    "tooltip": "VRAM usage limit in GB (-1 = no limit)"
                }),
                "preset_prompt": (preset_tags, {"default": preset_tags[0]}),
                "ChineseReply": ("BOOLEAN", {"default": False}),
                "custom_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": 'user_prompt'}),
                "draft_model_type": (draft_model_types, {
                    "default": "None",
                    "tooltip": "Speculative decoding draft model.\nngram-map: Fast hash-based ngram matching (recommended)\nprompt-lookup: Legacy sliding window search\nNone: No speculative decoding"
                }),
                "draft_ngram_size": ("INT", {
                    "default": 3, "min": 1, "max": 10, "step": 1,
                    "tooltip": "N-gram size for draft model matching."
                }),
                "draft_num_pred_tokens": ("INT", {
                    "default": 10, "min": 1, "max": 32, "step": 1,
                    "tooltip": "Max number of tokens to predict per draft step."
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "queue_handler": (any_type, {"tooltip": "Used to control the execution order of instruct nodes."}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("output", "output_list", "state_uid")
    OUTPUT_IS_LIST = (False, True, False)
    FUNCTION = "run"
    CATEGORY = "luy/llama-cpp"

    def run(self, model, n_ctx, vram_limit, preset_prompt, ChineseReply, custom_prompt,
            draft_model_type, draft_ngram_size, draft_num_pred_tokens,
            unique_id, queue_handler=None):
        custom_config = {
            "model": model,
            "mmproj": "None",
            "chat_handler": "None",
            "n_ctx": n_ctx,
            "vram_limit": vram_limit,
            "image_min_tokens": 0,
            "image_max_tokens": 0,
            "draft_model_type": draft_model_type,
            "draft_ngram_size": draft_ngram_size,
            "draft_num_pred_tokens": draft_num_pred_tokens
        }

        if not LLAMA_CPP_STORAGE.llm or LLAMA_CPP_STORAGE.current_config != custom_config:
            #print("[llama-cpp_vlm] Loading model...")
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

        uid = unique_id.rpartition('.')[-1]
        messages = []
        user_content = []

        if ChineseReply:
            messages.append({"role": "system", "content": "请使用中文回答。"})
        else:
            messages.append({"role": "system", "content": "Please answer in English."})

        if custom_prompt.strip():
            user_content.append({"type": "text", "text": custom_prompt.strip()})
        else:
            p = preset_prompts.get(preset_prompt, "")
            user_content.append({"type": "text", "text": p})

        messages.append({"role": "user", "content": user_content})
        output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **parameters)
        out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
        out2 = [out1]

        del messages
        gc.collect()
        return (out1, out2, uid)


# 合并基础节点映射和当前文件的独有节点
NODE_CLASS_MAPPINGS = {**BASE_NODE_CLASS_MAPPINGS, "llama_text_simple": llama_text_simple}
NODE_DISPLAY_NAME_MAPPINGS = {**BASE_NODE_DISPLAY_NAME_MAPPINGS, "llama_text_simple": "Llama-cpp Text Simple"}