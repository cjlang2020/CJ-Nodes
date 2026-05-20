# nodes.py - 分离式架构节点
# 仅包含 llama_cpp_model_loader, llama_cpp_instruct_adv, llama_cpp_parameters
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
    load_text_presets, tensor_to_numpy, image_to_base64_jpeg, scale_image_tensor, cqdm, _MTMD, draft_model_types,
    BASE_NODE_CLASS_MAPPINGS, BASE_NODE_DISPLAY_NAME_MAPPINGS
)

import folder_paths
import comfy.model_management as mm


class llama_cpp_model_loader:
    @classmethod
    def INPUT_TYPES(s):
        all_llms = folder_paths.get_filename_list("LLM")
        model_list = [f for f in all_llms if "mmproj" not in f.lower()]
        mmproj_list = ["None"]+[f for f in all_llms if "mmproj" in f.lower()]

        return {"required": {
            "model": (model_list,),
            "mmproj": (mmproj_list, {"default": "None"}),
            "chat_handler": (chat_handlers, {"default": "None"}),
            "n_ctx": ("INT", {
                "default": 8192,
                "min": 1024, "max": 327680, "step": 128,
                "tooltip": "Context length limit."
            }),
            "vram_limit": ("INT", {
                "default": -1,
                "min": -1, "max": 1024, "step": 1,
                "tooltip": "VRAM usage limit in GB (-1 = no limit)\nReference range; actual usage may slightly exceed."
            }),
            "image_min_tokens": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
            "image_max_tokens": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
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
            }
        }

    RETURN_TYPES = ("LLAMACPPMODEL",)
    RETURN_NAMES = ("llama_model",)
    FUNCTION = "loadmodel"
    CATEGORY = "llama-cpp-vlm"

    def loadmodel(self, model: str, mmproj: str, chat_handler: str, n_ctx: int, vram_limit: int,
                  image_min_tokens: int, image_max_tokens: int,
                  draft_model_type: str, draft_ngram_size: int, draft_num_pred_tokens: int):
        custom_config = {
            "model": model,
            "mmproj": mmproj,
            "chat_handler": chat_handler,
            "n_ctx": n_ctx,
            "vram_limit": vram_limit,
            "image_min_tokens": image_min_tokens,
            "image_max_tokens": image_max_tokens,
            "draft_model_type": draft_model_type,
            "draft_ngram_size": draft_ngram_size,
            "draft_num_pred_tokens": draft_num_pred_tokens
        }
        if not LLAMA_CPP_STORAGE.llm or LLAMA_CPP_STORAGE.current_config != custom_config:
            #print("[llama-cpp_vlm] Loading model...")
            LLAMA_CPP_STORAGE.load_model(custom_config)
        return (custom_config,)


