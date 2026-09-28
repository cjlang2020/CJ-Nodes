// CJ-Nodes 预制风格标签（CJMusicStylePreset）前端面板
//
// 「预制风格」是原生 COMBO widget（可见、能存、没 JS 也能选）；本面板只做两件事：
// 1) 按 /CJ-Nodes/api/music-style/presets 的类别表，给每个类别渲染下拉（预设值自动填好）；
// 2) 用户改过的类别写入隐藏 widget「调整状态」（JSON {preset, rows}），后端只在 preset 与
//    本次「预制风格」一致时才采用 → 面板没加载 / 状态过期都不会改坏风格。
// 约定：面板不做解析、不做分类，取值一律是词表里的英文原文（显示中英对照）。
import { app } from "../../../../scripts/app.js";

const API_PRESETS = "/CJ-Nodes/api/music-style/presets";
const CUSTOM = "（自定义）";
const NONE = "（不选）";
const ALWAYS_KINDS = new Set(["vocab", "free"]);

let payload = null;
let payloadPromise = null;
let categoryMap = {};

function injectStyles() {
    if (document.getElementById("cj-msp-style")) return;
    const style = document.createElement("style");
    style.id = "cj-msp-style";
    style.textContent = `
        .cj-msp{display:flex;flex-direction:column;gap:4px;height:100%;min-height:0;padding:5px;font:11px/1.35 sans-serif;color:#ccc;box-sizing:border-box;overflow:hidden}
        .cj-msp-head{display:flex;align-items:center;gap:5px;flex-wrap:wrap;flex:0 0 auto}
        .cj-msp-info{color:#8fb7d6;font-size:10px;flex:1 1 100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-msp-note{color:#e6b422;font-size:10px;flex:0 0 auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-msp-list{display:flex;flex-direction:column;gap:3px;flex:1 1 auto;min-height:36px;overflow-y:auto}
        .cj-msp-row{display:flex;align-items:center;gap:4px;padding:2px 4px;border-radius:4px;background:#262626;border:1px solid #333}
        .cj-msp-row.changed{border-color:#e6a722;background:#2c2718}
        .cj-msp-lbl{flex:0 0 auto;width:52px;color:#9aa7b3;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-msp-row.changed .cj-msp-lbl{color:#e6a722}
        .cj-msp-sels{display:flex;flex:1 1 auto;gap:3px;min-width:0;flex-wrap:wrap}
        .cj-msp-sel{flex:1 1 96px;min-width:70px;background:#1a1a1a;border:1px solid #444;border-radius:3px;color:#ddd;font:10px sans-serif;padding:2px 3px;outline:none}
        .cj-msp-sel:focus{border-color:#46b4e6}
        .cj-msp-tools{display:flex;gap:2px;flex:0 0 auto}
        .cj-msp-tools button,.cj-msp-btn{padding:0 4px;height:17px;background:#2c2c2c;border:1px solid #444;border-radius:3px;color:#aaa;font:10px sans-serif;line-height:1;cursor:pointer}
        .cj-msp-tools button{width:17px;padding:0;font-family:monospace}
        .cj-msp-tools button:hover,.cj-msp-btn:hover{border-color:#46b4e6;color:#fff}
        .cj-msp-foot{display:flex;flex-direction:column;gap:2px;border-top:1px solid #333;padding-top:4px;flex:0 0 auto}
        .cj-msp-foot b{font-size:10px;color:#888;font-weight:normal}
        .cj-msp-prev{max-height:52px;overflow:auto;color:#8fbf8f;font:10px monospace;white-space:pre-wrap;word-break:break-all}
    `;
    document.head.appendChild(style);
}

function chainCallback(obj, prop, cb) {
    const old = obj[prop];
    obj[prop] = function (...args) {
        const result = old?.apply(this, args);
        cb.apply(this, args);
        return result;
    };
}

function nextFrame(callback) {
    const request = globalThis.requestAnimationFrame ?? ((fn) => setTimeout(fn, 16));
    request(callback);
}

// ── widget 读写 ─────────────────────────────────────────
function findWidgets(node) {
    const byName = (name) => node.widgets?.find((w) => w.name === name);
    return { preset: byName("预制风格"), variant: byName("变体"), state: byName("调整状态"),
             delimiter: byName("分隔符"), bpm: byName("BPM") };
}

