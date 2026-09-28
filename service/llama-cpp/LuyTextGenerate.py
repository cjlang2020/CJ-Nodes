# LuyTextGenerate.py
# 用文本编码器(CLIP)做自回归文本生成：对齐 comfy_extras/nodes_textgen.py 的 TextGenerate，
# 额外提供 system_prompt/ 目录预置系统提示词下拉 + 自定义系统提示词。
# 本文件只依赖 ComfyUI 本体，不依赖 llama-cpp-python。

import os
import re

# 兼容不同版本的ComfyUI
try:
    from comfy.nodes import BaseNode  # type: ignore
except ImportError:
    class BaseNode:
        pass

NODE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEM_PROMPT_DIR = os.path.join(NODE_DIR, "system_prompt")
DEFAULT_SYSTEM_PROMPT = "默认"
SYSTEM_PROMPT_EXTS = (".txt", ".md")
MEDIA_TOKENS = ("<|image|>", "<|video|>", "<|audio|>", "<image_soft_token>")

SYSTEM_PROMPT_FILES = {}
SYSTEM_PROMPT_CACHE = {}


def scan_system_prompt_files():
    """扫描 system_prompt/ 目录："编号-名称.txt" 按编号排在前，其余按名称排。"""
    files = {}
    if not os.path.isdir(SYSTEM_PROMPT_DIR):
        try:
            os.makedirs(SYSTEM_PROMPT_DIR)
        except OSError:
            return files
    ordered = []
    for filename in os.listdir(SYSTEM_PROMPT_DIR):
        name, ext = os.path.splitext(filename)
        if ext.lower() not in SYSTEM_PROMPT_EXTS or not name:
            continue
        match = re.match(r"^(\d+)-(.*)$", name)
        if match:
            number, name = int(match.group(1)), match.group(2)
        else:
            number = 9999
        if not name or name == DEFAULT_SYSTEM_PROMPT:
            continue
        ordered.append((number, name, filename))
    ordered.sort(key=lambda item: (item[0], item[1]))
    for _, name, filename in ordered:
        files.setdefault(name, filename)
    return files


