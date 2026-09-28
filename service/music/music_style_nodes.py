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
import json
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


# ═════════════════ 风格标签替换（扒谱 style → 逐标签替换） ═════════════════
#
# 把 `C major, 96 BPM, slow, 4/4, harmony built on C, Am, F, G, verse-chorus form,
# sections: intro → verse×2 → chorus×2 → outro` 这类逗号串拆成"一个标签一行"，
# 前端面板给每行「类别下拉 + 取值下拉 + 常用点选 + 手输」，改完再拼回逗号串。
#
# 三条硬约束（勿改）：
# 1) **行值原文照抄**：row["value"] 初始 == 原标签文本，只有用户主动改才变 → 没改的标签
#    往返后与原文逐字相同（分类/归一化绝不"顺手改用户的风格"）。
# 2) 面板状态存在隐藏文本框 `替换状态`（JSON: {source, rows}）。后端**只在 source 与本次
#    输入完全一致时**才采用它 → 上游风格一变就退回原样透传，绝不用错位的旧行表。
# 3) 解析/分类/候选值全在本文件（词表驱动，与 CJMusicStyleTags 共用 style_tags/），
#    前端只是渲染器：面板没加载时本节点仍是一条可用的透传线。

_FREE_KEY = "other"
_FREE_LABEL = "其他 / 自定义"

# 结构型类别：扒谱 style_hint 的组成部分，取值集固定（不在词表里）
_STRUCT_CATEGORIES = (
    ("key", "调性"),
    ("bpm", "速度BPM"),
    ("tempo_feel", "速度感觉"),
    ("meter", "拍号"),
    ("harmony", "和声走向"),
    ("form", "曲式"),
    ("structure", "段落结构"),
)

_KEYS = ("C major", "G major", "D major", "A major", "E major", "B major", "F# major", "C# major",
         "F major", "Bb major", "Eb major", "Ab major", "Db major", "Gb major",
         "A minor", "E minor", "B minor", "F# minor", "C# minor", "G# minor", "D# minor", "A# minor",
         "D minor", "G minor", "C minor", "F minor", "Bb minor", "Eb minor")

_TEMPO_FEELS = (("very slow", "很慢"), ("slow", "慢"), ("medium tempo", "中速"),
                ("mid-tempo", "中速律动"), ("upbeat", "稍快"), ("fast", "快"),
                ("driving", "推进感"), ("laid-back", "慵懒"), ("half-time", "半速"),
                ("double-time", "双倍速"), ("rubato", "自由速度"), ("steady", "稳定律动"))

_METERS = ("4/4", "3/4", "2/4", "6/8", "12/8", "5/4", "7/8", "9/8")

_FORMS = ("verse-chorus form", "verse-only form", "AABA form", "strophic form",
          "through-composed", "call and response", "theme and variations", "rondo form")

# 常见段落组合（structure 行的点选项；扒谱本身用 `intro → verse×2 → …` 写法）
_SECTION_SETS = ("intro, verse, chorus, bridge, outro",
                 "intro, verse, pre-chorus, chorus, verse, chorus, bridge, chorus, outro",
                 "verse, chorus, verse, chorus, bridge, chorus",
                 "intro, verse, pre-chorus, chorus, outro",
                 "intro → verse×2 → chorus×2 → bridge → chorus×2 → outro")

# 常见和声进行（音级 + 级数标签；按当前调性移调后给 chips）
_HARMONY_PRESETS = (((1, 5, 6, 4), "I–V–vi–IV"), ((6, 4, 1, 5), "vi–IV–I–V"),
                    ((1, 6, 4, 5), "I–vi–IV–V"), ((1, 4, 5, 1), "I–IV–V–I"),
                    ((2, 5, 1, 1), "ii–V–I"), ((1, 6, 2, 5), "I–vi–ii–V"))

_PITCH_INDEX = {"C": 0, "B#": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "Fb": 4,
                "F": 5, "E#": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
                "A#": 10, "Bb": 10, "B": 11, "Cb": 11}
_SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
_MAJOR_SCALE = ((0, ""), (2, "m"), (4, "m"), (5, ""), (7, ""), (9, "m"), (11, "dim"))
_MINOR_SCALE = ((0, "m"), (2, "dim"), (3, ""), (5, "m"), (7, "m"), (8, ""), (10, ""))
_MINOR_MODES = ("minor", "min", "aeolian", "dorian", "phrygian", "locrian", "小调")

_SEP_RE = re.compile(r"[,，;；、\n]")
_RE_BPM = re.compile(r"^\d+(?:\.\d+)?\s*BPM$", re.IGNORECASE)
_RE_METER = re.compile(r"^\d+\s*/\s*\d+$")
_RE_KEY = re.compile(
    r"^([A-G][#b]?)\s*(major|maj|minor|min|dorian|phrygian|lydian|mixolydian|aeolian|locrian|ionian|大调|小调)$",
    re.IGNORECASE)
