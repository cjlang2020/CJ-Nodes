// CJ-Nodes 风格标签替换（CJMusicStyleReplacer）前端面板
//
// 面板本身不做解析：行表来自 /CJ-Nodes/api/music-style/parse 或节点执行返回的 ui 载荷，
// 用户改完把整张行表写回隐藏 widget「替换状态」，后端按行逐字拼接。
// 三条约束：
// 1) 面板是"编辑视图"：没编辑过就不写状态（节点保持原样透传）；
// 2) 只在 source 与面板行表一致时才写状态（后端同样按 source 校验）；
// 3) 词表/接口挂了只能降级（显示文字框），不能影响节点执行。
import { app } from "../../../../scripts/app.js";

const API_VOCAB = "/CJ-Nodes/api/music-style/vocab";
const API_PARSE = "/CJ-Nodes/api/music-style/parse";
const CUSTOM_VALUE = "__custom__";
const CHIP_LIMIT = 8;
const FREE_KEY = "other";

let vocab = null;
let vocabPromise = null;
let categoryMap = {};

function injectStyles() {
    if (document.getElementById("cj-ms-style")) return;
    const style = document.createElement("style");
    style.id = "cj-ms-style";
    style.textContent = `
        .cj-ms{display:flex;flex-direction:column;gap:4px;height:100%;min-height:0;padding:5px;font:11px/1.35 sans-serif;color:#ccc;box-sizing:border-box;overflow:hidden}
        .cj-ms-head{display:flex;align-items:center;gap:5px;flex-wrap:wrap}
        .cj-ms-info{color:#8fb7d6;font-size:10px;flex:1 1 100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-ms-note{color:#e6b422;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-ms-list{display:flex;flex-direction:column;gap:3px;flex:1 1 auto;min-height:36px;overflow-y:auto}
        .cj-ms-item{display:flex;flex-direction:column;gap:2px;padding:3px 4px;border-radius:4px;background:#262626;border:1px solid #333}
        .cj-ms-item.changed{border-color:#e6a722}
        .cj-ms-line{display:flex;align-items:center;gap:4px}
        .cj-ms-idx{width:13px;flex:0 0 auto;text-align:right;color:#666;font:10px monospace}
        .cj-ms-cat,.cj-ms-pick,.cj-ms-txt{background:#1a1a1a;border:1px solid #444;border-radius:3px;color:#ddd;font:10px sans-serif;padding:2px 3px;outline:none;min-width:0}
        .cj-ms-cat{flex:0 0 auto;width:92px}
        .cj-ms-pick{flex:1 1 42%}
        .cj-ms-txt{flex:1 1 42%}
        .cj-ms-cat:focus,.cj-ms-pick:focus,.cj-ms-txt:focus{border-color:#46b4e6}
        .cj-ms-tools{display:flex;gap:2px;flex:0 0 auto}
        .cj-ms-tools button{width:17px;height:17px;padding:0;background:#2c2c2c;border:1px solid #444;border-radius:3px;color:#aaa;font:10px monospace;line-height:1;cursor:pointer}
        .cj-ms-tools button:hover{border-color:#46b4e6;color:#fff}
        .cj-ms-chips{display:flex;flex-wrap:wrap;gap:3px;padding-left:17px}
        .cj-ms-chip{max-width:190px;padding:1px 6px;overflow:hidden;background:#222;border:1px solid #3a3a3a;border-radius:9px;color:#9fb8cc;font:10px sans-serif;white-space:nowrap;text-overflow:ellipsis;cursor:pointer}
        .cj-ms-chip:hover,.cj-ms-chip.on{background:#2f4a5e;border-color:#46b4e6;color:#fff}
        .cj-ms-foot{display:flex;flex-direction:column;gap:2px;border-top:1px solid #333;padding-top:4px}
        .cj-ms-foot b{font-size:10px;color:#888;font-weight:normal}
        .cj-ms-prev{max-height:52px;overflow:auto;color:#8fbf8f;font:10px monospace;white-space:pre-wrap;word-break:break-all}
        .cj-ms-empty{color:#777;padding:5px;font-size:10px}
        .cj-ms-btn{padding:2px 6px;background:#2c2c2c;border:1px solid #444;border-radius:3px;color:#ccc;font:10px sans-serif;cursor:pointer}
        .cj-ms-btn:hover{background:#3a3a3a;border-color:#46b4e6;color:#fff}
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

// ── 小工具 ──────────────────────────────────────────────
function findWidgets(node) {
    const byName = (name) => node.widgets?.find((w) => w.name === name);
    return { source: byName("风格"), delimiter: byName("分隔符"), state: byName("替换状态") };
}

function currentSource(node) {
    return String(findWidgets(node).source?.value ?? "");
}

function currentDelimiter(node) {
    const raw = String(findWidgets(node).delimiter?.value ?? "");
    return raw === "" ? ", " : raw;
}

function hasUpstream(node) {
    const input = node.inputs?.find((item) => item.name === "风格");
    return !!(input && input.link != null);
}

function sameValue(a, b) {
    return String(a ?? "").trim().toLowerCase() === String(b ?? "").trim().toLowerCase();
}

function isChanged(row) {
    return !!row.text && row.value !== row.text && !!row.value;
}

function joinValues(rows, delimiter) {
    const text = delimiter.replace("\\n", "\n").replace("\\t", "\t");
    return rows.map((row) => String(row.value ?? "").trim()).filter(Boolean).join(text);
}

function normalizeRow(row) {
    const value = String(row?.value ?? row?.text ?? "");
    return {
        text: String(row?.text ?? value),
        category: String(row?.category ?? FREE_KEY),
        value,
        suggest: Array.isArray(row?.suggest) ? row.suggest : null,
    };
}

function toolButton(text, title, onClick) {
    const button = document.createElement("button");
    button.textContent = text;
    button.title = title;
    button.addEventListener("click", onClick);
    return button;
}

// ── 词表 / 接口 ─────────────────────────────────────────
function ensureVocab() {
    if (vocab) return Promise.resolve(vocab);
    if (!vocabPromise) {
        vocabPromise = fetch(API_VOCAB)
            .then((response) => {
                if (!response.ok) throw new Error("HTTP " + response.status);
                return response.json();
            })
            .then((data) => {
                if (!Array.isArray(data?.categories)) throw new Error("词表格式不对");
                vocab = data;
                categoryMap = {};
                for (const category of data.categories) categoryMap[category.key] = category;
                return data;
            })
            .catch((error) => {
                vocabPromise = null;
                throw error;
            });
    }
    return vocabPromise;
}

async function apiParse(source, delimiter) {
    const response = await fetch(API_PARSE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ style: source, delimiter }),
    });
    if (!response.ok) throw new Error("HTTP " + response.status);
    return await response.json();
}

// ── 状态读写 ────────────────────────────────────────────
function readState(node) {
    const raw = findWidgets(node).state?.value;
    if (!raw) return null;
    try {
        const data = typeof raw === "string" ? JSON.parse(raw) : raw;
        if (!data || typeof data.source !== "string" || !Array.isArray(data.rows)) return null;
        return data;
    } catch (error) {
        return null;
    }
}

function writeState(node) {
    const widget = findWidgets(node).state;
    if (!widget) return;
    const payload = JSON.stringify({
        source: node._ms.source ?? "",
        rows: node._ms.rows.map((row) => ({ text: row.text, category: row.category, value: row.value,
                                            suggest: row.suggest ?? null })),
    });
    widget.value = payload;
    const index = node.widgets?.indexOf(widget);
    if (index != null && index >= 0 && Array.isArray(node.widgets_values)) node.widgets_values[index] = payload;
    node.flags = node.flags || {};
    node.flags.dirty = true;
    app.graph?.setDirtyCanvas(true, false);
}

function setNote(node, note) {
    node._ms.note = note || "";
    renderHead(node);
}

// ── 渲染 ────────────────────────────────────────────────
function renderHead(node) {
    const els = node._msEls;
    if (!els) return;
    const ms = node._ms;
    const changed = ms.rows.filter(isChanged).length;
    const bits = [hasUpstream(node) ? "输入：上游连线" : (currentSource(node).trim() ? "输入：手输/粘贴" : "输入：空")];
    bits.push(`标签 ${ms.rows.length} 个`);
    if (changed) bits.push(`已改 ${changed} 项`);
    bits.push(`分隔符「${currentDelimiter(node).replace(/\n/g, "\\n")}」`);
    els.info.textContent = bits.join(" ｜ ");
    els.note.textContent = ms.note || "";
    els.note.style.display = ms.note ? "" : "none";
    fillCategorySelect(els.addSelect, els.addSelect.value || FREE_KEY);
}

function renderFoot(node) {
    const els = node._msEls;
    if (!els) return;
    const result = joinValues(node._ms.rows, currentDelimiter(node));
    els.prev.textContent = result || "（空）";
    els.prev.title = result;
}

function renderRows(node) {
    const els = node._msEls;
    if (!els) return;
    const scroll = els.list.scrollTop;
    els.list.innerHTML = "";
    if (!node._ms.rows.length) {
        const empty = document.createElement("div");
        empty.className = "cj-ms-empty";
        empty.textContent = "（无标签）连接扒谱「风格底稿」后本节点执行一次即可回填，"
            + "或直接在「风格」里粘贴文本再点「重新解析」";
        els.list.appendChild(empty);
    } else {
        node._ms.rows.forEach((row, index) => els.list.appendChild(buildRow(node, row, index)));
    }
    els.list.scrollTop = scroll;
    renderHead(node);
    renderFoot(node);
    fitNodeHeight(node);
}

function buildRow(node, row, index) {
    if (!categoryMap[row.category]) row.category = FREE_KEY;
    const item = document.createElement("div");
    item.className = "cj-ms-item" + (isChanged(row) ? " changed" : "");

    const line = document.createElement("div");
    line.className = "cj-ms-line";

    const idx = document.createElement("span");
    idx.className = "cj-ms-idx";
    idx.textContent = String(index + 1);

    const catSelect = document.createElement("select");
    catSelect.className = "cj-ms-cat";
    catSelect.title = "标签类别";
    for (const category of vocab?.categories ?? []) {
        const option = document.createElement("option");
        option.value = category.key;
        option.textContent = category.label;
        catSelect.appendChild(option);
    }
    catSelect.value = row.category;
    catSelect.addEventListener("change", () => {
        row.category = catSelect.value;
        row.suggest = null;
        renderRows(node);
        writeState(node);
    });

    const input = document.createElement("input");
    input.className = "cj-ms-txt";
    input.value = row.value ?? "";
    input.title = isChanged(row) ? `当前值（原值: ${row.text}）` : "取值（可手输）";

    const pick = buildPick(node, row, item, input);

    input.addEventListener("input", () => {
        row.value = input.value;
        syncPick(pick, row);
        touchRow(node, row, item);
    });

    const tools = document.createElement("span");
    tools.className = "cj-ms-tools";
    tools.appendChild(toolButton("↺", "恢复为原始标签", () => {
        row.value = row.text;
        renderRows(node);
        writeState(node);
    }));
    tools.appendChild(toolButton("↑", "上移", () => moveRow(node, index, -1)));
    tools.appendChild(toolButton("↓", "下移", () => moveRow(node, index, 1)));
    tools.appendChild(toolButton("✕", "删除本标签", () => {
        node._ms.rows.splice(index, 1);
        renderRows(node);
        writeState(node);
    }));

    line.append(idx, catSelect, pick, input, tools);
    item.appendChild(line);
    const chips = buildChips(node, row, input);
    if (chips) item.appendChild(chips);
    return item;
}

function buildPick(node, row, item, input) {
    const select = document.createElement("select");
    select.className = "cj-ms-pick";
    select.title = "候选取值（显示「中文 | English」，取值只写英文）";
    syncPick(select, row);
    select.addEventListener("change", () => {
        if (select.value === CUSTOM_VALUE) {
            input.focus();
            return;
        }
        row.value = select.value;
        input.value = row.value;
        touchRow(node, row, item);
    });
    return select;
}

function syncPick(select, row) {
    const options = categoryMap[row.category]?.options ?? [];
    select.innerHTML = "";
    const custom = document.createElement("option");
    custom.value = CUSTOM_VALUE;
    custom.textContent = "（自定义/自由文本）";
    select.appendChild(custom);
    for (const option of options) {
        const entry = document.createElement("option");
        entry.value = option.value;
        entry.textContent = option.label ?? option.value;
        entry.title = option.label ?? option.value;
        select.appendChild(entry);
    }
    const hit = options.find((option) => sameValue(option.value, row.value));
    select.value = hit ? hit.value : CUSTOM_VALUE;
}

function buildChips(node, row, input) {
    const category = categoryMap[row.category];
    const values = (row.suggest?.length ? row.suggest : (category?.chips ?? [])).slice(0, CHIP_LIMIT);
    if (!values.length) return null;
    const wrap = document.createElement("div");
    wrap.className = "cj-ms-chips";
    for (const value of values) {
        const option = category?.options?.find((item) => sameValue(item.value, value));
        const chip = document.createElement("button");
        chip.className = "cj-ms-chip" + (sameValue(value, row.value) ? " on" : "");
        chip.textContent = option?.short ?? value;
        chip.title = option?.label ?? value;
        chip.addEventListener("click", () => {
            row.value = value;
            input.value = value;
            renderRows(node);
            writeState(node);
        });
        wrap.appendChild(chip);
    }
    return wrap;
}

function touchRow(node, row, item) {
    item?.classList.toggle("changed", isChanged(row));
    renderFoot(node);
    writeState(node);
}

function moveRow(node, index, delta) {
    const rows = node._ms.rows;
    const target = index + delta;
    if (target < 0 || target >= rows.length) return;
    [rows[index], rows[target]] = [rows[target], rows[index]];
    renderRows(node);
    writeState(node);
}

function fillCategorySelect(select, value) {
    if (!select) return;
    const options = vocab?.categories ?? [];
    if (select.options.length !== options.length) {
        select.innerHTML = "";
        for (const category of options) {
            const option = document.createElement("option");
            option.value = category.key;
            option.textContent = category.label;
            select.appendChild(option);
        }
    }
    if (options.some((category) => category.key === value)) select.value = value;
}

function fitNodeHeight(node) {
    const wrap = node._msWrap;
    if (!wrap || !node.size) return;
    const have = wrap.clientHeight;
    if (!have) {                                    // 还没布局完 → 下一帧再看（限次数，避免空转）
        if ((node._msFitTry ?? 0) < 8) {
            node._msFitTry = (node._msFitTry ?? 0) + 1;
            nextFrame(() => fitNodeHeight(node));
        }
        return;
    }
    node._msFitTry = 0;
    const need = naturalContentHeight(node);
    if (need <= have + 4) return;
    if (need <= (node._msFitted ?? 0) + 4) return;   // 之前已按更大的内容调过 → 是用户自己缩的，不抢
    node.setSize([node.size[0], Math.min(1200, node.size[1] + (need - have))]);
    node._msFitted = need;
}

// 面板自然内容高度（行列表溢出时 scrollHeight 仍是内容高度）
function naturalContentHeight(node) {
    const els = node._msEls;
    if (!els) return 0;
    const fixed = (els.head?.offsetHeight ?? 0) + (els.note?.offsetHeight ?? 0) + (els.foot?.offsetHeight ?? 0);
    return (els.list?.scrollHeight ?? 0) + fixed + 14;
}

function nextFrame(callback) {
    const request = globalThis.requestAnimationFrame ?? ((fn) => setTimeout(fn, 16));
    request(callback);
}

// ── 同步（面板 ← 输入/执行结果）──────────────────────────
function adoptRows(node, rows, source, note) {
    node._ms.source = source;
    node._ms.rows = rows.map(normalizeRow);
    node._ms.note = note || "";
    renderRows(node);
    writeState(node);
}

async function parseFromApi(node, source) {
    setNote(node, "解析中…");
    try {
        await ensureVocab();
        const data = await apiParse(source, currentDelimiter(node));
        adoptRows(node, Array.isArray(data.rows) ? data.rows : [], source,
            hasUpstream(node) ? "已按当前输入解析（先执行一次才能读到上游值）" : "已按输入文本解析");
    } catch (error) {
        node._ms.source = source;
        node._ms.rows = [];
        renderRows(node);
        setNote(node, "解析失败：" + (error?.message || error)
            + "（词表/解析接口未加载？新增路由需重启一次 ComfyUI）");
    }
}

function syncPanel(node, force) {
    const ms = node._ms ?? (node._ms = { source: null, rows: [], note: "" });
    const source = currentSource(node);
    if (!force && ms.source === source && ms.rows.length) { renderRows(node); return; }
    const saved = readState(node);
    if (!force && saved && saved.source === source && saved.rows.length) {
        adoptRows(node, saved.rows, source, "已恢复工作流里保存的替换");
        return;
    }
    if (!source.trim()) {
        // 连线上游时「风格」widget 自身永远是空的 → 那不代表"输入被清空"，绝不能拿它抹掉行表
        if (hasUpstream(node)) {
            if (ms.rows.length) {
                if (force) { ms.rows = ms.rows.map((row) => ({ ...row, value: row.text })); writeState(node); }  // 重解析=放弃修改
                renderRows(node);
                return;
            }
            if (saved && saved.rows.length) {       // 刚加载：先把上次保存的行表显示出来（执行时再校验 source）
                adoptRows(node, saved.rows, saved.source, "已恢复工作流里保存的替换");
                return;
            }
        }
        ms.source = source;
        ms.rows = [];
        ms.note = "";
        renderRows(node);
        setNote(node, "「风格」是空的：连接扒谱「风格底稿」（执行一次后回填），或粘贴文本后点「重新解析」");
        return;
    }
    parseFromApi(node, source);
}

function scheduleSync(node, delay) {
    clearTimeout(node._msTimer);
    node._msTimer = setTimeout(() => {
        node._msTimer = null;
        syncPanel(node);
    }, delay ?? 60);
}

// ── 面板装配 ────────────────────────────────────────────
function buildPanel(node) {
    const wrap = document.createElement("div");
    wrap.className = "cj-ms";
    node._msWrap = wrap;

    const head = document.createElement("div");
    head.className = "cj-ms-head";
    const info = document.createElement("span");
    info.className = "cj-ms-info";
    const addSelect = document.createElement("select");
    addSelect.className = "cj-ms-cat";
    addSelect.title = "要新增的标签类别";
    const addButton = document.createElement("button");
    addButton.className = "cj-ms-btn";
    addButton.textContent = "+ 添加标签";
    addButton.title = "按左侧类别新增一个空标签行";
    addButton.addEventListener("click", () => {
        node._ms.rows.push({ text: "", category: addSelect.value || FREE_KEY, value: "", suggest: null });
        renderRows(node);
        writeState(node);
        const last = node._msEls.list.querySelector(".cj-ms-item:last-child .cj-ms-txt");
        last?.focus();
    });
    const reparseButton = document.createElement("button");
    reparseButton.className = "cj-ms-btn";
    reparseButton.textContent = "重新解析";
    reparseButton.title = "放弃面板上的修改，按「风格」里的文本（或上游执行结果）重新拆一遍";
    reparseButton.addEventListener("click", () => syncPanel(node, true));
    head.append(info, addSelect, addButton, reparseButton);

    const note = document.createElement("div");
    note.className = "cj-ms-note";

    const list = document.createElement("div");
    list.className = "cj-ms-list";

    const foot = document.createElement("div");
    foot.className = "cj-ms-foot";
    const footLabel = document.createElement("b");
    footLabel.textContent = "输出预览（= 生成节点收到的 style）";
    const prev = document.createElement("div");
    prev.className = "cj-ms-prev";
    foot.append(footLabel, prev);

    wrap.append(head, note, list, foot);
    node._msEls = { info, note, list, prev, addSelect };

    // 高度不写死：新前端按 computeLayoutSize 把节点剩余空间全分给 DOM widget（跟着节点高度变），
    // 旧画布路径看 --comfy-widget-min-height。**不能给 widget 加 computeSize**——那样会被
    // 当成固定高度 widget 而拿不到弹性空间（1.52 的 _arrangeWidgets 行为）。
    wrap.style.setProperty("--comfy-widget-min-height", "200px");
    node.addDOMWidget("ms_panel", "风格标签替换", wrap, {
        getValue: () => "",
        setValue: () => {},
    });
}

function hookSourceWidget(node) {
    const sourceWidget = findWidgets(node).source;
    if (!sourceWidget) return;
    const original = sourceWidget.callback;
    sourceWidget.callback = function (...args) {
        const result = original?.apply(this, args);
        scheduleSync(node, 400);
        return result;
    };
}

app.registerExtension({
    name: "CJNodes.MusicStyleReplacer",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "CJMusicStyleReplacer") return;
        injectStyles();

        chainCallback(nodeType.prototype, "onNodeCreated", function () {
            const node = this;
            node._ms = { source: null, rows: [], note: "" };

            const stateWidget = findWidgets(node).state;
            if (stateWidget) {
                stateWidget.hidden = true;
                stateWidget.computeSize = () => [0, -4];
            }

            buildPanel(node);
            hookSourceWidget(node);
            renderRows(node);

            ensureVocab()
                .then(() => { renderRows(node); scheduleSync(node, 0); })
                .catch((error) => setNote(node, "词表加载失败：" + (error?.message || error)
                    + "（/CJ-Nodes/api/music-style/vocab 未加载？新增路由需重启一次 ComfyUI）"));

            node.setSize([Math.max(620, node.size[0]), Math.max(340, node.size[1])]);
            app.graph?.setDirtyCanvas(true, true);
        });

        // 工作流里的 widgets_values 在 onNodeCreated 之后才回填 → 再同步一次
        chainCallback(nodeType.prototype, "onConfigure", function () {
            scheduleSync(this, 30);
        });

        chainCallback(nodeType.prototype, "onWidgetChanged", function (name) {
            if (name === "风格" || name === "替换状态") scheduleSync(this, 400);
        });

        chainCallback(nodeType.prototype, "onExecuted", function (message) {
            const node = this;
            if (!node._ms || !message) return;
            const source = String(message.ms_source?.[0] ?? "");
            const usedState = !!message.ms_used_state?.[0];
            const rows = Array.isArray(message.ms_rows) ? message.ms_rows : null;
            ensureVocab()
                .then(() => {
                    if (!usedState && rows) {
                        adoptRows(node, rows, source, rows.length
                            ? "已按执行输入解析（在这里改完，下一次执行生效）"
                            : "执行输入为空");
                        return;
                    }
                    if (usedState && !node._ms.rows.length) {
                        const saved = readState(node);
                        if (saved && saved.rows.length) {
                            adoptRows(node, saved.rows, source, "已恢复工作流里保存的替换");
                            return;
                        }
                    }
                    setNote(node, "本次执行使用了面板替换");
                })
                .catch(() => {});
        });

        chainCallback(nodeType.prototype, "onRemoved", function () {
            clearTimeout(this._msTimer);
            this._msTimer = null;
        });
    },
});

console.log("CJ-Nodes MusicStyleReplacer UI loaded");