function currentBpm(node) {
    const raw = Number(findWidgets(node).bpm?.value ?? 0);
    return Number.isFinite(raw) ? raw : 0;
}

function currentVariant(node) {
    const raw = String(findWidgets(node).variant?.value ?? "").trim();
    return raw || (payload?.variant_default ?? "标准");
}

function currentPreset(node) {
    const raw = String(findWidgets(node).preset?.value ?? "").trim();
    return raw || CUSTOM;
}

function currentDelimiter(node) {
    const raw = String(findWidgets(node).delimiter?.value ?? "");
    return raw === "" ? ", " : raw;
}

function setWidgetValue(node, key, value) {
    const widget = findWidgets(node)[key];
    if (!widget) return;
    widget.value = value;
    const index = node.widgets?.indexOf(widget);
    if (index != null && index >= 0 && Array.isArray(node.widgets_values)) node.widgets_values[index] = value;
    node.flags = node.flags || {};
    node.flags.dirty = true;
    app.graph?.setDirtyCanvas(true, false);
}

function readState(node) {
    const raw = findWidgets(node).state?.value;
    if (!raw) return null;
    try {
        const data = typeof raw === "string" ? JSON.parse(raw) : raw;
        if (!data || typeof data.preset !== "string" || !Array.isArray(data.rows)) return null;
        const rows = [];
        for (const row of data.rows) {
            const value = String(row?.value ?? "").trim();
            if (value) rows.push({ category: String(row?.category ?? "other"), value });
        }
        const base = [];
        for (const row of Array.isArray(data.base) ? data.base : []) {
            const value = String(row?.value ?? "").trim();
            if (value) base.push({ category: String(row?.category ?? "other"), value });
        }
        return { preset: data.preset, variant: String(data.variant ?? ""), rows, base };
    } catch (error) {
        return null;
    }
}

function writeState(node) {
    const payloadText = JSON.stringify({
        preset: node._msp.preset ?? currentPreset(node),
        variant: node._msp.variant ?? currentVariant(node),
        rows: node._msp.rows.map((row) => ({ category: row.category, value: row.value })),
        base: (node._msp.base ?? []).map((row) => ({ category: row.category, value: row.value })),
    });
    setWidgetValue(node, "state", payloadText);
}

// ── 词表 / 预设数据 ─────────────────────────────────────
function ensurePayload() {
    if (payload) return Promise.resolve(payload);
    if (!payloadPromise) {
        payloadPromise = fetch(API_PRESETS)
            .then((response) => {
                if (!response.ok) throw new Error("HTTP " + response.status);
                return response.json();
            })
            .then((data) => {
                if (!Array.isArray(data?.categories)) throw new Error("数据格式不对");
                payload = data;
                categoryMap = {};
                for (const category of data.categories) categoryMap[category.key] = category;
                return data;
            })
            .catch((error) => {
                payloadPromise = null;
                throw error;
            });
    }
    return payloadPromise;
}

function presetDef(label) {
    return (payload?.presets ?? []).find((item) => item.label === label) ?? null;
}

// 某个预设下的 10 个演绎（自定义走 custom_variants），后端已把 rows/bpm 算好
function variantList(label) {
    if (label === CUSTOM) return payload?.custom_variants ?? [];
    return presetDef(label)?.variants ?? [];
}

function variantEntry(label, variantLabel) {
    const list = variantList(label);
    const wanted = variantLabel || (payload?.variant_default ?? "标准");
    return list.find((item) => item.label === wanted) ?? list.find(
        (item) => item.label === (payload?.variant_default ?? "标准")) ?? null;
}

function fallbackCategory(key) {
    return { key, label: key, kind: "free", options: [], chips: [] };
}

// 固定显示词表类别（9 类 + 其他）；预设里带了结构型类别（如 upbeat → tempo_feel）时额外补一行
function visibleCategories(node) {
    const shown = (payload?.categories ?? []).filter((category) => ALWAYS_KINDS.has(category.kind));
    const keys = new Set(shown.map((category) => category.key));
    const extra = [];
    for (const row of node._msp.rows) {
        if (keys.has(row.category)) continue;
        keys.add(row.category);
        extra.push(categoryMap[row.category] ?? fallbackCategory(row.category));
    }
    return shown.concat(extra);
}