_RE_HARMONY = re.compile(
    r"^(harmony\s+built\s+on|harmony|chord\s+progression|chords|和弦构建于|和弦走向|和弦)\s*[:：]?\s*(.*)$",
    re.IGNORECASE)
_RE_SECTIONS = re.compile(r"^(sections?|段落|结构|曲式结构)\s*[:：]\s*(.*)$", re.IGNORECASE)
_RE_CHORD = re.compile(
    r"^(?:N\.?C\.?|"
    r"(?:[A-G][#b]?)(?:maj|min|m|dim|aug|sus|add|no|ø)?\d*(?:(?:sus|add)\d+|b5|#5|b9|#9|11|13)?(?:/[A-G][#b]?)?|"
    r"[b#]?(?:VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)\d*)$")
# 仅用于"sections: 之后继续吸收"，不做独立分类（避免把 EDM 的 drop 当成段落）
_RE_SECTION_NAME = re.compile(
    r"^(?:intro|outro|verse|pre[\s-]?chorus|post[\s-]?chorus|chorus|bridge|solo|instrumental|interlude|"
    r"breakdown|drop|hook|refrain|coda|tag|vamp|riff|middle\s*eight|main\s*riff|"
    r"前奏|主歌|副歌|桥段|间奏|尾奏|尾声|高潮)(?:\s*[×x]?\s*\d+)?$",
    re.IGNORECASE)

_VOCAB_CACHE = {}


def _opt(value, label=None, short=None):
    return {"value": value, "label": label or value, "short": short or value}


_STRUCT_OPTIONS = {
    "key": tuple(_opt(name) for name in _KEYS),
    "bpm": (),
    "tempo_feel": tuple(_opt(en, "%s | %s" % (cn, en), cn) for en, cn in _TEMPO_FEELS),
    "meter": tuple(_opt(name) for name in _METERS),
    "harmony": (),
    "form": tuple(_opt(name) for name in _FORMS),
    "structure": (),
}

_TEMPO_FEEL_KEYS = frozenset(en for en, _ in _TEMPO_FEELS)
_FORM_KEYS = frozenset(name.lower() for name in _FORMS) | frozenset(
    ("verse-chorus", "verse chorus form", "aaba", "32-bar aaba", "strophic", "through composed",
     "through-composed form", "rondo", "verse only", "call-and-response"))


def _unique(values):
    out, seen = [], set()
    for value in values:
        text = str(value or "").strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _token_key(text):
    """分类/匹配用的归一化键：小写、& → and、去掉所有标点与空白。"""
    text = str(text or "").lower().replace("&", "and")
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)


def _normalize_delimiter(text):
    delimiter = str(text if text is not None else "")
    delimiter = delimiter.replace("\\n", "\n").replace("\\t", "\t")
    return delimiter or ", "


def _vocab_stamp():
    if not os.path.isdir(_TAGS_DIR):
        return ()
    stamp = []
    for name in sorted(os.listdir(_TAGS_DIR)):
        if not name.lower().endswith(".txt"):
            continue
        try:
            stat = os.stat(os.path.join(_TAGS_DIR, name))
        except OSError:
            continue
        stamp.append((name, stat.st_mtime_ns, stat.st_size))
    return tuple(stamp)


def _vocab_data():
    """→ (词表类别, 归一化索引)；按 txt 的 mtime/大小缓存，改词表后刷新页面即生效。"""
    stamp = _vocab_stamp()
    cached = _VOCAB_CACHE.get("stamp")
    if cached == stamp and "categories" in _VOCAB_CACHE:
        return _VOCAB_CACHE["categories"], _VOCAB_CACHE["index"]
    categories, index = [], {}
    for _, key, cn_name, filename, _slots in _scan_categories():
        options = []
        for raw in _load_options(filename)[1:]:          # 首项是"（不选）"
            value = _extract_english(raw) or raw
            short = _SPLIT.split(raw)[0].strip() or value
            options.append(_opt(value, raw, short))
            index.setdefault(_token_key(value), (key, value))
            index.setdefault(_token_key(short), (key, value))
        categories.append({"key": key, "label": cn_name, "options": options})
    _VOCAB_CACHE.update({"stamp": stamp, "categories": categories, "index": index})
    return categories, index


def _catalog_options():
    """类别 key → 词表候选项（给 _suggest 用）。"""
    categories, _index = _vocab_data()
    return {item["key"]: item["options"] for item in categories}


