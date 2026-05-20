# llamacpp_image.py - 仅包含 llama_run_simple 类
# 共享代码已移至 base.py

import os
import sys

# 动态设置路径以支持 base.py 导入
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import gc
import numpy as np

from base import (
    LLAMA_CPP_STORAGE, any_type, chat_handlers, preset_prompts, preset_tags,
    load_text_presets, tensor_to_numpy, image_to_base64_jpeg, cqdm, draft_model_types, _MTMD,
    BASE_NODE_CLASS_MAPPINGS, BASE_NODE_DISPLAY_NAME_MAPPINGS
)

import folder_paths
import comfy.model_management as mm


class llama_run_simple:
    @classmethod
    def INPUT_TYPES(s):
        all_llms = folder_paths.get_filename_list("LLM")
        model_list = [f for f in all_llms if "mmproj" not in f.lower()]
        mmproj_list = ["None"]+[f for f in all_llms if "mmproj" in f.lower()]
        # 加载 aitools 下 T 和 V 目录的所有 txt 文件作为 preset_prompts
        load_text_presets("V")
        load_text_presets("T")
        return {
            "required": {
                "model": (model_list,{"default": "Qwen3.5/4B/Qwen3.5-4B-Q4_K_S.gguf"}),
                "mmproj": (mmproj_list, {"default": "Qwen3.5/4B/mmproj-BF16.gguf"}),
                "chat_handler": (chat_handlers, {"default": "Qwen3.5"}),
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
                "preset_prompt": (preset_tags, {"default": preset_tags[1]}),
                "ChineseReply": ("BOOLEAN", {"default": False}),
                "custom_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": 'user_prompt'}),
                "unload_model": ("BOOLEAN", {"default": True, "tooltip": "Unload model after inference. If True, calls clean_state to release resources."}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1, "tooltip": "Random seed for ensuring execution each run."}),
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
                "enable_mtp": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Multi-Token Prediction (MTP) acceleration.\nRequires a model with MTP support (e.g., Qwen3 variants)."
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "images": ("IMAGE",),
                "queue_handler": (any_type, {"tooltip": "Used to control the execution order of instruct nodes."}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("output", "output_list", "state_uid", "system_prompt", "user_prompt")
    OUTPUT_IS_LIST = (False, True, False, False, False)
    FUNCTION = "run"
    CATEGORY = "luy/llama-cpp"

    def run(self, model, mmproj, chat_handler, n_ctx, vram_limit,
            preset_prompt, ChineseReply, custom_prompt, unload_model, seed,
            draft_model_type, draft_ngram_size, draft_num_pred_tokens, enable_mtp,
            unique_id, images=None, queue_handler=None):
        custom_config = {
            "model": model,
            "mmproj": mmproj,
            "chat_handler": chat_handler,
            "n_ctx": n_ctx,
            "vram_limit": vram_limit,
            "image_min_tokens": 0,
            "image_max_tokens": 0,
            "draft_model_type": draft_model_type,
            "draft_ngram_size": draft_ngram_size,
            "draft_num_pred_tokens": draft_num_pred_tokens,
            "enable_mtp": enable_mtp
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
            "state_uid": -1
        }

        _parameters = parameters.copy()
        _parameters.pop("state_uid", None)
        if _MTMD:
            _parameters.pop("presence_penalty", None)
        uid = unique_id.rpartition('.')[-1]
        messages = []
        # 判断图片数量
        if images is not None:
            if hasattr(images, 'shape'):
                image_count = images.shape[0]
            else:
                image_count = len(images)
        else:
            image_count = 0

        # 自动设置默认系统提示词
        if image_count == 0:
            system_prompt_text = "你是一名AI助手，擅长扩写用户的描述内容。"
        elif image_count == 1:
            system_prompt_text = "你是一名图片分析专家，擅长将图片的内容详细描述出来！"
        else:
            system_prompt_text = "你是一名视频描述专家，擅长将不同图片帧的内容描述出来，同时能将不同画面之间的关系进行连贯描述，擅长分析前后图片之间的过度关系，符合画面的连贯关系！"
        if ChineseReply:
            system_prompt_text += ",\n请使用中文回答。"
        else:
            system_prompt_text += ",\nPlease answer in English."
        messages.append({"role": "system", "content": system_prompt_text})

        out1 = ""
        out2 = []
        user_content = []
        # 根据 preset_prompt 是否为 None 决定用户提示词内容
        if preset_prompt == "None":
            # preset_prompt 为 None 时，完全使用 custom_prompt
            user_text = custom_prompt.strip()
            user_content.append({"type": "text", "text": user_text})
        else:
            # preset_prompt 不为 None 时，获取预设值并替换 {} 为 custom_prompt
            p = preset_prompts[preset_prompt]
            # 替换 {} 为 custom_prompt 内容
            p = p.replace("{}", custom_prompt.strip())
            # 替换 @ 为 image
            p = p.replace("@", "image")
            user_text = p
            user_content.append({"type": "text", "text": p})

        if images is not None:
            if not hasattr(llama_model.chat_handler, "clip_model_path") or llama_model.chat_handler.clip_model_path is None:
                raise ValueError("Image input detected, but the loaded model is not configured with a mmproj module.")

            image_content = {
                "type": "image_url",
                "image_url": {"url": ""}
            }
            user_content.append(image_content)
            messages.append({"role": "user", "content": user_content})

            for i, image in enumerate(cqdm(images)):
                if mm.processing_interrupted():
                    raise mm.InterruptProcessingException()
                data = image_to_base64_jpeg(image)
                for item in user_content:
                    if item.get("type") == "image_url":
                        item["image_url"]["url"] = f"data:image/jpeg;base64,{data}"
                        break
                output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **_parameters)
                text = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
                out2.append(text)
                if len(images) > 1:
                    out1 += f"====== Image {i+1} ======\n{text}\n\n"
                else:
                    out1 = text
                data = None

        else:
            messages.append({"role": "user", "content": user_content})
            output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **_parameters)
            out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
            out2 = [out1]

        del messages
        gc.collect()

        # 根据参数决定是否卸载模型（释放显存）
        if unload_model:
            #print("[llama-cpp_vlm] Unloading model and releasing VRAM...")
            LLAMA_CPP_STORAGE.clean_state(uid)
            LLAMA_CPP_STORAGE.clean()

        return (out1, out2, uid, system_prompt_text, user_text)


# 合并基础节点映射和当前文件的独有节点
NODE_CLASS_MAPPINGS = {**BASE_NODE_CLASS_MAPPINGS, "llama_run_simple": llama_run_simple}
NODE_DISPLAY_NAME_MAPPINGS = {**BASE_NODE_DISPLAY_NAME_MAPPINGS, "llama_run_simple": "Llama-cpp Run Simple"}