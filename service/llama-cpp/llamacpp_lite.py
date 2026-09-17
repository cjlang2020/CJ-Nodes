# llamacpp_lite.py - 仅包含 llama_run_lite 类
# 与 llamacpp_image.py 的 llama_run_simple 功能一致，只隐藏不常用参数并固定为默认值：
#   最大生成长度=4096  温度=0.8  最大尺寸=256  最大帧数=24  随机种子=0  启用推理=True  推理后卸载模型=True
#   TopP=0.9  TopK=30  重复惩罚=1.0  频率惩罚=0.0  最小P=0.05  典型P=1.0  存在惩罚=1.0
#   显存限制=-1  图片最小token=0  图片最大token=0  投机解码=None  N元组大小=3  单步预测token数=10  启用MTP=False
#   Mirostat模式=0  Mirostat学习率=0.1  Mirostat目标熵=5.0  打印提示词=False
# 共享代码在 base.py

import os
import sys

# 动态设置路径以支持 base.py 导入
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import gc
import numpy as np

# 缓存存储：key=unique_id, value=(输出, 输出列表, 状态ID, 系统提示词, 用户提示词)
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
    load_text_presets, tensor_to_numpy, image_to_base64_jpeg, scale_image_tensor, cqdm, _MTMD,
    output_text, thinking_modes, chat_handler_mmproj
)

import folder_paths
import comfy.model_management as mm


class llama_run_lite:
    @classmethod
    def INPUT_TYPES(s):
        all_llms = folder_paths.get_filename_list("LLM")
        model_list = [f for f in all_llms if "mmproj" not in f.lower()]
        mmproj_list = ["None"] + [f for f in all_llms if "mmproj" in f.lower()]
        # 加载 aitools 下 T 和 V 目录的所有 txt 文件作为 preset_prompts
        load_text_presets("V")
        load_text_presets("T")
        return {
            "required": {
                "模型": (model_list, {"default": "Qwen3.5\\4B\\Qwen3.5-4B-Q4_K_S.gguf"}),
                "视觉模块": (mmproj_list, {"default": "Qwen3.5\\4B\\mmproj-BF16.gguf"}),
                "对话模板": (chat_handlers, {"default": "Qwen3.5"}),
                "预设提示词": (preset_tags, {"default": preset_tags[1]}),
                "自定义提示词": ("STRING", {"default": "", "multiline": True, "placeholder": 'user_prompt'}),
                "系统角色提示词": ("STRING", {"default": "", "multiline": True, "placeholder": '为空则使用内置默认角色；语言要求统一由“中文回复”决定'}),
                "中文回复": ("BOOLEAN", {"default": False}),
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
                "推理模式": (["one by one", "images", "video"], {
                    "default": "one by one",
                    "tooltip": "one by one: Read one image at a time\nimages:  \tRead all images at once\nvideo:  \tTreat the input images as video"
                }),
                "使用缓存": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Use cached result from last run. Skips model inference and returns previous output."
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

    def run(self, 模型, 视觉模块, 对话模板, 预设提示词, 自定义提示词, 系统角色提示词, 中文回复, 分隔符,
            思考模式, 上下文长度, 推理模式, 使用缓存, unique_id, 图片=None, 队列控制=None):
        uid = unique_id.rpartition('.')[-1]

        if 预设提示词 == "None":
            user_text = 自定义提示词.strip()
        else:
            p = preset_prompts[预设提示词]
            p = p.replace("{}", 自定义提示词.strip())
            p = p.replace("@", "image")
            user_text = p

        if 使用缓存 and uid in _CACHE:
            print(f"[llama-cpp_lite] Cache hit for node {uid}, skipping inference.")
            return _CACHE[uid] + (split_text(_CACHE[uid][0], 分隔符),)

        custom_config = {
            "model": 模型,
            "mmproj": 视觉模块,
            "chat_handler": 对话模板,
            "n_ctx": 上下文长度,
            "vram_limit": -1,
            "image_min_tokens": 0,
            "image_max_tokens": 0,
            "draft_model_type": "None",
            "draft_ngram_size": 3,
            "draft_num_pred_tokens": 10,
            "enable_mtp": False
        }

        if not LLAMA_CPP_STORAGE.llm or LLAMA_CPP_STORAGE.current_config != custom_config:
            LLAMA_CPP_STORAGE.load_model(custom_config)

        llama_model = LLAMA_CPP_STORAGE

        if not llama_model.llm:
            raise RuntimeError("The model has been unloaded or failed to load!")

        parameters = {
            "max_tokens": 4096,
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
        if 思考模式 == "off":
            parameters["reasoning_budget"] = 0

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
            if not chat_handler_mmproj(llama_model.chat_handler):
                raise ValueError("Image input detected, but the loaded model is not configured with a mmproj module.")

            frames = 图片
            if video_input:
                indices = np.linspace(0, len(图片) - 1, 24, dtype=int)
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
                    output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **parameters)
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
                        img_np = scale_image_tensor(image, 256)
                    else:
                        img_np = tensor_to_numpy(image)
                    data = image_to_base64_jpeg(img_np)
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{data}"}
                    }
                    user_content.append(image_content)

                messages.append({"role": "user", "content": user_content})
                output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **parameters)
                out1 = output_text(output, 思考模式)
                out2 = [out1]

        else:
            messages.append({"role": "user", "content": user_content})
            output = llama_model.llm.create_chat_completion(messages=messages, seed=0, **parameters)
            out1 = output_text(output, 思考模式)
            out2 = [out1]

        del messages
        gc.collect()

        LLAMA_CPP_STORAGE.clean_state(uid)
        LLAMA_CPP_STORAGE.clean()

        _CACHE[uid] = (out1, out2, uid, system_prompt_text, user_text)
        return _CACHE[uid] + (split_text(out1, 分隔符),)


NODE_CLASS_MAPPINGS = {"llama_run_lite": llama_run_lite}
NODE_DISPLAY_NAME_MAPPINGS = {"llama_run_lite": "Llama-cpp Run Lite"}
