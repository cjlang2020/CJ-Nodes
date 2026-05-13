# llamacpp.py - 仅包含 llama_run 类
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
    load_text_presets, image2base64, scale_image, cqdm,
    BASE_NODE_CLASS_MAPPINGS, BASE_NODE_DISPLAY_NAME_MAPPINGS
)

import folder_paths
import comfy.model_management as mm


class llama_run:
    @classmethod
    def INPUT_TYPES(s):
        all_llms = folder_paths.get_filename_list("LLM")
        model_list = [f for f in all_llms if "mmproj" not in f.lower()]
        mmproj_list = ["None"]+[f for f in all_llms if "mmproj" in f.lower()]
        load_text_presets("V")
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
                    "tooltip": "VRAM usage limit in GB (-1 = no limit)\nReference range; actual usage may slightly exceed."
                }),
                "preset_prompt": (preset_tags, {"default": preset_tags[1]}),
                "ChineseReply": ("BOOLEAN", {"default": False}),
                "custom_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": 'user_prompt\n\nFor preset hints marked with an "*", this will be used to fill the placeholder (e.g., Object names in BBox detection)\nOtherwise, this will override the preset prompts.'}),
                "system_prompt": ("STRING", {"multiline": True, "default": ""}),
                "image_min_tokens": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
                "image_max_tokens": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
                "max_tokens": ("INT", {"default": 2048, "min": 0, "max": 4096, "step": 1}),
                "top_k": ("INT", {"default": 30, "min": 0, "max": 1000, "step": 1}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "min_p": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "typical_p": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "temperature": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0, "step": 0.01}),
                "repeat_penalty": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "frequency_penalty": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "presence_penalty": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "mirostat_mode": ("INT", {"default": 0, "min": 0, "max": 2, "step": 1}),
                "mirostat_eta": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.01}),
                "mirostat_tau": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "inference_mode": (["one by one", "images", "video"], {
                    "default": "one by one",
                    "tooltip": "one by one: Read one image at a time\nimages:  \tRead all images at once\nvideo:  \tTreat the input images as video"
                }),
                "max_frames": ("INT", {
                    "default": 24,
                    "min": 2,
                    "max": 1024,
                    "step": 1,
                    "tooltip": 'Number of frames to sample evenly from input video.\n(for "video" mode only)'
                }),
                "max_size": ("INT", {
                    "default": 256,
                    "min": 128,
                    "max": 16384,
                    "step": 64,
                    "tooltip": 'Max size of input images in "images" and "video" modes.'
                }),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1}),
                "force_offload": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Unload the model after inference."
                }),
                "save_states": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Preserve the context of this conversation in RAM."
                }),
                "state_uid": ("INT", {
                    "default": -1, "min": -1, "max": 999999, "step": 1,
                    "tooltip": "Use a specific ID to save the conversation state.\n(-1 = use node's unique_id)"
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

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("output", "output_list", "state_uid")
    OUTPUT_IS_LIST = (False, True, False)
    FUNCTION = "run"
    CATEGORY = "luy/llama-cpp"

    def sanitize_messages(self, messages):
        clean_messages = messages.copy()
        for msg in clean_messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        item["image_url"]["url"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAADElEQVQImWP4//8/AAX+Av5Y8msOAAAAAElFTkSuQmCC"
        return clean_messages

    def run(self, model, mmproj, chat_handler, n_ctx, vram_limit, image_min_tokens, image_max_tokens,
            max_tokens, top_k, top_p, min_p, typical_p, temperature, repeat_penalty,
            frequency_penalty, presence_penalty, mirostat_mode, mirostat_eta, mirostat_tau,
            preset_prompt, ChineseReply, custom_prompt, system_prompt, inference_mode, max_frames,
            max_size, seed, force_offload, save_states, state_uid, unique_id, images=None, queue_handler=None):
        custom_config = {
            "model": model,
            "mmproj": mmproj,
            "chat_handler": chat_handler,
            "n_ctx": n_ctx,
            "vram_limit": vram_limit,
            "image_min_tokens": image_min_tokens,
            "image_max_tokens": image_max_tokens
        }

        if not LLAMA_CPP_STORAGE.llm or LLAMA_CPP_STORAGE.current_config != custom_config:
            #print("[llama-cpp_vlm] Loading model...")
            LLAMA_CPP_STORAGE.load_model(custom_config)

        llama_model = LLAMA_CPP_STORAGE

        if not llama_model.llm:
            raise RuntimeError("The model has been unloaded or failed to load!")

        parameters = {
            "max_tokens": max_tokens,
            "top_k": top_k,
            "top_p": top_p,
            "min_p": min_p,
            "typical_p": typical_p,
            "temperature": temperature,
            "repeat_penalty": repeat_penalty,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "mirostat_mode": mirostat_mode,
            "mirostat_eta": mirostat_eta,
            "mirostat_tau": mirostat_tau,
            "state_uid": state_uid
        }

        try:
            from llama_cpp.llama_chat_format import MTMDChatHandler
            _MTMD = True
        except:
            _MTMD = False

        if _MTMD:
            parameters.pop("presence_penalty", None)

        _parameters = parameters.copy()
        _parameters.pop("state_uid", None)
        uid = unique_id.rpartition('.')[-1] if state_uid in (None, -1) else state_uid

        last_sys_prompt = llama_model.sys_prompts.get(f"{uid}", None)
        video_input = inference_mode == "video"
        system_prompts = "请将输入的图片序列当做视频而不是静态帧序列, " + system_prompt if video_input else system_prompt
        if last_sys_prompt != system_prompts:
            messages = []
            llama_model.clean_state()
            llama_model.sys_prompts[f"{uid}"] = system_prompts
            if system_prompts.strip():
                messages.append({"role": "system", "content": system_prompts})
        else:
            if save_states:
                try:
                    #print(f"[llama-cpp_vlm] Loading state and history id={uid}...")
                    messages = llama_model.messages.get(f"{uid}", [])
                except Exception as e:
                    messages = []
            else:
                messages = []
        out1 = ""
        out2 = []
        user_content = []
        if custom_prompt.strip() and "*" not in preset_prompt:
            user_content.append({"type": "text", "text": custom_prompt})
        else:
            p = preset_prompts[preset_prompt].replace("#", custom_prompt.strip()).replace("@", "video" if video_input else "image")
            if ChineseReply:
                p = p + ",\n请使用中文回答。"
            user_content.append({"type": "text", "text": p})

        if images is not None:
            if not hasattr(llama_model.chat_handler, "clip_model_path") or llama_model.chat_handler.clip_model_path is None:
                raise ValueError("Image input detected, but the loaded model is not configured with a mmproj module.")

            frames = images
            if video_input:
                indices = np.linspace(0, len(images) - 1, max_frames, dtype=int)
                frames = [images[i] for i in indices]

            if inference_mode == "one by one":
                tmp_list = []
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": ""}
                }
                user_content.append(image_content)
                messages.append({"role": "user", "content": user_content})
                #print(f"[llama-cpp_vlm] Start processing {len(frames)} images")

                for i, image in enumerate(cqdm(frames)):
                    if mm.processing_interrupted():
                        raise mm.InterruptProcessingException()
                    data = image2base64(np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
                    for item in user_content:
                        if item.get("type") == "image_url":
                            item["image_url"]["url"] = f"data:image/jpeg;base64,{data}"
                            break
                    output = llama_model.llm.create_chat_completion(messages=messages, seed=seed, **_parameters)
                    text = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
                    out2.append(text)
                    if len(frames) > 1:
                        tmp_list.append(f"====== Image {i+1} ======")
                    tmp_list.append(text)

                out1 = "\n\n".join(tmp_list)
            else:
                for image in frames:
                    if len(frames) > 1:
                        data = image2base64(scale_image(image, max_size))
                    else:
                        data = image2base64(np.clip(255.0 * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{data}"}
                    }
                    user_content.append(image_content)

                messages.append({"role": "user", "content": user_content})
                output = llama_model.llm.create_chat_completion(messages=messages, seed=seed, **_parameters)
                out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
                out2 = [out1]
        else:
            messages.append({"role": "user", "content": user_content})
            output = llama_model.llm.create_chat_completion(messages=messages, seed=seed, **_parameters)
            out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
            out2 = [out1]

        if save_states:
            #print(f"[llama-cpp_vlm] Saving state id={uid}...")
            messages.append({"role": "assistant", "content": out1})
            clear_message = self.sanitize_messages(messages)
            llama_model.messages[f"{uid}"] = clear_message
        else:
            if not llama_model.messages.get(f"{uid}"):
                llama_model.sys_prompts.pop(f"{uid}", None)

        if force_offload:
            llama_model.clean()

        del messages
        gc.collect()
        return (out1, out2, uid)


# 合并基础节点映射和当前文件的独有节点
NODE_CLASS_MAPPINGS = {**BASE_NODE_CLASS_MAPPINGS, "llama_run": llama_run}
NODE_DISPLAY_NAME_MAPPINGS = {**BASE_NODE_DISPLAY_NAME_MAPPINGS, "llama_run": "Llama-cpp Run"}