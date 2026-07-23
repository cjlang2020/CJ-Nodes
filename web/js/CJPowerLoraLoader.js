import { app } from "../../../../scripts/app.js";

const NODE_TYPE = "CJPowerLoraLoader";
const ROW_H = 22;
const HDR_H = 18;
const BTN_H = 22;
const PAD = 6;
const MARGIN = 12;

function fitString(ctx, str, maxWidth) {
  if (ctx.measureText(str).width <= maxWidth) return str;
  let lo = 0, hi = str.length;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (ctx.measureText(str.slice(0, mid)).width < maxWidth) lo = mid + 1;
    else hi = mid - 1;
  }
  return str.slice(0, Math.max(0, hi)) + "\u2026";
}

class CjPowerLoraWidget {
  constructor(name) {
    this.name = name;
    this.type = "custom";
    this.options = {};
    this.y = 0;
    this.last_y = 0;
    this.value = [];
    this._wData = null;
  }

  computeSize(width) {
    const n = this.value.length;
    let h = PAD;
    if (n > 0) h += HDR_H + 4;
    h += n * ROW_H + 4;
    h += BTN_H + PAD;
    return [width, h];
  }

  draw(ctx, node, width, posY, height) {
    const LQ = isLowQuality();
    const alpha = app.canvas.editor_alpha;
    let y = posY + PAD;

    ctx.save();
    ctx.globalAlpha = alpha;

    const innerW = width - MARGIN * 2;

    if (this.value.length > 0) {
      const allOn = this.value.every((l) => l.on);
      drawToggle(ctx, MARGIN, y, 14, allOn);
      ctx.fillStyle = "#888";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText("LoRA", MARGIN + 24, y + 7);
      ctx.textAlign = "center";
      ctx.fillText("\u5F3A\u5EA6", width - MARGIN - 50, y + 7);
      ctx.strokeStyle = "#333";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(MARGIN, y + 16);
      ctx.lineTo(width - MARGIN, y + 16);
      ctx.stroke();
      y += HDR_H + 4;
    }

    for (let i = 0; i < this.value.length; i++) {
      const lora = this.value[i];
      const rowY = y + i * ROW_H;

      if (!lora.on) ctx.globalAlpha = alpha * 0.4;
      else ctx.globalAlpha = alpha;

      ctx.fillStyle = "#2a2a2a";
      ctx.beginPath();
      ctx.roundRect(MARGIN, rowY, innerW, ROW_H - 2, 3);
      ctx.fill();

      drawToggle(ctx, MARGIN + 4, rowY + 4, 14, lora.on);

      ctx.fillStyle = lora.lora ? "#ddd" : "#666";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      const label = lora.lora || "\u9009\u62E9 LoRA...";
      const maxNameW = innerW - 28 - 64 - 16 - 4;
      ctx.fillText(fitString(ctx, label, maxNameW), MARGIN + 24, rowY + 10);

      const strX = width - MARGIN - 88;
      const btnW = 20;
      const valW = 30;
      const halfH = ROW_H - 6;
      const midY = rowY + 10;

      ctx.fillStyle = "#1a1a1a";
      ctx.beginPath();
      ctx.roundRect(strX, rowY + 2, btnW, halfH, 2);
      ctx.fill();
      ctx.fillStyle = lora.on ? "#ddd" : "#666";
      ctx.font = "12px monospace";
      ctx.textAlign = "center";
      ctx.fillText("\u2212", strX + btnW / 2, midY);

      ctx.fillStyle = "#1a1a1a";
      ctx.beginPath();
      ctx.roundRect(strX + btnW, rowY + 2, valW, halfH, 2);
      ctx.fill();
      ctx.strokeStyle = "#444";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.roundRect(strX + btnW, rowY + 2, valW, halfH, 2);
      ctx.stroke();
      ctx.fillStyle = "#ddd";
      ctx.font = "10px monospace";
      ctx.textAlign = "center";
      ctx.fillText(String(lora.strength ?? 1), strX + btnW + valW / 2, midY);

      ctx.fillStyle = "#1a1a1a";
      ctx.beginPath();
      ctx.roundRect(strX + btnW + valW, rowY + 2, btnW, halfH, 2);
      ctx.fill();
      ctx.fillStyle = lora.on ? "#ddd" : "#666";
      ctx.font = "12px monospace";
      ctx.textAlign = "center";
      ctx.fillText("+", strX + btnW + valW + btnW / 2, midY);

      if (!LQ) {
        ctx.fillStyle = "#c66";
        ctx.font = "10px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("\u2715", width - MARGIN - 8, rowY + 10);
      }

      ctx.globalAlpha = alpha;
    }

    const btnY = y + this.value.length * ROW_H + 4;
    if (!LQ) {
      ctx.fillStyle = "#1a1a1a";
      ctx.beginPath();
      ctx.roundRect(MARGIN, btnY, innerW, BTN_H, 3);
      ctx.fill();
      ctx.strokeStyle = "#555";
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#999";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("+ \u6DFB\u52A0 LoRA", width * 0.5, btnY + BTN_H * 0.5);
    }

    ctx.globalAlpha = 1;
    ctx.restore();
  }

