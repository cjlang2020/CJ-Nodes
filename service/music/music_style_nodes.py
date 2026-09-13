# -*- coding: utf-8 -*-
"""Luy-音乐风格标签节点（CJ-Nodes/service/music）

用途: 给 YuE2 生成节点拼 `style` 文本。点选式多选，**显示中英对照、输出纯英文**。

设计要点（勿删）:
1) 多选用"分类 + 槽位下拉"实现：ComfyUI 原生 COMBO 是单选，所以每个类别按真实使用量
   给 1-3 个槽位（乐器 3、情绪 3、流派 2、音色质地 2，其余 1）。真实 style 写法每类标签数
   基本就在这个范围内；槽位数可由词表文件名尾部 ` xN` 覆盖，或在 _SLOTS 里改。
2) **界面控件名（中文）直接取自词表文件名的中文部分**：`3-vocal_type-人声类型.txt` →
   控件名「人声类型」；多槽位自动加序号 → 「乐器1/乐器2/乐器3」。所以改文件名就能改界面标签，
   加文件就多一个中文下拉。`_slot_labels()` 是 INPUT_TYPES 与 build() 的唯一来源，
   保证"界面上叫什么"和"取值时找哪个 key"永远一致。
3) 输出顺序由**类别顺序**决定，不受点击/槽位顺序影响 → 同一组选择永远得到同一串文本，
   这样 A/B 对比（只换人声）才可复现。
4) 中英对照技巧：下拉项写成 `中文 | English`，后端只取 ASCII 段；最后再过一遍 CJK 剥离，
   **保证输出里不会残留中文**（即使词表写错、或用户手工粘贴了中文标签）。
5) 词表驱动：`style_tags/NN-key-中文名.txt`，一行一条，`#` 开头为注释。加文件=加类别（默认 1 槽），
   改文件=改选项，**不用改代码**；改完按 F5 刷新页面即可（`INPUT_TYPES` 在每次 /object_info
   请求时重读 txt，连"重载插件"都不用点）。
6) 输出分了组：`voice`（人声三项）/ `instruments` / `mood` / `backing`（其余），
   方便"只换音色、其余不动"的对照实验（voice 单独接 StringMergeDeal 的一个槽）。
7) 预留前端面板接口：`补充标签` 是多行文本框，将来做标签云面板时把结果写进它即可，后端不用改。
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_TAGS_DIR = os.path.join(_HERE, "style_tags")

SKIP = "（不选）"

# 固定参数名（不能与词表生成的控件名冲突）
RESERVED_LABELS = {"BPM", "补充标签", "分隔符"}

# 每类槽位数（键 = 文件名里的 key；未列出的类别默认 1；文件名尾部 ` xN` 可覆盖）
_SLOTS = {
    "genre": 2,
    "timbre": 2,
    "instruments": 3,
    "mood": 3,
}
_DEFAULT_SLOTS = 1
_MAX_SLOTS = 6

# 输出分组：voice = 人声三要素；backing = 其余所有类别（含用户新增的类别）
_GROUPS = {
    "voice": ("vocal_type", "timbre", "delivery"),
    "instruments": ("instruments",),
    "mood": ("mood",),
}

_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\u3000-\u303f\uff00-\uffef]")
_SPLIT = re.compile(r"\s*(?:\||｜|##)\s*")
_FILE_RE = re.compile(r"^(\d+)-([A-Za-z_]+)-(.*?)(?:\s*x(\d+))?\.txt$", re.IGNORECASE)
_FILE_RE_CN = re.compile(r"^(\d+)-(.*?)(?:\s*x(\d+))?\.txt$", re.IGNORECASE)


def _scan_categories():
    """扫描词表目录 → [(序号, key, 中文类别名, 文件名, 槽位数)]，按序号排序。"""
    if not os.path.isdir(_TAGS_DIR):
        return []
    found = []
    for filename in os.listdir(_TAGS_DIR):
        if not filename.lower().endswith(".txt"):
            continue
        match = _FILE_RE.match(filename)
        if match:
            number, key, cn_name, slot_hint = match.groups()
        else:
            match = _FILE_RE_CN.match(filename)
            if not match:
                continue
            number, cn_name, slot_hint = match.groups()
            key = "cat%s" % number                 # 没写 key 的文件用序号兜底
        slots = int(slot_hint) if slot_hint else _SLOTS.get(key, _DEFAULT_SLOTS)
        found.append((int(number), key, cn_name.strip(), filename, max(1, min(_MAX_SLOTS, slots))))
    found.sort(key=lambda item: item[0])
    return found


def _load_options(filename):
    """读取一个词表文件的所有选项（首项为"不选"）。"""
    options = [SKIP]
    path = os.path.join(_TAGS_DIR, filename)
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line not in options:
                    options.append(line)
    except OSError as exc:
        print("[Luy-风格标签] 读取词表失败 %s: %s" % (filename, exc), flush=True)
    return options


def _extract_english(raw):
    """`中文 | English` → `English`；再剥掉任何残留中文，保证纯英文输出。"""
    text = str(raw or "").strip()
    if not text or text == SKIP:
        return ""
    parts = [part.strip() for part in _SPLIT.split(text) if part.strip()]
    if not parts:
        return ""
    # 取"中文占比最低"的一段作为英文（兼容 中文|English 与 English|中文 两种写法）
    parts.sort(key=lambda part: len(_CJK.findall(part)) / max(1, len(part)))
    best = _CJK.sub(" ", parts[0])
    best = re.sub(r"\s+", " ", best)
    return best.strip(" ,，、;；/|")


def _slots_for(key, categories):
    for _, cat_key, _, _, slots in categories:
        if cat_key == key:
            return slots
    return _DEFAULT_SLOTS


def _slot_labels(categories):
    """生成界面控件名（中文，取自词表文件名的中文部分）+ 对应类别 key。

    单槽位 = 直接用类别名（如「人声类型」）；多槽位加序号（如「乐器1/乐器2/乐器3」）。
    INPUT_TYPES 与 build() 共用本函数，**保证界面名与取值逻辑不会对不上**。
    重名时补类别 key 以区分。
    """
    labels, used = [], set()
    for _, key, cn_name, _, slots in categories:
        for index in range(1, slots + 1):
            label = cn_name if slots == 1 else "%s%d" % (cn_name, index)
            if label in used or label in RESERVED_LABELS:
                label = "%s(%s)" % (label, key)
            used.add(label)
            labels.append((label, key, index, slots))
    return labels


class CJMusicStyleTags:
    @classmethod
    def INPUT_TYPES(cls):
        categories = _scan_categories()
        required = {}
        for label, key, index, slots in _slot_labels(categories):
            entry = next(item for item in categories if item[1] == key)
            cn_name, filename = entry[2], entry[3]
            options = _load_options(filename)
            hint = "%s：可选 %d 个；选项形如「中文 | English」，输出只取英文" % (cn_name, slots)
            tooltip = hint if slots == 1 else "%s（第 %d/%d 个）" % (hint, index, slots)
            required[label] = (options, {"tooltip": tooltip})
        if not required:
            required["未找到词表"] = ([SKIP], {
                "tooltip": "未找到词表：请在 service/music/style_tags/ 下放 形如 "
                           "1-language-语种.txt 的文件（一行一条，支持「中文 | English」）"})
        return {
            "required": required,
            "optional": {
                "BPM": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 400.0, "step": 1.0,
                    "tooltip": "末尾输出的速度标签（0=不输出）。建议接扒谱节点的 tempo，保持与旋律一致；"
                               "若同时接了扒谱的 style_hint（已含 BPM），请保持 0，避免出现两个 BPM",
                }),
                "补充标签": ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "词表里没有的标签，逗号分隔（中英都可，中文会被自动剥离）",
                    "tooltip": "手写补充/覆盖（对应 extra_tags）；将来前端标签云面板也写入这里，后端无需改动",
                }),
                "分隔符": ("STRING", {
                    "default": ", ",
                    "tooltip": "标签分隔符（对应 delimiter）；支持字面量 \\n 换行",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("风格", "人声", "乐器", "情绪", "其他", "补充", "速度")
    FUNCTION = "build"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "音乐风格标签选择器：分类多选，界面中英对照，**输出纯英文**。\n"
        "「风格」直接接 YuE2 生成节点的 style；「人声 / 乐器 / 情绪 / 其他」分类输出便于"
        "「只换人声」这类对照实验；「速度」是单独的「88 BPM」标签。\n"
        "输出顺序按类别固定（语种→流派→人声→乐器→情绪→节奏→年代），同一组选择结果可复现。\n"
        "注意：BPM 填了值会写进「风格」；若同时接了扒谱的 style_hint（已含 BPM），保持 0。\n"
        "「补充标签」单独走「补充」输出，不混进任何类别分组。\n"
        "词表在 service/music/style_tags/*.txt：加文件即加类别，文件名的中文部分就是界面控件名。"
    )

    def build(self, **kwargs):
        bpm = kwargs.get("BPM", 0.0)
        extra_tags = kwargs.get("补充标签", "")
        delimiter = kwargs.get("分隔符", ", ")

        categories = _scan_categories()
        picked = []            # [(category_key, english)]
        pairs = []             # 中文对照，仅用于控制台回显
        seen = set()

        def push(category_key, raw):
            english = _extract_english(raw)
            if not english:
                return
            key = english.lower()
            if key in seen:                     # 跨类别也去重，保留首次出现
                return
            seen.add(key)
            picked.append((category_key, english))
            if english.lower() != str(raw).strip().lower():
                pairs.append("%s→%s" % (str(raw).split("|")[0].strip(), english))

        for label, key, _index, _slots in _slot_labels(categories):
            push(key, kwargs.get(label))

        # 手工/面板补充：允许逗号或换行分隔
        for chunk in re.split(r"[,\n;，、]+", str(extra_tags or "")):
            push("extra", chunk)

        delimiter = str(delimiter).replace("\\n", "\n").replace("\\t", "\t")
        bpm_text = ""
        try:
            bpm_value = float(bpm or 0)
        except (TypeError, ValueError):
            bpm_value = 0.0
        if bpm_value > 0:
            bpm_text = "%g BPM" % bpm_value

        def join(category_keys):
            return delimiter.join(tag for cat, tag in picked if cat in category_keys)

        order = [key for _, key, _, _, _ in categories] + ["extra"]
        style = join(set(order))
        if bpm_text:
            style = ("%s%s%s" % (style, delimiter, bpm_text)) if style else bpm_text

        outputs = {
            "style": style,
            "voice": join(set(_GROUPS["voice"])),
            "instruments": join(set(_GROUPS["instruments"])),
            "mood": join(set(_GROUPS["mood"])),
        }
        grouped = set(_GROUPS["voice"]) | set(_GROUPS["instruments"]) | set(_GROUPS["mood"])
        # 分组输出只取"有类别的"标签；补充标签（手写/面板）只出现在 style 里，语义更纯
        outputs["backing"] = join(set(order) - grouped - {"extra"})
        outputs["extra"] = join({"extra"})

        if pairs:
            print("[Luy-风格标签] 中英对照: %s" % " | ".join(pairs), flush=True)
        print("[Luy-风格标签] style = %s" % (style or "(空)"), flush=True)
        return (outputs["style"], outputs["voice"], outputs["instruments"],
                outputs["mood"], outputs["backing"], outputs["extra"], bpm_text)


NODE_CLASS_MAPPINGS = {
    "CJMusicStyleTags": CJMusicStyleTags,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CJMusicStyleTags": "Luy-音乐风格标签",
}