// ── 面板状态 ────────────────────────────────────────────
function rowsOf(node, categoryKey) {
    return node._msp.rows.filter((row) => row.category === categoryKey).map((row) => row.value);
}

function setCategoryRows(node, categoryKey, values) {
    node._msp.rows = node._msp.rows.filter((row) => row.category !== categoryKey);
    for (const value of values) {
        if (value) node._msp.rows.push({ category: categoryKey, value });
    }
    const order = visibleCategories(node).map((category) => category.key);
    const rank = (key) => {
        const index = order.indexOf(key);
        return index < 0 ? order.length : index;
    };
    node._msp.rows.sort((a, b) => rank(a.category) - rank(b.category));   // Array.sort 稳定 → 同类保序
}

function syncSlots(node) {
    node._msp.slots = {};
    for (const row of node._msp.rows) {
        node._msp.slots[row.category] = (node._msp.slots[row.category] ?? 0) + 1;
    }
}

function adoptRows(node, rows, label, variantLabel, base, note) {
    node._msp.preset = label;
    node._msp.variant = variantLabel;
    node._msp.rows = rows.map((row) => ({ category: row.category, value: row.value }));
    node._msp.base = (base ?? rows).map((row) => ({ category: row.category, value: row.value }));
    syncSlots(node);
    node._msp.note = note || "";
    node._msp.synced = true;
    renderRows(node);
    writeState(node);
}

function selectionNote(label, variantLabel) {
    const variantNote = (payload?.variants ?? []).find((item) => item.label === variantLabel)?.note || "";
    if (label === CUSTOM) {
        return variantNote ? "自定义模式 ｜ 变体：" + variantNote
            : "自定义模式：直接选各类别（没加载面板时请用「补充标签」手写）";
    }
    const presetNote = presetDef(label)?.note || "";
    return variantNote ? `${presetNote} ｜ 变体：${variantNote}` : presetNote;
}

// 应用「预设 + 变体」：行表与基准行表来自后端，BPM 写进原生 widget（可手改）
function applySelection(node, label, variantLabel, note) {
    const entry = variantEntry(label, variantLabel);
    const rows = (entry?.rows ?? []).map((row) => ({ category: String(row.category ?? "other"),
                                                     value: String(row.value ?? "") }));
    adoptRows(node, rows, label, variantLabel, rows, note || selectionNote(label, variantLabel));
    const bpm = Number(entry?.bpm ?? 0);
    if (bpm > 0) setWidgetValue(node, "bpm", bpm);
    renderHead(node);
}

// ── 渲染 ────────────────────────────────────────────────
function isChangedCategory(node, categoryKey) {
    const now = rowsOf(node, categoryKey).map((value) => value.toLowerCase()).sort();
    const base = (node._msp.base ?? []).filter((row) => row.category === categoryKey)
        .map((row) => row.value.toLowerCase()).sort();
    return now.join("|") !== base.join("|");
}

function bpmText(node) {
    const bpm = currentBpm(node);
    if (!bpm) return "速度 0（不输出）";
    const presetBpm = variantEntry(node._msp.preset, node._msp.variant)?.bpm ?? 0;
    return Math.abs(presetBpm - bpm) < 1e-6 ? `速度 ${bpm}（预设）` : `速度 ${bpm}（手填）`;
}

function renderHead(node) {
    const els = node._mspEls;
    if (!els) return;
    const ms = node._msp;
    const changed = visibleCategories(node).filter((category) => isChangedCategory(node, category.key)).length;
    const bits = [`预设「${ms.preset ?? currentPreset(node)}」`, `变体「${ms.variant ?? currentVariant(node)}」`,
        `标签 ${ms.rows.length} 个`];
    if (changed) bits.push(`已调 ${changed} 类`);
    bits.push(`分隔符「${currentDelimiter(node).replace(/\n/g, "\\n")}」`);
    bits.push(bpmText(node));
    els.info.textContent = bits.join(" ｜ ");
    els.note.textContent = ms.note || "";
    els.note.style.display = ms.note ? "" : "none";
    els.note.title = ms.note || "";
}

