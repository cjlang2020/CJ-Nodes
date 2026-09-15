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


NODE_CLASS_MAPPINGS = {
    "CJMusicStyleTags": CJMusicStyleTags,
    "CJMusicStyleReplacer": CJMusicStyleReplacer,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CJMusicStyleTags": "Luy-音乐风格标签",
    "CJMusicStyleReplacer": "Luy-风格标签替换",
}