def _parse_key(text):
    match = _RE_KEY.match(str(text or "").strip())
    if not match:
        return None
    root = match.group(1)
    root = root[:1].upper() + root[1:]
    pitch = _PITCH_INDEX.get(root)
    if pitch is None:
        return None
    return {"pc": pitch, "minor": match.group(2).lower() in _MINOR_MODES,
            "flats": "b" in root[1:], "text": str(text).strip()}


def _key_name(pitch, minor, flats):
    names = _FLAT_NAMES if flats else _SHARP_NAMES
    return "%s %s" % (names[pitch % 12], "minor" if minor else "major")


def _classify_tag(text):
    """标签 → 类别 key（结构化正则优先，再词表，最后 other）。"""
    tag = str(text or "").strip()
    if not tag:
        return _FREE_KEY
    low = tag.lower()
    if _RE_BPM.match(tag) or low == "unknown tempo":
        return "bpm"
    if _RE_METER.match(tag):
        return "meter"
    if _RE_KEY.match(tag) or low == "unknown key":
        return "key"
    if low in _TEMPO_FEEL_KEYS:
        return "tempo_feel"
    if _RE_HARMONY.match(tag):
        return "harmony"
    if _RE_SECTIONS.match(tag):
        return "structure"
    if low in _FORM_KEYS:
        return "form"
    hit = _vocab_data()[1].get(_token_key(tag))
    if hit:
        return hit[0]
    return _FREE_KEY


def _split_segments(text):
    return [part.strip() for part in _SEP_RE.split(str(text or "")) if part.strip()]


def _merge_segments(segments):
    """把"逗号在标签内部"的复合标签并回一条：`harmony built on C, Am, F, G`、`sections: …`。"""
    merged, index = [], 0
    while index < len(segments):
        segment = segments[index]
        match = _RE_HARMONY.match(segment)
        if match:
            parts = [match.group(2)] if match.group(2) else []
            nxt = index + 1
            while nxt < len(segments) and _RE_CHORD.match(segments[nxt]):
                parts.append(segments[nxt])
                nxt += 1
            merged.append(match.group(1) if not parts else "%s %s" % (match.group(1), ", ".join(parts)))
            index = nxt
            continue
        match = _RE_SECTIONS.match(segment)
        if match:
            parts = [match.group(2)] if match.group(2) else []
            nxt = index + 1
            while nxt < len(segments) and (_RE_SECTION_NAME.match(segments[nxt])
                                           or _classify_tag(segments[nxt]) == _FREE_KEY):
                parts.append(segments[nxt])
                nxt += 1
            merged.append("%s: %s" % (match.group(1), ", ".join(parts)) if parts else match.group(1))
            index = nxt
            continue
        merged.append(segment)
        index += 1
    return merged


def _key_suggestions(key_info):
    if not key_info:
        return list(_KEYS[:7])
    pitch, minor, flats = key_info["pc"], key_info["minor"], key_info["flats"]
    return _unique([key_info["text"],
                    _key_name(pitch, minor, flats),
                    _key_name(pitch + (3 if minor else 9), not minor, flats),
                    _key_name(pitch, not minor, flats),
                    _key_name(pitch + 1, minor, flats),
                    _key_name(pitch - 1, minor, flats),
                    _key_name(pitch + 2, minor, flats),
                    _key_name(pitch - 2, minor, flats)])


def _harmony_suggestions(key_info):
    pitch = key_info["pc"] if key_info else 0
    minor = key_info["minor"] if key_info else False
    names = _FLAT_NAMES if (key_info and key_info["flats"]) else _SHARP_NAMES
    scale = _MINOR_SCALE if minor else _MAJOR_SCALE
    out = []
    for degrees, _label in _HARMONY_PRESETS:
        chords = [names[(pitch + scale[degree - 1][0]) % 12] + scale[degree - 1][1] for degree in degrees]
        out.append("harmony built on " + ", ".join(chords))
    return out


def _suggest(category, value, key_info):
    if category == "bpm":
        return _unique([value, "60", "72", "80", "90", "100", "120", "128"])
    if category == "tempo_feel":
        return [en for en, _ in _TEMPO_FEELS]
    if category == "meter":
        return list(_METERS)
    if category == "key":
        return _key_suggestions(key_info or _parse_key(value))
    if category == "harmony":
        return _harmony_suggestions(key_info)
    if category == "form":
        return list(_FORMS)
    if category == "structure":
        return ["sections: " + item for item in _SECTION_SETS]
    catalog = _catalog_options().get(category)
    if catalog:
        return [item["value"] for item in catalog[:8]]
    return []