function renderFoot(node) {
    const els = node._mspEls;
    if (!els) return;
    const text = node._msp.rows.map((row) => row.value).join(currentDelimiter(node)
        .replace("\\n", "\n").replace("\\t", "\t"));
    els.prev.textContent = text || "（空）";
    els.prev.title = text;
}

function buildSelect(node, category, value) {
    const select = document.createElement("select");
    select.className = "cj-msp-sel";
    select.title = `${category.label}：显示「中文 | English」，取值只写英文`;

    const none = document.createElement("option");
    none.value = NONE;
    none.textContent = NONE;
    select.appendChild(none);

    const options = category.options ?? [];
    for (const option of options) {
        const entry = document.createElement("option");
        entry.value = option.value;
        entry.textContent = option.label ?? option.value;
        entry.title = option.label ?? option.value;
        select.appendChild(entry);
    }
    // 预设里写了词表没有的取值 → 补一个临时项，既能显示也不会被吞掉
    if (value && !options.some((option) => option.value === value)) {
        const extra = document.createElement("option");
        extra.value = value;
        extra.textContent = `预设: ${value}`;
        select.appendChild(extra);
        select.title += "（该取值不在词表里，可换成词表项）";
    }
    select.value = value || NONE;

    select.addEventListener("change", () => {
        const selects = node._mspEls.selects[category.key] ?? [];
        const values = selects.map((item) => (item.value === NONE ? "" : item.value));
        setCategoryRows(node, category.key, values);
        updateRowBadge(node, category.key);
        renderFoot(node);
        writeState(node);
    });
    return select;
}

function updateRowBadge(node, categoryKey) {
    const row = node._mspEls.rowEls?.[categoryKey];
    row?.classList.toggle("changed", isChangedCategory(node, categoryKey));
    renderHead(node);
}

function buildRow(node, category) {
    const row = document.createElement("div");
    row.className = "cj-msp-row";
    if (isChangedCategory(node, category.key)) row.classList.add("changed");

    const label = document.createElement("span");
    label.className = "cj-msp-lbl";
    label.textContent = category.label;
    label.title = category.key;

    const sels = document.createElement("div");
    sels.className = "cj-msp-sels";

    const values = rowsOf(node, category.key);
    const count = Math.max(1, node._msp.slots?.[category.key] ?? values.length);
    const limit = payload?.slot_limit ?? 6;
    const selects = [];
    for (let index = 0; index < count; index += 1) {
        const select = buildSelect(node, category, values[index] ?? "");
        selects.push(select);
        sels.appendChild(select);
    }
    node._mspEls.selects[category.key] = selects;
    node._mspEls.rowEls[category.key] = row;

    const tools = document.createElement("span");
    tools.className = "cj-msp-tools";
    if (count < limit) {
        const more = document.createElement("button");
        more.textContent = "+";
        more.title = `再加一个「${category.label}」标签`;
        more.addEventListener("click", () => {
            node._msp.slots[category.key] = count + 1;
            renderRows(node);
            writeState(node);
        });
        tools.appendChild(more);
    }
    if (count > 1) {
        const less = document.createElement("button");
        less.textContent = "✕";
        less.title = "去掉最后一个（其取值一并移除）";
        less.addEventListener("click", () => {
            node._msp.slots[category.key] = count - 1;
            const kept = values.slice(0, count - 1);
            setCategoryRows(node, category.key, kept);
            renderRows(node);
            writeState(node);
        });
        tools.appendChild(less);
    }

    row.append(label, sels, tools);
    return row;
}

function renderRows(node) {
    const els = node._mspEls;
    if (!els) return;
    const scroll = els.list.scrollTop;
    els.list.innerHTML = "";
    els.selects = {};
    els.rowEls = {};
    for (const category of visibleCategories(node)) els.list.appendChild(buildRow(node, category));
    els.list.scrollTop = scroll;
    renderHead(node);
    renderFoot(node);
    fitNodeHeight(node);
}

