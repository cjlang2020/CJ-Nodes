import json


class PromptBuilderNode:
    """可视化提示词构建器 - 前端输出Ideogram 4嵌套格式，后端透传或组装"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "prompt_data": ("STRING", {"default": "", "multiline": True,
                                            "tooltip": "前端序列化的完整参数JSON（隐藏）"}),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "INT")
    RETURN_NAMES = ("prompt_json", "width", "height")
    FUNCTION = "build_prompt"
    CATEGORY = "luy/提示词"

    NESTED_MARKER = "compositional_deconstruction"

    def build_prompt(self, prompt_data=""):
        data = self._parse(prompt_data)
        if not data:
            return ("", 1024, 1024)

        # ── 检测是否为前端输出的嵌套格式（Ideogram 4 JSON caption） ──
        if self.NESTED_MARKER in data:
            return self._forward_nested(data)

        # ── 向后兼容：旧版扁平格式 ──
        return self._build_from_flat(data)

    # ──────────────────────────────────────────────
    #  嵌套格式 — prompt_data 已经是 Ideogram 4 JSON
    #  直接透传，仅提取 width/height
    # ──────────────────────────────────────────────
    def _forward_nested(self, data):
        width = int(data.get("width", 1024))
        height = int(data.get("height", 1024))
        # 移除内部字段，只保留 caption schema
        out = {}
        if data.get("high_level_description"):
            out["high_level_description"] = data["high_level_description"]
        sd = data.get("style_description")
        if sd:
            out["style_description"] = sd
        cd = data.get("compositional_deconstruction")
        if cd:
            out["compositional_deconstruction"] = cd
        return (json.dumps(out, ensure_ascii=False, indent=2), width, height)

    # ──────────────────────────────────────────────
    #  扁平格式 — 旧版兼容
    # ──────────────────────────────────────────────
    def _build_from_flat(self, data):
        high_level_description = data.get("high_level_description", "")
        background = data.get("background", "")
        style = data.get("style", "none")
        aesthetics = data.get("aesthetics", "")
        lighting = data.get("lighting", "")
        medium = data.get("medium", "")
        photo_style = data.get("photo_style", "")
        art_style = data.get("art_style", "")
        regions = data.get("regions", [])
        style_color_palette = data.get("style_color_palette", [])
        width = int(data.get("width", 1024))
        height = int(data.get("height", 1024))

        prompt_json = self._build_json(
            high_level_description, background,
            style, aesthetics, lighting, medium,
            photo_style, art_style, regions, style_color_palette,
            width, height
        )
        return (prompt_json, width, height)

    def _parse(self, raw):
        if not raw:
            return {}
        try:
            d = json.loads(raw)
            return d if isinstance(d, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def _build_text(self, high_level_description, background, style,
                    aesthetics, lighting, medium, photo_style, art_style, regions):
        parts = []
        if high_level_description.strip():
            parts.append(high_level_description.strip())
        if style != "none":
            sp = []
            if aesthetics.strip(): sp.append(aesthetics.strip())
            if lighting.strip(): sp.append(lighting.strip())
            if style == "photo":
                if photo_style.strip(): sp.append(photo_style.strip())
                if medium.strip(): sp.append(medium.strip())
            else:
                if medium.strip(): sp.append(medium.strip())
                if art_style.strip(): sp.append(art_style.strip())
            if sp: parts.append(", ".join(sp))
        if background.strip(): parts.append(background.strip())
        for rg in regions:
            desc = rg.get("desc", "").strip()
            text = rg.get("text", "").strip()
            if text and desc: parts.append(f'"{text}" - {desc}')
            elif text: parts.append(f'"{text}"')
            elif desc: parts.append(desc)
        return ", ".join(parts) if parts else ""

    def _build_json(self, high_level_description, background,
                    style, aesthetics, lighting, medium,
                    photo_style, art_style, regions, style_color_palette,
                    width=1024, height=1024):
        out = {}

        if high_level_description.strip():
            out["high_level_description"] = high_level_description.strip()

        sd = {}
        if aesthetics.strip(): sd["aesthetics"] = aesthetics.strip()
        if lighting.strip(): sd["lighting"] = lighting.strip()
        if photo_style.strip(): sd["photo"] = photo_style.strip()
        if medium.strip(): sd["medium"] = medium.strip()
        scp = [c.upper() for c in style_color_palette if c]
        if scp: sd["color_palette"] = scp
        out["style_description"] = sd

        cd = {}
        if background.strip(): cd["background"] = background.strip()

        elems = []
        for rg in regions:
            elem = {"type": rg.get("type", "obj")}
            x, y, w, h = rg.get("x", 0), rg.get("y", 0), rg.get("w", 0), rg.get("h", 0)
            if w > 0 and h > 0:
                elem["bbox"] = self._to_grid(x, y, w, h, width, height)
            if rg.get("desc"): elem["desc"] = rg["desc"]
            pal = rg.get("palette", [])
            clean = [c.upper() for c in pal if c]
            if clean: elem["color_palette"] = clean
            elems.append(elem)
        cd["elements"] = elems
        out["compositional_deconstruction"] = cd

        return json.dumps(out, ensure_ascii=False, indent=2)

    def _to_grid(self, x, y, w, h, img_width=1024, img_height=1024):
        """将归一化坐标(0-1)转换为 0-1000 坐标系 [y1,x1,y2,x2]"""
        x1 = round(x * 1000)
        y1 = round(y * 1000)
        x2 = round((x + w) * 1000)
        y2 = round((y + h) * 1000)
        if x1 > x2: x1, x2 = x2, x1
        if y1 > y2: y1, y2 = y2, y1
        return [min(y1, 1000), min(x1, 1000), min(y2, 1000), min(x2, 1000)]

    def _build_preview(self, high_level_description, background,
                       style, aesthetics, lighting, medium,
                       photo_style, art_style, regions):
        lines = []
        if high_level_description.strip(): lines.append(f"Desc: {high_level_description.strip()}")
        if aesthetics.strip(): lines.append(f"Aesthetics: {aesthetics.strip()}")
        if lighting.strip(): lines.append(f"Lighting: {lighting.strip()}")
        if medium.strip(): lines.append(f"Medium: {medium.strip()}")
        if photo_style.strip(): lines.append(f"Photo: {photo_style.strip()}")
        if background.strip(): lines.append(f"Background: {background.strip()}")
        if regions:
            lines.append(f"Elements: {len(regions)}")
            for i, rg in enumerate(regions):
                tag = f"  [{i+1:02d}] {rg.get('type', 'obj')}"
                bbox = rg.get("bbox")
                if isinstance(bbox, list) and len(bbox) == 4:
                    tag += f" [{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}]"
                if rg.get("desc"): tag += f" - {rg['desc'][:40]}"
                lines.append(tag)
        return "\n".join(lines)
