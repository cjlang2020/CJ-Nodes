import { app } from "../../../../scripts/app.js";

function injectStyles() {
    if (document.getElementById("cj-lora-loader-style")) return;
    const s = document.createElement("style");
    s.id = "cj-lora-loader-style";
    s.textContent = `
        .cj-ll{display:flex;flex-direction:column;gap:4px;padding:4px;font:10px sans-serif;color:#ccc}
        .cj-ll-row{display:flex;align-items:center;gap:6px}
        .cj-ll-label{width:52px;flex:0 0 auto;color:#aaa;font-size:10px;text-align:left;white-space:nowrap}
        .cj-ll-select{flex:1;min-width:0;background:#1a1a1a;border:1px solid #444;border-radius:3px;color:#ddd;font:10px sans-serif;padding:2px 4px;outline:none;cursor:pointer;appearance:auto}
        .cj-ll-select:focus{border-color:#46b4e6}
        .cj-ll-strength{width:64px;flex:0 0 auto;background:#1a1a1a;border:1px solid #444;border-radius:3px;color:#ddd;font:10px monospace;padding:2px 4px;outline:none;text-align:center}
        .cj-ll-strength:focus{border-color:#46b4e6}
    `;
    document.head.appendChild(s);
}

function chainCallback(obj, prop, cb) {
    const old = obj[prop];
    obj[prop] = function (...args) {
        const r = old?.apply(this, args);
        cb.apply(this, args);
        return r;
    };
}

function buildLoraLoaderUI(node) {
    const wrap = document.createElement("div");
    wrap.className = "cj-ll";

    // 从 optional widget 读取树形数据
    const w_tree = node.widgets?.find(w => w.name === "lora_tree_json");
    let loraTree = {};
    if (w_tree) {
        if (w_tree.value) {
            try { loraTree = JSON.parse(w_tree.value); } catch (e) {}
        }
        w_tree.hidden = true;
        w_tree.computeSize = () => [0, -4];
    }

    // 隐藏 strength_model widget
    const w_strength = node.widgets?.find(w => w.name === "strength_model");
    if (w_strength) {
        w_strength.hidden = true;
        w_strength.computeSize = () => [0, -4];
    }

    const dirs = Object.keys(loraTree);
    if (dirs.length === 0) {
        const hint = document.createElement("div");
        hint.style.cssText = "color:#888;padding:8px;font-size:11px;";
        hint.textContent = "未找到Lora文件夹";
        wrap.appendChild(hint);
        node.addDOMWidget("cj_ll_ui", "LoraLoaderUI", wrap, { getValue: () => "", setValue: () => {} });
        return;
    }

    // --- 文件夹 ---
    const dirRow = document.createElement("div");
    dirRow.className = "cj-ll-row";
    const dirLabel = document.createElement("span");
    dirLabel.className = "cj-ll-label";
    dirLabel.textContent = "文件夹:";
    const dirSelect = document.createElement("select");
    dirSelect.className = "cj-ll-select";
    for (const d of dirs) {
        const o = document.createElement("option");
        o.value = d; o.textContent = d;
        dirSelect.appendChild(o);
    }
    dirRow.append(dirLabel, dirSelect);
    wrap.appendChild(dirRow);

    // --- 文件名 + 强度 ---
    const fileRow = document.createElement("div");
    fileRow.className = "cj-ll-row";
    const fileLabel = document.createElement("span");
    fileLabel.className = "cj-ll-label";
    fileLabel.textContent = "文件名:";
    const fileSelect = document.createElement("select");
    fileSelect.className = "cj-ll-select";
    const strengthLabel = document.createElement("span");
    strengthLabel.className = "cj-ll-label";
    strengthLabel.textContent = "强度:";
    strengthLabel.style.width = "36px";
    const strengthInput = document.createElement("input");
    strengthInput.className = "cj-ll-strength";
    strengthInput.type = "number";
    strengthInput.min = "0"; strengthInput.max = "2"; strengthInput.step = "0.01";
    strengthInput.value = String(w_strength?.value ?? 1.0);
    strengthInput.title = "Lora强度";
    fileRow.append(fileLabel, fileSelect, strengthLabel, strengthInput);
    wrap.appendChild(fileRow);

    // 填充文件列表
    function fillFiles(dir) {
        fileSelect.innerHTML = "";
        const files = loraTree[dir] || [];
        for (const f of files) {
            const o = document.createElement("option");
            o.value = f; o.textContent = f;
            fileSelect.appendChild(o);
        }
    }

    // 同步选中值到 node 对象 + strength widget
    function sync() {
        node._selected_dir = dirSelect.value;
        node._selected_name = fileSelect.value;
        if (w_strength) w_strength.value = parseFloat(strengthInput.value) || 1.0;
    }

    // 初始化（默认选中 ".." 根目录）
    const defaultDir = (node._selected_dir && dirs.includes(node._selected_dir)) ? node._selected_dir : "..";
    dirSelect.value = defaultDir;
    fillFiles(dirSelect.value);
    if (node._selected_name) {
        const fileOpts = [...fileSelect.options].map(o => o.value);
        if (fileOpts.includes(node._selected_name)) fileSelect.value = node._selected_name;
    }
    sync();

    // 事件
    dirSelect.addEventListener("change", () => { fillFiles(dirSelect.value); sync(); });
    fileSelect.addEventListener("change", () => sync());
    strengthInput.addEventListener("input", () => sync());

    node.addDOMWidget("cj_ll_ui", "LoraLoaderUI", wrap, {
        getValue: () => JSON.stringify({ lora_dir: dirSelect.value, lora_name: fileSelect.value, strength_model: parseFloat(strengthInput.value) || 1.0 }),
        setValue: (v) => {
            try {
                const d = JSON.parse(v);
                if (d.lora_dir) { dirSelect.value = d.lora_dir; fillFiles(d.lora_dir); }
                if (d.lora_name) fileSelect.value = d.lora_name;
                if (d.strength_model != null) strengthInput.value = d.strength_model;
            } catch (e) {}
        }
    });
}

app.registerExtension({
    name: "CJNodes.LoraLoaderWithTrigger",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LoraLoaderWithTrigger") return;
        injectStyles();
        chainCallback(nodeType.prototype, "onNodeCreated", function () {
            buildLoraLoaderUI(this);
            this.setSize([Math.max(380, this.size[0]), Math.max(100, this.size[1])]);
        });
    }
});

console.log("CJ-Nodes LoraLoaderWithTrigger UI loaded");