// 面板自然内容高度（行列表溢出时 scrollHeight 仍是内容高度）
function naturalContentHeight(node) {
    const els = node._mspEls;
    if (!els) return 0;
    const fixed = (els.head?.offsetHeight ?? 0) + (els.note?.offsetHeight ?? 0) + (els.foot?.offsetHeight ?? 0);
    return (els.list?.scrollHeight ?? 0) + fixed + 14;
}

function fitNodeHeight(node) {
    const wrap = node._mspWrap;
    if (!wrap || !node.size) return;
    const have = wrap.clientHeight;
    if (!have) {                                    // 还没布局完 → 下一帧再看（限次数，避免空转）
        if ((node._mspFitTry ?? 0) < 8) {
            node._mspFitTry = (node._mspFitTry ?? 0) + 1;
            nextFrame(() => fitNodeHeight(node));
        }
        return;
    }
    node._mspFitTry = 0;
    const need = naturalContentHeight(node);
    if (need <= have + 4) return;
    if (need <= (node._mspFitted ?? 0) + 4) return;   // 之前已按更大的内容调过 → 是用户自己缩的，不抢
    node.setSize([node.size[0], Math.min(1200, node.size[1] + (need - have))]);
    node._mspFitted = need;
}

// ── 同步（面板 ← 预制风格 widget / 工作流 / 执行结果）───
function syncPanel(node, force) {
    const label = currentPreset(node);
    const variantLabel = currentVariant(node);
    const saved = readState(node);
    const same = node._msp.preset === label && node._msp.variant === variantLabel;
    if (force) {                                     // 换预设/变体 / 点「↺ 重载预设」→ 预设+变体原样
        applySelection(node, label, variantLabel, same ? "已重置为预设+变体原样" : "");
        return;
    }
    if (node._msp.synced && same) {                  // 面板就是当前来源 → 保持现状
        renderRows(node);
        return;
    }
    if (saved && saved.preset === label && saved.variant === variantLabel) {   // 恢复工作流里的微调
        adoptRows(node, saved.rows, label, variantLabel, saved.base, "已恢复工作流里保存的微调");
        return;
    }
    applySelection(node, label, variantLabel, "");    // 首次加载 / 选择变了 → 预设+变体原样
}

function scheduleSync(node, delay, force) {
    clearTimeout(node._mspTimer);
    node._mspTimer = setTimeout(() => {
        node._mspTimer = null;
        syncPanel(node, !!force);
    }, delay ?? 60);
}

// ── 面板装配 ────────────────────────────────────────────
function buildPanel(node) {
    const wrap = document.createElement("div");
    wrap.className = "cj-msp";
    node._mspWrap = wrap;

    const head = document.createElement("div");
    head.className = "cj-msp-head";
    const info = document.createElement("span");
    info.className = "cj-msp-info";

    const reload = document.createElement("button");
    reload.className = "cj-msp-btn";
    reload.textContent = "↺ 重载预设";
    reload.title = "丢弃面板上的微调，回到「预制风格」的原样";

    const clear = document.createElement("button");
    clear.className = "cj-msp-btn";
    clear.textContent = "清空 / 自定义";
    clear.title = "切成「（自定义）」并清空所有类别（之后按面板 / 补充标签拼）";

    head.append(info, reload, clear);

    const note = document.createElement("div");
    note.className = "cj-msp-note";

    const list = document.createElement("div");
    list.className = "cj-msp-list";

    const foot = document.createElement("div");
    foot.className = "cj-msp-foot";
    const footLabel = document.createElement("b");
    footLabel.textContent = "面板预览（= 生成节点收到的 style，不含「补充标签」与 BPM）";
    const prev = document.createElement("div");
    prev.className = "cj-msp-prev";
    foot.append(footLabel, prev);

    wrap.append(head, note, list, foot);
    node._mspEls = { info, note, list, prev, head, foot, selects: {}, rowEls: {} };

    reload.addEventListener("click", () => {
        syncPanel(node, true);
    });
    clear.addEventListener("click", () => {
        setWidgetValue(node, "preset", CUSTOM);
        setWidgetValue(node, "variant", payload?.variant_default ?? "标准");
        setWidgetValue(node, "bpm", 0);
        applySelection(node, CUSTOM, payload?.variant_default ?? "标准", "已清空（自定义模式）");
    });

    // 高度不写死：新前端按 computeLayoutSize 把节点剩余空间全分给 DOM widget（跟着节点高度变），
    // 旧画布路径看 --comfy-widget-min-height。**不能给 widget 加 computeSize**——那会被当成
    // 固定高度 widget 而拿不到弹性空间（1.52 的 _arrangeWidgets 行为）。
    wrap.style.setProperty("--comfy-widget-min-height", "320px");
    node.addDOMWidget("msp_panel", "预制风格", wrap, {
        getValue: () => "",
        setValue: () => {},
    });
}