  _contentStart(posY) {
    let y = posY + PAD;
    if (this.value.length > 0) y += HDR_H + 4;
    return y;
  }

  mouse(event, pos, node) {
    const canvas = app.canvas;
    const startY = this._contentStart(this.last_y);
    const btnY = startY + this.value.length * ROW_H + 4;

    if (event.type === "pointerdown") {
      const hdrY = this.last_y + PAD;

      if (this.value.length > 0 && pos[1] >= hdrY && pos[1] < hdrY + HDR_H) {
        if (pos[0] - MARGIN >= 4 && pos[0] - MARGIN <= 24) {
          const allOn = this.value.every((l) => l.on);
          this.value.forEach((l) => (l.on = !allOn));
          this._sync(node);
          node.setDirtyCanvas(true, true);
          return true;
        }
      }

      if (pos[1] >= btnY && pos[1] <= btnY + BTN_H) {
        this.value.push({ on: true, lora: "", strength: 1.0 });
        this._sync(node);
        node.setDirtyCanvas(true, true);
        return true;
      }

      const idx = Math.floor((pos[1] - startY) / ROW_H);
      if (idx >= 0 && idx < this.value.length) {
        const rowY = startY + idx * ROW_H;
        if (pos[1] < rowY || pos[1] > rowY + ROW_H) return true;
        const localX = pos[0] - MARGIN;
        const innerW = node.size[0] - MARGIN * 2;

        if (localX >= 4 && localX <= 24) {
          this.value[idx].on = !this.value[idx].on;
          this._sync(node);
          node.setDirtyCanvas(true, true);
          return true;
        }

        const strX = innerW - 88;
        const btnW = 20;
        const valW = 32;

        if (localX >= strX && localX < strX + btnW) {
          this.value[idx].strength = Math.round(((this.value[idx].strength ?? 1) - 0.1) * 10) / 10;
          this._sync(node);
          node.setDirtyCanvas(true, true);
          return true;
        }

        if (localX >= strX + btnW && localX < strX + btnW + valW) {
          canvas.prompt("\u5F3A\u5EA6", String(this.value[idx].strength ?? 1), (v) => {
            this.value[idx].strength = parseFloat(v) || 0;
            this._sync(node);
            node.setDirtyCanvas(true, true);
          }, event);
          return true;
        }

        if (localX >= strX + btnW + valW && localX < strX + btnW + valW + btnW) {
          this.value[idx].strength = Math.round(((this.value[idx].strength ?? 1) + 0.1) * 10) / 10;
          this._sync(node);
          node.setDirtyCanvas(true, true);
          return true;
        }

        if (localX >= innerW - 16 - 2 && localX <= innerW) {
          this.value.splice(idx, 1);
          this._sync(node);
          node.setDirtyCanvas(true, true);
          return true;
        }

        if (localX >= 24) {
          const loras = this._getLoraList(node);
          this._showLoraPicker(event, idx, node, loras);
          return true;
        }
      }
      return true;
    }

    if (event.type === "pointermove") {
      return true;
    }

    return false;
  }

  _getLoraList(node) {
    try {
      const w = node.widgets?.find((w) => w.name === "loras_list");
      if (w) return JSON.parse(w.value);
    } catch (e) {}
    return [];
  }