def read_system_prompt(name):
    filename = SYSTEM_PROMPT_FILES.get(name)
    if not filename:
        return ""
    path = os.path.join(SYSTEM_PROMPT_DIR, filename)
    try:
        stat = os.stat(path)
    except OSError:
        return ""
    key = (path, stat.st_mtime_ns, stat.st_size)
    if key in SYSTEM_PROMPT_CACHE:
        return SYSTEM_PROMPT_CACHE[key]
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return ""
    for encoding in ("utf-8-sig", "gbk"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
    SYSTEM_PROMPT_CACHE.clear()
    SYSTEM_PROMPT_CACHE[key] = text
    return text


def inner_tokenizer(clip):
    """取 SD1Tokenizer 里真正干活的那个 SDTokenizer（音频 token 数要从它身上问）。"""
    tokenizer = getattr(clip, "tokenizer", None)
    name = getattr(tokenizer, "clip_name", None)
    return getattr(tokenizer, name, tokenizer) if name else tokenizer


def audio_token_count(tokenizer, audio):
    counter = getattr(tokenizer, "_audio_token_count", None)
    if counter is None:
        return None
    try:
        samples = int(audio["waveform"].shape[-1])
        sample_rate = audio.get("sample_rate", 16000) or 16000
    except (TypeError, KeyError, AttributeError):
        return None
    if sample_rate != 16000:
        samples = int(samples * 16000 / sample_rate)
    return counter(samples)


def build_media(tokenizer, image, video, audio, fps):
    """镜像 gemma4 tokenizer 的 media 拼法；音频占位算不出来时返回 None。"""
    media = ""
    if video is not None:
        count = len(range(0, video.shape[0], max(1, round(fps)))) or 1
        media += " ".join("%02d:%02d <|image><|video|><image|>" % (i // 60, i % 60) for i in range(count)) + "\n\n"
    elif image is not None:
        media += "<|image><|image|><image|>\n\n" * image.shape[0]
    if audio is not None:
        count = audio_token_count(tokenizer, audio)
        if count is None:
            return None
        media += "<|audio>" + "<|audio|>" * count + "<audio|>\n"
    return media


def build_chat_text(clip, system, prompt, image, video, audio, thinking, fps):
    """按编码器自带模板手拼对话文本；不认识的编码器返回 None（交给通用兜底）。"""
    tokenizer = getattr(clip, "tokenizer", None)
    clip_name = str(getattr(tokenizer, "clip_name", "") or "")

    if "gemma4" in clip_name:
        media = build_media(inner_tokenizer(clip), image, video, audio, fps)
        if media is None:
            return None
        think_prefix = "<|think|>\n" if thinking else ""
        model_open = "" if thinking else "<|channel>final\n"
        return ("<|turn>system\n" + think_prefix + system + "<turn|>\n"
                "<|turn>user\n" + media + prompt + "<turn|>\n"
                "<|turn>model\n" + model_open)

    if "gemma3" in clip_name:
        media = "\n<image_soft_token>\n" if image is not None else ""
        return ("<start_of_turn>system\n" + system + "<end_of_turn>\n"
                "<start_of_turn>user\n" + media + prompt + "<end_of_turn>\n"
                "<start_of_turn>model\n")

    return None


class LuyTextGenerate(BaseNode):
    DESCRIPTION = ("用带 LLM 头的文本编码器(LTXV/gemma3/gemma4 等)生成文本，可用于提示词扩写/图片反推。\n"
                   "系统提示词预置在 service/llama-cpp/system_prompt/ 目录，加 txt 即出现在下拉里。")

    @classmethod
    def INPUT_TYPES(cls):
        global SYSTEM_PROMPT_FILES
        SYSTEM_PROMPT_FILES = scan_system_prompt_files()
        presets = [DEFAULT_SYSTEM_PROMPT] + list(SYSTEM_PROMPT_FILES.keys())
        return {
            "required": {
                "clip": ("CLIP", {"tooltip": "需支持文本生成的编码器(带 LLM 头)，例如 LTX-2 的 gemma3/gemma4。"}),
                "提示词": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
                "系统提示词": (presets, {
                    "default": DEFAULT_SYSTEM_PROMPT,
                    "tooltip": "选“默认”=用编码器自带的对话模板与系统提示词(等价核心 TextGenerate)；\n"
                               "选文件=用该 txt 作为 system 提示词(自动套用编码器的对话模板)；\n"
                               "文件里含 {prompt} 时整份文件当完整模板，需自行保留媒体占位符。"
                }),
                "自定义系统提示词": ("STRING", {"multiline": True, "default": "", "tooltip": "非空时覆盖上面的下拉选择。"}),
                "最大生成长度": ("INT", {
                    "default": 512, "min": 1, "max": 32768, "step": 1,
                    "tooltip": "只算新生成的 token，不含输入的提示词。"
                }),
                "采样模式": (["on", "off"], {
                    "default": "on",
                    "tooltip": "off = 贪心解码(argmax)，下面的采样参数全部不生效。"
                }),
                "温度": ("FLOAT", {"default": 0.7, "min": 0.01, "max": 2.0, "step": 0.01}),
                "top_k": ("INT", {"default": 64, "min": 0, "max": 1000, "step": 1}),
                "top_p": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01}),
                "min_p": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "重复惩罚": ("FLOAT", {"default": 1.05, "min": 0.0, "max": 5.0, "step": 0.01}),
                "存在惩罚": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 5.0, "step": 0.01}),
                "随机种子": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "参考图。批次(B>1)即多图参考：gemma4 每张图一组 soft token，gemma3 拼成一段。"
                }),
                "video": ("IMAGE", {
                    "tooltip": "视频帧批次，按“视频帧率”子采样(gemma4 到 1FPS)。"
                }),
                "audio": ("AUDIO", {}),
                "视频帧率": ("INT", {
                    "default": 24, "min": 1, "max": 240, "step": 1,
                    "tooltip": "仅 video 输入时需要，用于计算子采样帧数。"
                }),
                "thinking": ("BOOLEAN", {"default": False, "tooltip": "模型支持时开启思考模式。"}),
                "mtp": (["auto", "off", "2", "3", "4", "5"], {
                    "default": "auto",
                    "tooltip": "投机解码(多 token 预测头)草稿深度。\n"
                               "只有 checkpoint 带 MTP 权重(如 qwen35)才生效；auto 自适应，2-5 固定深度。"
                }),
                "去思考块": ("BOOLEAN", {"default": True, "tooltip": "去掉输出里的 <think>...</think> 块。"}),
                "空则回退原提示词": ("BOOLEAN", {"default": True, "tooltip": "生成结果为空(只出思考块/直接结束)时返回原提示词。"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("生成文本", "实际提示词")
    FUNCTION = "generate"
    CATEGORY = "luy/AI"

    @staticmethod
    def _compose(clip, system, prompt, image, video, audio, thinking, fps):
        if "{prompt}" in system or "{text}" in system:
            text = system.replace("{prompt}", prompt).replace("{text}", prompt)
            if (image is not None or video is not None or audio is not None) and not any(t in text for t in MEDIA_TOKENS):
                print("⏭️ LuyTextGenerate: 自定义模板不含 <|image|>/<|video|>/<|audio|>/<image_soft_token> 占位符，参考图/视频/音频会被忽略。")
            return text, True
        text = build_chat_text(clip, system, prompt, image, video, audio, thinking, fps)
        if text is not None:
            return text, True
        if video is not None or audio is not None:
            print("⏭️ LuyTextGenerate: 当前编码器不支持自定义模板下的视频/音频占位，已改为把系统提示词并入用户提示词。")
        return system + "\n\n" + prompt, False

    def generate(self, clip, 提示词, 系统提示词, 自定义系统提示词, 最大生成长度, 采样模式,
                 温度, top_k, top_p, min_p, 重复惩罚, 存在惩罚, 随机种子,
                 image=None, video=None, audio=None, 视频帧率=24, thinking=False, mtp="auto",
                 去思考块=True, 空则回退原提示词=True):
        model = getattr(clip, "cond_stage_model", None)
        if model is None or not hasattr(model, "generate"):
            raise RuntimeError("clip 输入不是支持文本生成的编码器；请接 LTXV(gemma3/gemma4) 这类带 LLM 头的文本编码器。")

        system = 自定义系统提示词.strip() or read_system_prompt(系统提示词).strip()
        if system:
            text, skip_template = self._compose(clip, system, 提示词, image, video, audio, thinking, 视频帧率)
        else:
            text, skip_template = 提示词, False

        kwargs = {"image": image, "skip_template": skip_template, "min_length": 1, "thinking": thinking}
        if video is not None:
            kwargs["video"] = video
            kwargs["fps"] = 视频帧率
        if audio is not None:
            kwargs["audio"] = audio
        tokens = clip.tokenize(text, **kwargs)

        generated_ids = clip.generate(
            tokens,
            do_sample=采样模式 == "on",
            max_length=最大生成长度,
            temperature=温度,
            top_k=top_k,
            top_p=top_p,
            min_p=min_p,
            repetition_penalty=重复惩罚,
            presence_penalty=存在惩罚,
            seed=随机种子,
            mtp=False if mtp == "off" else (True if mtp == "auto" else int(mtp)),
        )

        out = clip.decode(generated_ids)
        if 去思考块:
            out = re.sub(r"<think>.*?(?:</think>|$)", "", out, flags=re.DOTALL)
        out = out.strip()
        if not out and 空则回退原提示词:
            out = 提示词

        return (out, text)