def parse_style(source):
    """style 串 → 行表 [{text, category, value, suggest}]；value 一律照抄原文。"""
    segments = _merge_segments(_split_segments(source))
    key_info = None
    for segment in segments:                              # 先找调性：和声 chips 要按它移调
        if _classify_tag(segment) == "key":
            key_info = _parse_key(segment)
            if key_info:
                break
    rows = []
    for segment in segments:
        category = _classify_tag(segment)
        rows.append({"text": segment, "category": category, "value": segment,
                     "suggest": _suggest(category, segment, key_info)})
    return rows


def style_categories():
    """面板用的类别表（结构型 + 词表型 + 其他）。"""
    categories = []
    for key, label in _STRUCT_CATEGORIES:
        options = [dict(item) for item in _STRUCT_OPTIONS.get(key, ())]
        chips = [item["value"] for item in options[:8]] or _suggest(key, "", None)
        categories.append({"key": key, "label": label, "kind": "struct",
                           "options": options, "chips": chips[:8]})
    vocab, _index = _vocab_data()
    for item in vocab:
        categories.append({"key": item["key"], "label": item["label"], "kind": "vocab",
                           "options": item["options"],
                           "chips": [opt["value"] for opt in item["options"][:8]]})
    categories.append({"key": _FREE_KEY, "label": _FREE_LABEL, "kind": "free",
                       "options": [], "chips": []})
    return categories


def style_parse(source, delimiter=", "):
    delimiter = _normalize_delimiter(delimiter)
    rows = parse_style(source)
    return {"source": "" if source is None else str(source), "delimiter": delimiter,
            "rows": rows, "result": delimiter.join(row["value"] for row in rows)}


def _read_state(raw):
    """解析隐藏 widget 里存的面板状态；任何不对就返回 None（→ 原样透传）。"""
    if not raw:
        return None
    try:
        state = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(state, dict) or not isinstance(state.get("source"), str):
        return None
    entries = state.get("rows")
    if not isinstance(entries, list):
        return None
    tags = []
    for entry in entries:
        text = entry.get("value") if isinstance(entry, dict) else entry
        text = str(text or "").strip()
        if text:
            tags.append(text)
    return {"source": state["source"], "tags": tags}