  async _showLoraPicker(event, idx, node, fallbackLoras) {
    let loras = fallbackLoras;
    try {
      const resp = await fetch("/cj-nodes/loras-list");
      if (resp.ok) loras = await resp.json();
    } catch (e) {}
    if (!loras || loras.length === 0) return;
    const currentLora = this.value[idx]?.lora || "";
    const used = new Set(
      this.value.filter((_, i) => i !== idx).map((v) => v.lora).filter(Boolean)
    );
    const orig = [...loras].filter((l) => !used.has(l)).sort();

    const items = orig.map((l) => ({
      title: l,
      callback: () => {
        this.value[idx].lora = l;
        this._sync(node);
        node.setDirtyCanvas(true, true);
      }
    }));

    const menu = new LiteGraph.ContextMenu(items, {
      title: currentLora || "\u9009\u62E9 LoRA",
      event
    });

    const menuEl = document.querySelector(".litecontextmenu");
    if (!menuEl) return;

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "\u641C\u7D22 LoRA...";
    input.style.cssText = "width:calc(100% - 12px);box-sizing:border-box;margin:4px 6px;padding:4px 6px;border:1px solid #555;border-radius:3px;background:#1a1a1a;color:#ddd;font-size:11px;outline:none;";

    const entryEls = menuEl.querySelectorAll(".litemenu-entry");

    const applyFilter = (filter) => {
      this._loraSearchFilter = filter;
      const f = filter.toLowerCase();
      entryEls.forEach((el, i) => {
        if (i < orig.length) {
          el.style.display = orig[i].toLowerCase().includes(f) ? "" : "none";
        }
      });
    };

    input.addEventListener("input", () => applyFilter(input.value));

    input.addEventListener("keydown", (e) => {
      e.stopPropagation();
      if (e.key === "Escape") {
        this._loraSearchFilter = "";
        const bg = document.querySelector(".litecontextmenu");
        if (bg) bg.remove();
      }
    });

    if (this._loraSearchFilter) {
      input.value = this._loraSearchFilter;
    }

    const titleEl = menuEl.querySelector(".litemenu-title");
    if (titleEl) {
      titleEl.after(input);
    } else {
      menuEl.prepend(input);
    }

    setTimeout(() => {
      input.focus();
      if (this._loraSearchFilter) {
        applyFilter(this._loraSearchFilter);
      }
    }, 0);
  }

  _sync(node) {
    const w = node.widgets?.find((w) => w.name === "loras_data");
    if (w) w.value = JSON.stringify(this.value);
  }

  serializeValue(node, idx) {
    return JSON.stringify(this.value);
  }
}

function drawToggle(ctx, x, y, size, on) {
  const r = size / 2;
  const cx = x + r;
  const cy = y + r;
  const bgW = size * 1.4;
  ctx.fillStyle = on ? "#89B" : "#555";
  ctx.beginPath();
  ctx.roundRect(x, y + 2, bgW, size - 4, (size - 4) / 2);
  ctx.fill();
  ctx.fillStyle = on ? "#fff" : "#ccc";
  ctx.beginPath();
  const dotX = on ? x + bgW - r - 2 : x + 2;
  ctx.arc(dotX, cy, r * 0.5, 0, Math.PI * 2);
  ctx.fill();
}

function isLowQuality() {
  return (app.canvas.ds?.scale || 1) <= 0.5;
}

app.registerExtension({
  name: "CJNodes.CJPowerLoraLoader",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE_TYPE) return;
    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onCreated?.apply(this, arguments);

      const wData = this.widgets?.find((w) => w.name === "loras_data");
      const wList = this.widgets?.find((w) => w.name === "loras_list");

      let loras = [];
      if (wData) {
        try { loras = JSON.parse(wData.value || "[]"); } catch (e) {}
        wData.hidden = true;
        wData.computeSize = () => [0, -4];
      }
      if (wList) {
        wList.hidden = true;
        wList.computeSize = () => [0, -4];
      }

      const widget = new CjPowerLoraWidget("cj_loras");
      widget.value = loras;
      widget._wData = wData;

      if (wData) {
        wData.serializeValue = function () {
          return JSON.stringify(widget.value);
        };
      }

      const origSerialize = this.onSerialize;
      this.onSerialize = function (state) {
        origSerialize?.apply(this, arguments);
        if (wData) wData.value = JSON.stringify(widget.value);
      };

      this.addCustomWidget(widget);
      const s = this.computeSize();
      this.size = this.size || [0, 0];
      this.size[0] = Math.max(380, this.size[0], s[0]);
      this.size[1] = Math.max(100, this.size[1], s[1]);
      this.setDirtyCanvas(true, true);
    };
  },
});
