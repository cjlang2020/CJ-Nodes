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

# 缓存存储：key=unique_id, value=(output_tuple)
_CACHE = {}


def split_text(text: str, delimiter: str) -> list:
    """按分隔符切分文本（支持字面量 \\n、\\t 写法），去空白、丢空项，并保证数组非空"""
    if not delimiter:
        return [text]
    delimiter = delimiter.replace("\\n", "\n").replace("\\t", "\t")
    parts = [p.strip() for p in text.split(delimiter) if p.strip()]
    return parts or [text]

from base import (
    LLAMA_CPP_STORAGE, any_type, chat_handlers, preset_prompts, preset_tags,
    load_text_presets, tensor_to_numpy, image_to_base64_jpeg, scale_image_tensor, cqdm, draft_model_types, _MTMD,
    output_text, thinking_modes,
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
                "模型": (model_list,{"default": "Qwen3.5\\4B\\Qwen3.5-4B-Q4_K_S.gguf"}),
                "视觉模块": (mmproj_list, {"default": "Qwen3.5\\4B\\mmproj-BF16.gguf"}),
                "对话模板": (chat_handlers, {"default": "Qwen3.5"}),
                "预设提示词": (preset_tags, {"default": preset_tags[1]}),
                "自定义提示词": ("STRING", {"default": "", "multiline": True, "placeholder": 'user_prompt'}),
                "系统角色提示词": ("STRING", {"default": "", "multiline": True, "placeholder": '为空则使用内置默认角色；语言要求统一由“中文回复”决定'}),
                "中文回复": ("BOOLEAN", {"default": False}),
                "使用缓存": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Use cached result from last run. Skips model inference and returns previous output."
                }),
                "分隔符": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "留空则不分割。填写后按此分隔符把“输出”拆成数组（支持字面量\\n、\\t），自动去空白并丢弃空项。"
                }),
                "思考模式": (thinking_modes, {
                    "default": "off",
                    "tooltip": "off: Disable thinking for ANY model (sampler-level <think> budget, works even without handler support)\nauto: Model default behavior"
                }),
                "上下文长度": ("INT", {
                    "default": 12800,
                    "min": 2000, "max": 327680, "step": 128,
                    "tooltip": "Context length limit."
                }),
                "最大生成长度": ("INT", {"default": 4096, "min": 0, "max": 4096, "step": 1}),
                "温度": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0, "step": 0.01}),
                "推理模式": (["one by one", "images", "video"], {
                    "default": "one by one",
                    "tooltip": "one by one: Read one image at a time\nimages:  \tRead all images at once\nvideo:  \tTreat the input images as video"
                }),
                "最大尺寸": ("INT", {
                    "default": 256,
                    "min": 128,
                    "max": 16384,
                    "step": 64,
                    "tooltip": 'Max size of input images in "images" and "video" modes.'
                }),
                "最大帧数": ("INT", {
                    "default": 24,
                    "min": 2,
                    "max": 1024,
                    "step": 1,
                    "tooltip": 'Number of frames to sample evenly from input video.\n(for "video" mode only)'
                }),
                "随机种子": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "step": 1, "tooltip": "Random seed for ensuring execution each run."}),
                "启用推理": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Use LLM inference. If False, outputs the custom_prompt directly without calling the model."
                }),
                "推理后卸载模型": ("BOOLEAN", {"default": True, "tooltip": "Unload model after inference. If True, calls clean_state to release resources."}),
                "TopP": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "TopK": ("INT", {"default": 30, "min": 0, "max": 1000, "step": 1}),
                "重复惩罚": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "频率惩罚": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "最小P": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "典型P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "存在惩罚": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                "显存限制": ("INT", {
                    "default": -1,
                    "min": -1, "max": 1024, "step": 1,
                    "tooltip": "VRAM usage limit in GB (-1 = no limit)"
                }),
                "图片最小token": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
                "图片最大token": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 32}),
                "投机解码": (draft_model_types, {
                    "default": "None",
                    "tooltip": "Speculative decoding draft model.\nngram-map: Fast hash-based ngram matching (recommended)\nNone: No speculative decoding"
                }),
                "N元组大小": ("INT", {
                    "default": 3, "min": 1, "max": 10, "step": 1,
                    "tooltip": "N-gram size for draft model matching."
                }),
                "单步预测token数": ("INT", {
                    "default": 10, "min": 1, "max": 32, "step": 1,
                    "tooltip": "Max number of tokens to predict per draft step."
                }),
                "启用MTP": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Multi-Token Prediction (MTP) acceleration.\nRequires a model with MTP support (e.g., Qwen3 variants)."
                }),
                "Mirostat模式": ("INT", {"default": 0, "min": 0, "max": 2, "step": 1}),
                "Mirostat学习率": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 1.0, "step": 0.01}),
                "Mirostat目标熵": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.01}),
                "打印提示词": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Print the prompt messages to console for debugging."
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
            "optional": {
                "图片": ("IMAGE",),
                "队列控制": (any_type, {"tooltip": "Used to control the execution order of instruct nodes."}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("输出", "输出列表", "状态ID", "系统提示词", "用户提示词", "分隔结果")
    OUTPUT_IS_LIST = (False, True, False, False, False, True)
    FUNCTION = "run"
    CATEGORY = "luy/llama-cpp"

    def run(self, 模型, 视觉模块, 对话模板, 预设提示词, 自定义提示词, 系统角色提示词, 中文回复, 使用缓存, 分隔符, 思考模式,
            上下文长度, 最大生成长度, 温度, 推理模式, 最大尺寸, 最大帧数, 随机种子, 启用推理, 推理后卸载模型,
            TopP, TopK, 重复惩罚, 频率惩罚, 最小P, 典型P, 存在惩罚,
            显存限制, 图片最小token, 图片最大token,
            投机解码, N元组大小, 单步预测token数, 启用MTP,
            Mirostat模式, Mirostat学习率, Mirostat目标熵, 打印提示词,
            unique_id, 图片=None, 队列控制=None):
        uid = unique_id.rpartition('.')[-1]

        if 预设提示词 == "None":
            user_text = 自定义提示词.strip()
        else:
            p = preset_prompts[预设提示词]
            p = p.replace("{}", 自定义提示词.strip())
            p = p.replace("@", "image")
            user_text = p

        if not 启用推理:
            text = 自定义提示词.strip()
            return (text, [text], uid, "", user_text, split_text(text, 分隔符))

        if 使用缓存 and uid in _CACHE:
            print(f"[llama-cpp_vlm] Cache hit for node {uid}, skipping inference.")
            return _CACHE[uid] + (split_text(_CACHE[uid][0], 分隔符),)

        custom_config = {
            "model": 模型,
            "mmproj": 视觉模块,
            "chat_handler": 对话模板,
            "n_ctx": 上下文长度,
            "vram_limit": 显存限制,
            "image_min_tokens": 图片最小token,
            "image_max_tokens": 图片最大token,
            "draft_model_type": 投机解码,
            "draft_ngram_size": N元组大小,
            "draft_num_pred_tokens": 单步预测token数,
            "enable_mtp": 启用MTP
        }

        if not LLAMA_CPP_STORAGE.llm or LLAMA_CPP_STORAGE.current_config != custom_config:
            #print("[llama-cpp_vlm] Loading model...")
            LLAMA_CPP_STORAGE.load_model(custom_config)

        llama_model = LLAMA_CPP_STORAGE

        if not llama_model.llm:
            raise RuntimeError("The model has been unloaded or failed to load!")

        parameters = {
            "max_tokens": 最大生成长度,
            "top_k": TopK,
            "top_p": TopP,
            "min_p": 最小P,
            "typical_p": 典型P,
            "temperature": 温度,
            "repeat_penalty": 重复惩罚,
            "frequency_penalty": 频率惩罚,
            "presence_penalty": 存在惩罚,
            "mirostat_mode": Mirostat模式,
            "mirostat_eta": Mirostat学习率,
            "mirostat_tau": Mirostat目标熵,
            "state_uid": -1
        }

        _parameters = parameters.copy()
        _parameters.pop("state_uid", None)
        if _MTMD:
            _parameters.pop("presence_penalty", None)
        if 思考模式 == "off":
            _parameters["reasoning_budget"] = 0
        messages = []
        video_input = 推理模式 == "video"
        # 判断图片数量
        if 图片 is not None:
            if hasattr(图片, 'shape'):
                image_count = 图片.shape[0]
            else:
                image_count = len(图片)
        else:
            image_count = 0

        # 系统提示词：填写优先，留空用内置默认角色；语言要求始终按“中文回复”追加
        if 系统角色提示词.strip():
            system_prompt_text = 系统角色提示词.strip()
        elif image_count == 0:
            system_prompt_text = "你是一名AI助手，擅长扩写用户的描述内容。"
        elif video_input:
            system_prompt_text = "请将输入的图片序列当做视频而不是静态帧序列, 你是一个视频分析助手，可以帮助用户分析视频内容、理解画面变化和叙事逻辑。"
        else:
            system_prompt_text = "你是一名图片分析专家，擅长将图片的内容详细描述出来！"
        if 中文回复:
            system_prompt_text += "\n请使用中文回答。"
        else:
            system_prompt_text += "\nPlease answer in English."
        messages.append({"role": "system", "content": system_prompt_text})

        out1 = ""
        out2 = []
        user_content = []
        # 根据 preset_prompt 是否为 None 决定用户提示词内容
        if 预设提示词 == "None":
            # preset_prompt 为 None 时，完全使用 custom_prompt
            user_text = 自定义提示词.strip()
            user_content.append({"type": "text", "text": user_text})
        else:
            # preset_prompt 不为 None 时，获取预设值并替换 {} 为 custom_prompt
            p = preset_prompts[预设提示词]
            # 替换 {} 为 custom_prompt 内容
            p = p.replace("{}", 自定义提示词.strip())
            # 替换 @ 为 image
            p = p.replace("@", "image")
            user_text = p
            user_content.append({"type": "text", "text": p})

        if 图片 is not None:
            if not hasattr(llama_model.chat_handler, "clip_model_path") or llama_model.chat_handler.clip_model_path is None:
                raise ValueError("Image input detected, but the loaded model is not configured with a mmproj module.")

            frames = 图片
            if video_input:
                indices = np.linspace(0, len(图片) - 1, 最大帧数, dtype=int)
                frames = [图片[i] for i in indices]

            if 推理模式 == "one by one":
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": ""}
                }
                user_content.append(image_content)
                messages.append({"role": "user", "content": user_content})

                for i, image in enumerate(cqdm(frames)):
                    if mm.processing_interrupted():
                        raise mm.InterruptProcessingException()
                    data = image_to_base64_jpeg(image)
                    for item in user_content:
                        if item.get("type") == "image_url":
                            item["image_url"]["url"] = f"data:image/jpeg;base64,{data}"
                            break
                    output = llama_model.llm.create_chat_completion(messages=messages, seed=随机种子, **_parameters)
                    text = output_text(output, 思考模式)
                    out2.append(text)
                    if len(frames) > 1:
                        out1 += f"====== Image {i+1} ======\n{text}\n\n"
                    else:
                        out1 = text
                    data = None
            else:
                for image in frames:
                    if len(frames) > 1:
                        img_np = scale_image_tensor(image, 最大尺寸)
                    else:
                        img_np = tensor_to_numpy(image)
                    data = image_to_base64_jpeg(img_np)
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{data}"}
                    }
                    user_content.append(image_content)

                messages.append({"role": "user", "content": user_content})
                output = llama_model.llm.create_chat_completion(messages=messages, seed=随机种子, **_parameters)
                out1 = output_text(output, 思考模式)
                out2 = [out1]

        else:
            messages.append({"role": "user", "content": user_content})
            output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **_parameters)
            out1 = output_text(output, 思考模式)
            out2 = [out1]

        if 打印提示词:
            import copy
            _sanitized = copy.deepcopy(messages)
            for _msg in _sanitized:
                _c = _msg.get("content")
                if isinstance(_c, list):
                    for _item in _c:
                        if isinstance(_item, dict) and _item.get("type") == "image_url" and "image_url" in _item:
                            _item["image_url"]["url"] = "[BASE64_IMAGE_DATA]"
            print("提示词完成结构messages:", _sanitized)
        del messages
        gc.collect()

        # 根据参数决定是否卸载模型（释放显存）
        if 推理后卸载模型:
            #print("[llama-cpp_vlm] Unloading model and releasing VRAM...")
            LLAMA_CPP_STORAGE.clean_state(uid)
            LLAMA_CPP_STORAGE.clean()

        _CACHE[uid] = (out1, out2, uid, system_prompt_text, user_text)
        return _CACHE[uid] + (split_text(out1, 分隔符),)


# 合并基础节点映射和当前文件的独有节点
NODE_CLASS_MAPPINGS = {**BASE_NODE_CLASS_MAPPINGS, "llama_run_simple": llama_run_simple}
NODE_DISPLAY_NAME_MAPPINGS = {**BASE_NODE_DISPLAY_NAME_MAPPINGS, "llama_run_simple": "Llama-cpp Run Simple"}