class CJMusicStyleReplacer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "风格": ("STRING", {
                    "default": "", "multiline": False,
                    "tooltip": "接扒谱「风格底稿」（或任何逗号/分号分隔的风格串）。面板会把它拆成"
                               "一行一个标签，逐行替换后按「分隔符」拼回",
                }),
            },
            "optional": {
                "分隔符": ("STRING", {
                    "default": ", ",
                    "tooltip": "输出拼回用的分隔符（输入始终按 逗号/分号/顿号/换行 拆）；"
                               "支持字面量 \\n 换行。留空按「, 」处理",
                }),
                "替换状态": ("STRING", {
                    "default": "", "multiline": True,
                    "tooltip": "前端面板维护的行表 JSON（{source, rows}），**不用手改**；"
                               "为空 / 损坏 / 与本次输入不一致时本节点原样输出输入",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("风格",)
    FUNCTION = "replace"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "风格标签替换：把扒谱「风格底稿」这类逗号串拆成一行一个标签，在前端面板里"
        "逐行换「类别 + 取值」（下拉 / 常用点选 / 手输），再拼回逗号串。\n"
        "面板不进工作流逻辑：行表存在隐藏框「替换状态」里，后端只在它与本次输入一致时才采用，"
        "否则原样透传 → 面板没加载、状态过期都不会改坏风格。\n"
        "调性 / 速度 / 拍号 / 和声走向 / 曲式 / 段落 六类由正则识别；流派 / 人声 / 乐器等"
        "按 service/music/style_tags/ 的词表识别，改词表即改候选项。"
    )

    @classmethod
    def vocabulary_payload(cls):
        return {"categories": style_categories(), "delimiter": ", ", "chip_limit": 8}

    @classmethod
    def parse_payload(cls, source, delimiter=", "):
        return style_parse(source, delimiter)

    def replace(self, 风格, 分隔符=", ", 替换状态=""):
        source = str(风格 or "")
        delimiter = _normalize_delimiter(分隔符)
        rows = parse_style(source)
        state = _read_state(替换状态)
        used_state = bool(state) and state["source"] == source
        if used_state:
            result = delimiter.join(state["tags"])
        else:
            result = source
        if state and not used_state:
            print("[Luy-风格标签替换] 状态与本次输入不一致（上游风格已变），原样输出", flush=True)
        else:
            print("[Luy-风格标签替换] %d 个标签，%s → %s" % (
                len(rows), "使用面板替换" if used_state else "原样透传", result or "(空)"), flush=True)
        return {
            "ui": {
                "ms_source": [source],
                "ms_result": [result],
                "ms_rows": rows,
                "ms_used_state": [used_state],
                "ms_delimiter": [delimiter],
            },
            "result": (result,),
        }


# ═════════════════ 预制风格（预设下拉 + 前端逐类别微调） ═════════════════
#
# 「先选一个现成风格，再单独改某一类」：`预制风格` 是**普通 COMBO widget**（可见、可存、
# 没前端 JS 也能选，输出预设原样风格），下方 DOM 面板按类别给出下拉，可逐项微调。
#
# 三条硬约束（与 CJMusicStyleReplacer 同款，勿改）：
# 1) **预设原文可复现**：预设 style 串逐段 `_extract_english` 归一化（去中文/去重）后按段顺序
#    输出；没动面板时输出 == 预设文件内容（归一化后），不掺任何猜测。
# 2) 面板微调存隐藏 widget `调整状态`（JSON: {preset, rows}）；后端**只在 preset 与本次
#    `预制风格` 完全一致时才采用**，过期/坏 JSON 一律退回预设原样。
# 3) 解析/分类/候选项全在 Python（复用词表与 `_classify_tag`），前端只是渲染器；
#    面板/路由挂了本节点仍可用（预设下拉是原生 widget）。
#
# 预设词表：`style_presets/*.json`（{label, note, bpm, style}，按文件名排序）。取值请用
# `style_tags/` 里的英文原文，这样面板下拉能直接命中选项（未命中的会显示为「预设: xxx」）。
# `bpm` = 推荐速度（0/缺省 = 不写速度）；**由前端面板在选中预设时写进原生 `BPM` widget**
# （所以后端仍只看 BPM widget 的值，逻辑不变）——用户想不要速度就把 BPM 改回 0。

_PRESETS_DIR = os.path.join(_HERE, "style_presets")
_VARIANTS_PATH = os.path.join(_PRESETS_DIR, "_variants.json")     # `_` 开头：不是预设，是演绎变体表
PRESET_CUSTOM = "（自定义）"
VARIANT_DEFAULT = "标准"
_PRESET_CACHE = {}
_VARIANT_CACHE = {}

# 演绎轴：变体里这几个类别**整体替换**（这才叫“换个演绎”）；其余类别（音色/年代/乐器…）**追加**，
# 不抹掉预设自身特征。值与风格标签节点同词表（style_tags/），分类走 _classify_tag。
_VARIANT_AXES = ("mood", "rhythm", "tempo_feel", "delivery")

# 输出类别顺序（与 CJMusicStyleTags 同思路：顺序由类别决定，不受点击/变体插入顺序影响）
_CATEGORY_ORDER = ("language", "genre", "vocal_type", "timbre", "delivery", "instruments",
                   "mood", "rhythm", "tempo_feel", "era")


def _preset_stamp():
    if not os.path.isdir(_PRESETS_DIR):
        return ()
    stamp = []
    for name in sorted(os.listdir(_PRESETS_DIR)):
        if not name.lower().endswith(".json") or name.startswith("_"):    # `_variants.json` 不算预设
            continue
        try:
            stat = os.stat(os.path.join(_PRESETS_DIR, name))
        except OSError:
            continue
        stamp.append((name, stat.st_mtime_ns, stat.st_size))
    return tuple(stamp)


def _variant_stamp():
    try:
        stat = os.stat(_VARIANTS_PATH)
    except OSError:
        return ()
    return (stat.st_mtime_ns, stat.st_size)


def _as_float(raw, low=0.0, high=1e9, default=0.0):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, value))