function hookSelectWidgets(node) {
    for (const widget of [findWidgets(node).preset, findWidgets(node).variant]) {
        if (!widget) continue;
        const original = widget.callback;
        widget.callback = function (...args) {
            const result = original?.apply(this, args);
            node._msp.synced = false;
            scheduleSync(node, 0, true);
            return result;
        };
    }
}

app.registerExtension({
    name: "CJNodes.MusicStylePreset",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CJMusicStylePreset") return;
        injectStyles();

        chainCallback(nodeType.prototype, "onNodeCreated", function () {
            const node = this;
            node._msp = { preset: null, variant: null, rows: [], base: [], slots: {}, note: "", synced: false };

            const stateWidget = findWidgets(node).state;
            if (stateWidget) {
                stateWidget.hidden = true;
                stateWidget.computeSize = () => [0, -4];
            }

            buildPanel(node);
            hookSelectWidgets(node);
            renderRows(node);

            ensurePayload()
                .then(() => { renderRows(node); scheduleSync(node, 0, false); })
                .catch((error) => {
                    node._msp.note = "面板数据加载失败：" + (error?.message || error)
                        + "（/CJ-Nodes/api/music-style/presets 未加载？新增路由需重启一次 ComfyUI）";
                    renderHead(node);
                });

            node.setSize([Math.max(640, node.size[0]), Math.max(420, node.size[1])]);
            app.graph?.setDirtyCanvas(true, true);
        });

        // 工作流里的 widgets_values 在 onNodeCreated 之后才回填 → 再同步一次
        chainCallback(nodeType.prototype, "onConfigure", function () {
            if (!this._msp) return;
            this._msp.synced = false;
            scheduleSync(this, 30, false);
        });

        chainCallback(nodeType.prototype, "onWidgetChanged", function (name) {
            if (!this._msp) return;
            if (name === "预制风格" || name === "变体") { this._msp.synced = false; scheduleSync(this, 0, true); }
            else if (name === "调整状态") { this._msp.synced = false; scheduleSync(this, 60, false); }
            else if (name === "BPM" || name === "分隔符") renderHead(this);
        });

        chainCallback(nodeType.prototype, "onExecuted", function (message) {
            const node = this;
            if (!node._msp || !message) return;
            const used = !!message.msp_used_state?.[0];
            const result = String(message.msp_result?.[0] ?? "");
            const preset = String(message.msp_preset?.[0] ?? "");
            const variantLabel = String(message.msp_variant?.[0] ?? "");
            ensurePayload()
                .then(() => {
                    if ((preset && preset !== node._msp.preset)
                        || (variantLabel && variantLabel !== node._msp.variant)) {
                        applySelection(node, preset || currentPreset(node),
                            variantLabel || currentVariant(node), "已按执行结果同步预设/变体");
                        return;
                    }
                    if (!used) {                 // 正常用上面板微调时不覆盖预设的说明文字
                        node._msp.note = node._msp.rows.length
                            ? "本次执行按预设原样输出（面板微调未被采用：预设与状态不一致）"
                            : "本次执行没有面板标签（自定义模式且未选任何类别）";
                        renderHead(node);
                    }
                })
                .catch(() => {});
            if (result) {
                const els = node._mspEls;
                if (els) { els.prev.textContent = result; els.prev.title = result; }
            }
        });

        chainCallback(nodeType.prototype, "onRemoved", function () {
            clearTimeout(this._mspTimer);
            this._mspTimer = null;
        });
    },
});

console.log("CJ-Nodes MusicStylePreset UI loaded");