class llama_cpp_instruct_adv:
    @classmethod
    def INPUT_TYPES(s):
        # 加载 aitools 下 T 和 V 目录的所有 txt 文件作为 preset_prompts
        load_text_presets("V")
        load_text_presets("T")
        return {
            "required": {
                "llama_model": ("LLAMACPPMODEL",),
                "preset_prompt": (preset_tags, {"default": preset_tags[1]}),
                "custom_prompt": ("STRING", {"default": "", "multiline": True, "placeholder": 'user_prompt\n\nFor preset hints marked with an "*", this will be used to fill the placeholder (e.g., Object names in BBox detection)\nOtherwise, this will override the preset prompts.'}),
                "system_prompt": ("STRING", {"multiline": True, "default": ""}),
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
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "parameters": ("LLAMACPPARAMS",),
                "images": ("IMAGE",),
                "queue_handler": (any_type, {"tooltip": "Used to control the execution order of instruct nodes."}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("output", "output_list", "state_uid")
    OUTPUT_IS_LIST = (False, True, False)
    FUNCTION = "process"
    CATEGORY = "llama-cpp-vlm"

    def sanitize_messages(self, messages):
        clean_messages = messages.copy()
        for msg in clean_messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        item["image_url"]["url"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAADElEQVQImWP4//8/AAX+Av5Y8msOAAAAAElFTkSuQmCC"
        return clean_messages

    def process(self, llama_model, preset_prompt, custom_prompt, system_prompt, inference_mode, max_frames, max_size, seed, force_offload, save_states, unique_id, parameters=None, images=None, queue_handler=None):
        if not LLAMA_CPP_STORAGE.llm:
            LLAMA_CPP_STORAGE.load_model(llama_model)

        if parameters is None:
            parameters = {
                "max_tokens": 1024,
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
                "mirostat_tau": 5.0
            }

        if _MTMD:
            parameters.pop("presence_penalty", None)

        _uid = parameters.get("state_uid", None)
        _parameters = parameters.copy()
        _parameters.pop("state_uid", None)
        uid = unique_id.rpartition('.')[-1] if _uid in (None, -1) else _uid

        last_sys_prompt = LLAMA_CPP_STORAGE.sys_prompts.get(f"{uid}", None)
        video_input = inference_mode == "video"
        # 根据是否有图片和视频模式调整系统提示词
        if images is None:
            # 不传图片时，作为个人AI助手
            if system_prompt.strip():
                system_prompts = system_prompt
            else:
                system_prompts = "你是一个个人AI助手，可以帮助用户解答问题、提供建议和信息。"
        else:
            # 有图片时
            if video_input:
                # 视频模式：提示将图片序列当做视频
                if system_prompt.strip():
                    system_prompts = "请将输入的图片序列当做视频而不是静态帧序列, " + system_prompt
                else:
                    system_prompts = "请将输入的图片序列当做视频而不是静态帧序列, 你是一个视频分析助手，可以帮助用户分析视频内容、理解画面变化和叙事逻辑。"
            else:
                # 图片模式：作为图像分析助手
                if system_prompt.strip():
                    system_prompts = system_prompt
                else:
                    system_prompts = "你是一个图像分析助手，可以帮助用户分析图像内容、识别物体、描述场景和细节。"
        if last_sys_prompt != system_prompts:
            messages = []
            LLAMA_CPP_STORAGE.clean_state()
            LLAMA_CPP_STORAGE.sys_prompts[f"{uid}"] = system_prompts
            if system_prompts.strip():
                messages.append({"role": "system", "content": system_prompts})
        else:
            if save_states:
                try:
                    #print(f"[llama-cpp_vlm] Loading state and history id={uid}...")
                    messages = LLAMA_CPP_STORAGE.messages.get(f"{uid}", [])
                except Exception as e:
                    messages = []
            else:
                messages = []
        out1 = ""
        out2 = []
        user_content = []
        # 根据 preset_prompt 是否为 None 决定用户提示词内容
        if preset_prompt == "None":
            # preset_prompt 为 None 时，完全使用 custom_prompt
            user_content.append({"type": "text", "text": custom_prompt.strip()})
        else:
            # preset_prompt 不为 None 时，获取预设值并替换 {} 为 custom_prompt
            p = preset_prompts[preset_prompt]
            # 替换 {} 为 custom_prompt 内容
            p = p.replace("{}", custom_prompt.strip())
            # 替换 @ 为 video 或 image（视频模式）
            p = p.replace("@", "video" if video_input else "image")
            # 替换 # 为 custom_prompt（兼容旧格式）
            p = p.replace("#", custom_prompt.strip())
            user_content.append({"type": "text", "text": p})

        if images is not None:
            if not hasattr(LLAMA_CPP_STORAGE.chat_handler, "clip_model_path") or LLAMA_CPP_STORAGE.chat_handler.clip_model_path is None:
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
                    data = image_to_base64_jpeg(image)
                    for item in user_content:
                        if item.get("type") == "image_url":
                            item["image_url"]["url"] = f"data:image/jpeg;base64,{data}"
                            break
                    output = LLAMA_CPP_STORAGE.llm.create_chat_completion(messages=messages, seed=seed, **_parameters)
                    text = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
                    out2.append(text)
                    if len(frames) > 1:
                        tmp_list.append(f"====== Image {i+1} ======")
                    tmp_list.append(text)
                    data = None

                out1 = "\n\n".join(tmp_list)
            else:
                for image in frames:
                    if len(frames) > 1:
                        img_np = scale_image_tensor(image, max_size)
                    else:
                        img_np = tensor_to_numpy(image)
                    data = image_to_base64_jpeg(img_np)
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{data}"}
                    }
                    user_content.append(image_content)

                messages.append({"role": "user", "content": user_content})
                output = LLAMA_CPP_STORAGE.llm.create_chat_completion(messages=messages, seed=seed, **_parameters)
                out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
                out2 = [out1]
        else:
            messages.append({"role": "user", "content": user_content})
            output = LLAMA_CPP_STORAGE.llm.create_chat_completion(messages=messages, seed=seed, **_parameters)
            out1 = output['choices'][0]['message']['content'].removeprefix(": ").lstrip()
            out2 = [out1]

        if save_states:
            #print(f"[llama-cpp_vlm] Saving state id={uid}...")
            messages.append({"role": "assistant", "content": out1})
            clear_message = self.sanitize_messages(messages)
            LLAMA_CPP_STORAGE.messages[f"{uid}"] = clear_message
        else:
            if not LLAMA_CPP_STORAGE.messages.get(f"{uid}"):
                LLAMA_CPP_STORAGE.sys_prompts.pop(f"{uid}", None)

        if force_offload:
            LLAMA_CPP_STORAGE.clean()
        else:
            if LLAMA_CPP_STORAGE.current_config["chat_handler"] in ["Qwen3.5", "Qwen3.5-Thinking"]:
                LLAMA_CPP_STORAGE.llm.n_tokens = 0
                LLAMA_CPP_STORAGE.llm._ctx.memory_clear(True)
                if LLAMA_CPP_STORAGE.llm.is_hybrid and LLAMA_CPP_STORAGE.llm._hybrid_cache_mgr is not None:
                    LLAMA_CPP_STORAGE.llm._hybrid_cache_mgr.clear()

        del messages
        gc.collect()
        return (out1, out2, uid)


class llama_cpp_parameters:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "max_tokens": ("INT", {"default": 1024, "min": 0, "max": 4096, "step": 1}),
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
                "state_uid": ("INT", {
                    "default": -1, "min": -1, "max": 999999, "step": 1,
                    "tooltip": "Use a specific ID to save the conversation state.\n(-1 = use node's unique_id)"
                }),
            }
        }
    RETURN_TYPES = ("LLAMACPPARAMS",)
    RETURN_NAMES = ("parameters",)
    FUNCTION = "process"
    CATEGORY = "llama-cpp-vlm"
    def process(self, **kwargs):
        return (kwargs,)


# 合并基础节点映射和当前文件的独有节点
NODE_CLASS_MAPPINGS = {
    **BASE_NODE_CLASS_MAPPINGS,
    "llama_cpp_model_loader": llama_cpp_model_loader,
    "llama_cpp_instruct_adv": llama_cpp_instruct_adv,
    "llama_cpp_parameters": llama_cpp_parameters,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **BASE_NODE_DISPLAY_NAME_MAPPINGS,
    "llama_cpp_model_loader": "Llama-cpp Model Loader",
    "llama_cpp_instruct_adv": "Llama-cpp Instruct",
    "llama_cpp_parameters": "Llama-cpp Parameters",
}