def _variant_list():
    """→ [{'label', 'note', 'bpm_scale', 'tags'}]；按 json 的 mtime/大小缓存。"""
    stamp = _variant_stamp()
    if _VARIANT_CACHE.get("stamp") == stamp and "items" in _VARIANT_CACHE:
        return _VARIANT_CACHE["items"]
    items = []
    try:
        with open(_VARIANTS_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        print("[Luy-预制风格] 读取变体表失败 %s: %s" % (_VARIANTS_PATH, exc), flush=True)
        data = None
    for entry in (data or {}).get("variants", []) if isinstance(data, dict) else []:
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label") or "").strip()
        if not label:
            continue
        tags = [str(tag).strip() for tag in (entry.get("tags") or []) if str(tag).strip()]
        items.append({"label": label, "note": str(entry.get("note") or "").strip(),
                      "bpm_scale": _as_float(entry.get("bpm_scale"), 0.05, 5.0, 1.0),
                      "tags": tags})
    if not items:
        items = [{"label": VARIANT_DEFAULT, "note": "预设原样（未找到 _variants.json）",
                  "bpm_scale": 1.0, "tags": []}]
    _VARIANT_CACHE.update({"stamp": stamp, "items": items})
    return items


def _variant_by_label(label):
    for item in _variant_list():
        if item["label"] == label:
            return item
    return _variant_list()[0]


def _variant_bpm(preset_bpm, variant):
    """变体速度：预设 BPM × bpm_scale（无预设 BPM 时不猜，返 0）。"""
    if not variant or preset_bpm <= 0:
        return 0.0
    return float(int(round(preset_bpm * _as_float(variant.get("bpm_scale"), 0.05, 5.0, 1.0))))


def _apply_variant(base_rows, variant):
    """预设行 + 演绎变体 → 行表。

    - 变体为「标准」/空 → **原样返回**（保证预设 style 逐字可复现）；
    - 演绎轴（mood/rhythm/tempo_feel/delivery）在**它原本的位置整体替换**（不把整个风格重排）；
    - 其余类别（音色/年代/乐器…）**追加**在同类后面（不抹掉预设自身特征）；
    - 变体带来新类别时按类别顺序插到合适位置；最后跨类别去重（保留首次出现，与 _preset_rows 同规则）。
    """
    if not variant or not variant.get("tags"):
        return [dict(row) for row in base_rows]
    replace, append = {}, []
    for raw in variant["tags"]:
        english = _extract_english(raw) or str(raw).strip()
        if not english:
            continue
        category = _classify_tag(english)
        if category in _VARIANT_AXES:
            replace.setdefault(category, []).append(english)
        else:
            append.append((category, english))

    out, replaced = [], set()
    for row in base_rows:
        category = row["category"]
        if category in replace:
            if category in replaced:
                continue                              # 该类已整体换掉，丢掉后续旧值
            replaced.add(category)
            out.extend({"category": category, "value": value} for value in replace[category])
            continue
        out.append(dict(row))

    order = {key: index for index, key in enumerate(_category_order())}
    grouped = {}
    for category, english in append:
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(english)
    for category in list(replace) + list(grouped):            # 变体带的类别若 base 没有 → 也要插
        values = replace.get(category) if category in replace and category not in replaced else None
        if values is not None:
            grouped[category] = list(values)
    fresh = [key for key in grouped if key not in {row["category"] for row in out}]
    fresh.sort(key=lambda key: order.get(key, len(order)))
    for category in fresh:                                     # 新类别：按类别顺序插到合适位置
        position = len(out)
        for index, row in enumerate(out):
            if order.get(row["category"], len(order)) > order.get(category, len(order)):
                position = index
                break
        out[position:position] = [{"category": category, "value": value}
                                  for value in grouped.pop(category)]
    for category, values in grouped.items():                   # 已有类别：追加在同类最后一行之后
        position = 0
        for index, row in enumerate(out):
            if row["category"] == category:
                position = index + 1
        out[position:position] = [{"category": category, "value": value} for value in values]

    rows, seen = [], set()
    for row in out:
        low = row["value"].lower()
        if low in seen:
            continue
        seen.add(low)
        rows.append(row)
    return rows


def _category_order():
    """输出类别顺序（与 CJMusicStyleTags 同思路）：顺序由类别决定，不受变体插入顺序影响。"""
    known = [key for _, key, _, _, _ in _scan_categories()]
    return list(_CATEGORY_ORDER) + [key for key in known if key not in _CATEGORY_ORDER]


def _preset_variants(preset):
    """某个预设下的 10 个演绎（rows 已按变体算好，前端只渲染）：[{label, bpm, rows}]。"""
    preset_bpm = _as_float((preset or {}).get("bpm"), 0.0, 400.0, 0.0)
    base_rows = (preset or {}).get("rows", [])
    return [{"label": item["label"], "bpm": _variant_bpm(preset_bpm, item),
             "rows": _apply_variant(base_rows, item)} for item in _variant_list()]


def _preset_rows(style):
    """预设 style 串 → [{'category', 'value'}]：逐段取英文、跨类别去重、保持段顺序。"""
    rows, seen = [], set()
    for segment in _split_segments(style):
        english = _extract_english(segment)
        if not english:
            continue
        key = english.lower()
        if key in seen:
            continue
        seen.add(key)
        rows.append({"category": _classify_tag(english), "value": english})
    return rows


def _preset_bpm(raw):
    """预设推荐速度：0 = 不写（面板会把它写进原生 BPM widget，后端不参与）。"""
    return _as_float(raw, 0.0, 400.0, 0.0)


def _preset_list():
    """→ [{'label', 'note', 'style', 'rows'}]，按文件名排序；按 json 的 mtime/大小缓存。"""
    stamp = _preset_stamp()
    if _PRESET_CACHE.get("stamp") == stamp and "items" in _PRESET_CACHE:
        return _PRESET_CACHE["items"]
    items = []
    for name, _mtime, _size in stamp:
        path = os.path.join(_PRESETS_DIR, name)
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as exc:
            print("[Luy-预制风格] 读取预设失败 %s: %s" % (name, exc), flush=True)
            continue
        if not isinstance(data, dict):
            print("[Luy-预制风格] 预设格式不对（应为 JSON 对象）: %s" % name, flush=True)
            continue
        style = str(data.get("style") or "").strip()
        if not style:
            print("[Luy-预制风格] 预设缺少 style 字段: %s" % name, flush=True)
            continue
        items.append({"label": str(data.get("label") or os.path.splitext(name)[0]).strip(),
                      "note": str(data.get("note") or "").strip(),
                      "bpm": _preset_bpm(data.get("bpm")),
                      "style": style, "rows": _preset_rows(style)})
    _PRESET_CACHE.update({"stamp": stamp, "items": items})
    return items


def _preset_by_label(label):
    for item in _preset_list():
        if item["label"] == label:
            return item
    return None


def _read_preset_state(raw):
    """解析隐藏 widget `调整状态`；空/坏 JSON/结构不对 → None（→ 退回预设原样）。"""
    if not raw:
        return None
    try:
        state = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(state, dict) or not isinstance(state.get("preset"), str):
        return None
    entries = state.get("rows")
    if not isinstance(entries, list):
        return None
    rows = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        value = str(entry.get("value") or "").strip()
        if not value:
            continue
        rows.append({"category": str(entry.get("category") or _FREE_KEY), "value": value})
    return {"preset": state["preset"], "variant": str(state.get("variant") or ""), "rows": rows}


class CJMusicStylePreset:
    @classmethod
    def INPUT_TYPES(cls):
        labels = [item["label"] for item in _preset_list()]
        variant_labels = [item["label"] for item in _variant_list()]
        return {
            "required": {
                "预制风格": ([PRESET_CUSTOM] + labels, {
                    "tooltip": "选一个现成风格（词表：service/music/style_presets/*.json，加文件即加预设）。"
                               "选完后可在下方面板里对每个类别单独调；不会调就直接用预设原样。"
                               "「（自定义）」= 不用预设，完全按面板 / 「补充标签」拼",
                }),
                "变体": (variant_labels, {
                    "tooltip": "同一种风格下的 10 种演绎（变体表：style_presets/_variants.json）："
                               "标准/快歌/慢歌/悲伤/欢快/浪漫/燃向/梦幻/治愈/暗黑。"
                               "演绎轴（情绪/节奏/速度感/唱法）整体替换，其余类别照旧；BPM 自动按倍率缩放"
                               "（面板会写进 BPM 框，可手改）",
                }),
            },
            "optional": {
                "补充标签": ("STRING", {
                    "default": "",
                    "tooltip": "追加在预设之后（对应 extra_tags），可连上游；逗号分隔，单独走「补充」输出。"
                               "**单行输入**（不加 multiline）→ 原生控件固定高度，不会因节点拉高而变形",
                }),
                "分隔符": ("STRING", {
                    "default": ", ",
                    "tooltip": "标签分隔符（对应 delimiter）；支持字面量 \\n 换行",
                }),
                "BPM": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 400.0, "step": 1.0,
                    "tooltip": "末尾输出的速度标签（0=不输出）。**选预设/变体时面板会写进这里**"
                               "（预设 BPM × 变体倍率，快歌 1.3× / 慢歌 0.72×），可手改；"
                               "与扒谱 style_hint 合用时改回 0，避免出现两个 BPM",
                }),
                "调整状态": ("STRING", {
                    "default": "", "multiline": True,
                    "tooltip": "前端面板维护的逐类别微调 JSON（{preset, rows}），**不用手改**；"
                               "为空 / 损坏 / 与「预制风格」不一致时，本节点输出预设原样",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("风格",)
    FUNCTION = "build"
    CATEGORY = "luy/音乐"
    OUTPUT_NODE = False
    DESCRIPTION = (
        "预制风格标签：先选一个现成风格（预设下拉）与一种演绎（变体下拉：标准/快歌/慢歌/悲伤/欢快/"
        "浪漫/燃向/梦幻/治愈/暗黑），再用前端面板对每个类别（语种/流派/人声/音色/唱法/乐器/情绪/节奏/年代）"
        "单独微调，**只输出一路纯英文 style**（直接接 YuE2 生成节点的风格）。\n"
        "预设来自 service/music/style_presets/*.json（一个 json 一个预设：label/note/bpm/style，加文件即加预设）；"
        "变体表在 style_presets/_variants.json（bpm_scale + tags：演绎轴 情绪/节奏/速度感/唱法 整体替换，"
        "其余类别追加）；面板按 style_tags/ 词表生成下拉。三者改完 F5 即生效。\n"
        "微调存在隐藏框「调整状态」里，后端只在它与本次「预制风格 + 变体」一致时才采用，否则输出预设+变体"
        "原样 → 面板没加载 / 状态过期都不会改坏风格。\n"
        "「补充标签」追加在预设之后；BPM 面板会自动按变体倍率填（可手改，0=不输出）。"
    )

    @classmethod
    def presets_payload(cls):
        """前端面板数据（词表类别 + 预设 + 每个预设的变体行表），改 json 后刷新页面即生效。"""
        return {
            "custom": PRESET_CUSTOM,
            "variant_default": VARIANT_DEFAULT,
            "slot_limit": _MAX_SLOTS,
            "categories": style_categories(),
            "variants": [{"label": item["label"], "note": item["note"],
                          "bpm_scale": item["bpm_scale"], "tags": item["tags"]}
                         for item in _variant_list()],
            "custom_variants": _preset_variants(None),
            "presets": [{"label": item["label"], "note": item["note"], "bpm": item["bpm"],
                          "style": item["style"], "rows": item["rows"],
                          "variants": _preset_variants(item)}
                         for item in _preset_list()],
        }

    def build(self, 预制风格, 变体=VARIANT_DEFAULT, 补充标签="", 分隔符=", ", BPM=0.0, 调整状态=""):
        preset_name = str(预制风格 or "").strip() or PRESET_CUSTOM
        variant_name = str(变体 or "").strip() or VARIANT_DEFAULT
        delimiter = _normalize_delimiter(分隔符)
        preset = None if preset_name == PRESET_CUSTOM else _preset_by_label(preset_name)
        variant = _variant_by_label(variant_name)
        base = _apply_variant(preset["rows"] if preset else [], variant)

        state = _read_preset_state(调整状态)
        use_state = bool(state) and state["preset"] == preset_name \
            and state.get("variant", "") == variant_name and bool(state["rows"])
        rows = state["rows"] if use_state else base
        if state and not use_state:
            print("[Luy-预制风格] 面板调整状态与本次预设/变体不一致（已换或状态过期），用预设+变体原样",
                  flush=True)
        elif preset_name != PRESET_CUSTOM and preset is None:
            print("[Luy-预制风格] 未找到预设「%s」（style_presets/*.json 里没有这个 label）" % preset_name,
                  flush=True)

        picked, seen, pairs = [], set(), []

        def push(category_key, raw):
            english = _extract_english(raw)
            if not english:
                return
            key = english.lower()
            if key in seen:                     # 跨类别也去重，保留首次出现
                return
            seen.add(key)
            picked.append((str(category_key or _FREE_KEY), english))
            if str(raw).strip().lower() != key:
                pairs.append("%s→%s" % (str(raw).split("|")[0].strip(), english))

        for row in rows:
            push(row.get("category"), row.get("value"))
        for chunk in re.split(r"[,\n;，、]+", str(补充标签 or "")):
            push("extra", chunk)

        bpm_text = ""
        try:
            bpm_value = float(BPM or 0)
        except (TypeError, ValueError):
            bpm_value = 0.0
        if bpm_value > 0:
            bpm_text = "%g BPM" % bpm_value

        style = delimiter.join(value for _key, value in picked)
        if bpm_text:
            style = ("%s%s%s" % (style, delimiter, bpm_text)) if style else bpm_text

        if pairs:
            print("[Luy-预制风格] 中英对照: %s" % " | ".join(pairs), flush=True)
        print("[Luy-预制风格] 预设=%s 变体=%s ｜ %s ｜ style = %s" % (
            preset_name, variant["label"], "使用面板微调" if use_state else "预设+变体原样",
            style or "(空)"), flush=True)
        return {
            "ui": {
                "msp_preset": [preset_name],
                "msp_variant": [variant["label"]],
                "msp_result": [style],
                "msp_used_state": [use_state],
                "msp_rows": [{"category": key, "value": value} for key, value in picked],
                "msp_bpm": [bpm_text],
            },
            "result": (style,),
        }


NODE_CLASS_MAPPINGS = {
    "CJMusicStyleTags": CJMusicStyleTags,
    "CJMusicStyleReplacer": CJMusicStyleReplacer,
    "CJMusicStylePreset": CJMusicStylePreset,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CJMusicStyleTags": "Luy-音乐风格标签",
    "CJMusicStyleReplacer": "Luy-风格标签替换",
    "CJMusicStylePreset": "Luy-预制风格标签",
}
