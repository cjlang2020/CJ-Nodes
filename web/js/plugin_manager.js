import { app } from "../../../../scripts/app.js";
import "./cj_menu_style.js";

// 插件管理：网格列出 custom_nodes 下的插件（不含 CJ-Nodes 自身）。
// 点卡片直接切换启用/关闭 —— 实现方式是给目录（或 .py 文件）加/去 .disabled 后缀。
const LIST_API = "/CJ-Nodes/api/plugins";
const SET_API = "/CJ-Nodes/api/plugins/set-enabled";
const RELOAD_API = "/CJ-Nodes/api/plugins/reload";

const COLOR_ON = "#3fb950";
const COLOR_OFF = "#8b949e";

const state = { plugins: [], busy: false, busyId: null, dirty: false };

async function refreshNodeDefinitions() {
    const em = app.extensionManager;
    const svc = em?.command || em?.commandService || em?.commands;
    if (svc && typeof svc.execute === "function") {
        try {
            await svc.execute("Comfy.RefreshNodeDefinitions");
            return true;
        } catch (e) {
            console.warn("[CJ-Nodes] 执行 RefreshNodeDefinitions 失败:", e);
        }
    }
    if (typeof app.refreshComboInNodes === "function") {
        try {
            await app.refreshComboInNodes();
            return true;
        } catch (e) {
            console.warn("[CJ-Nodes] refreshComboInNodes 失败:", e);
        }
    }
    return false;
}

async function apiLoad() {
    const res = await fetch(LIST_API);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "读取插件列表失败");
    state.plugins = data.plugins.slice().sort((a, b) => a.name.localeCompare(b.name));
}

async function apiSetEnabled(plugin, enabled) {
    const res = await fetch(SET_API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: plugin.id, enabled }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "操作失败");
    return data;
}

async function apiReload() {
    const res = await fetch(RELOAD_API, { method: "POST" });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "重新加载失败");
    return data;
}

function el(tag, style, text) {
    const node = document.createElement(tag);
    if (style) Object.assign(node.style, style);
    if (text !== undefined) node.textContent = text;
    return node;
}

function buildDialog() {
    const mask = el("div", {
        position: "fixed", inset: "0", zIndex: "10000", display: "flex",
        alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.55)",
        backdropFilter: "blur(2px)",
    });
    const box = el("div", {
        width: "min(1040px, 94vw)", height: "min(700px, 88vh)", display: "flex", flexDirection: "column",
        background: "var(--comfy-menu-bg, #1e1e1e)", color: "var(--fg-color, #ddd)",
        border: "1px solid var(--border-color, #444)", borderRadius: "14px", overflow: "hidden",
        boxShadow: "0 18px 50px rgba(0,0,0,0.55)", fontSize: "13px",
    });

    // ---- 头部 ----
    const head = el("div", {
        display: "flex", alignItems: "center", gap: "12px", padding: "14px 18px",
        borderBottom: "1px solid var(--border-color, #3a3a3a)", flex: "0 0 auto",
        background: "linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0))",
    });
    head.append(el("div", { fontSize: "16px", fontWeight: "600", letterSpacing: "0.5px" }, "插件管理"));
    const counts = el("div", { display: "flex", alignItems: "center", gap: "10px", fontSize: "12px", opacity: "0.85" });
    head.append(counts);
    head.append(el("div", { flex: "1 1 auto" }));

    const btnStyle = {
        padding: "7px 14px", cursor: "pointer", borderRadius: "8px", fontSize: "13px",
        border: "1px solid var(--border-color, #4a4a4a)", background: "rgba(255,255,255,0.06)",
        color: "inherit", transition: "background .15s, border-color .15s",
    };
    const reloadBtn = el("button", btnStyle, "重新加载插件");
    const closeBtn = el("button", btnStyle, "关闭窗口");
    head.append(reloadBtn, closeBtn);

    // ---- 网格 ----
    const grid = el("div", {
        flex: "1 1 auto", minHeight: "0", overflowY: "auto", padding: "16px 18px",
        display: "grid", gap: "10px", gridTemplateColumns: "repeat(auto-fill, minmax(228px, 1fr))",
        alignContent: "start",
    });

    // ---- 底部提示 / 状态 ----
    const foot = el("div", {
        display: "flex", alignItems: "center", gap: "10px", padding: "12px 18px",
        borderTop: "1px solid var(--border-color, #3a3a3a)", flex: "0 0 auto", fontSize: "12px",
    });
    const status = el("div", { flex: "1 1 auto", minHeight: "18px", lineHeight: "1.5", opacity: "0.9" });
    foot.append(status);
    const hint = el("div", { padding: "0 18px 12px", fontSize: "12px", lineHeight: "1.6", opacity: "0.5" },
        "点卡片即可关闭/启用（改文件夹名的 .disabled 后缀）。改完点「重新加载插件」在当前会话生效；" +
        "带自定义 HTTP 路由或后台线程的插件可能仍需重启 ComfyUI。");
    box.append(head, grid, hint, foot);
    mask.append(box);

    function setStatus(text, color) {
        status.textContent = text || "";
        status.style.color = color || "inherit";
    }

    function setBusy(busy, text, color) {
        state.busy = busy;
        reloadBtn.disabled = busy;
        reloadBtn.style.opacity = busy ? "0.5" : "1";
        reloadBtn.style.cursor = busy ? "default" : "pointer";
        if (text) setStatus(text, color);
    }

    function render() {
        const on = state.plugins.filter(p => p.enabled).length;
        counts.replaceChildren(
            el("span", { opacity: "0.7" }, `共 ${state.plugins.length} 个`),
            el("span", { color: COLOR_ON, fontWeight: "600" }, `启用 ${on}`),
            el("span", { color: COLOR_OFF, fontWeight: "600" }, `已关闭 ${state.plugins.length - on}`),
        );
        const scrollTop = grid.scrollTop;
        grid.replaceChildren();
        for (const plugin of state.plugins) {
            const busy = state.busyId === plugin.id;
            const card = el("div", {
                position: "relative", padding: "12px 14px", borderRadius: "10px", cursor: "pointer",
                border: `1px solid ${plugin.enabled ? "rgba(63,185,80,0.35)" : "rgba(255,255,255,0.09)"}`,
                background: plugin.enabled ? "rgba(63,185,80,0.08)" : "rgba(255,255,255,0.025)",
                opacity: busy ? "0.6" : "1",
                transition: "transform .12s, box-shadow .12s, border-color .12s, background .12s",
            });
            const row = el("div", { display: "flex", alignItems: "center", gap: "8px", minWidth: "0" });
            row.append(el("span", {
                flex: "0 0 auto", width: "8px", height: "8px", borderRadius: "50%",
                background: plugin.enabled ? COLOR_ON : COLOR_OFF,
                boxShadow: plugin.enabled ? "0 0 6px rgba(63,185,80,0.8)" : "none",
            }));
            const nameEl = el("div", {
                fontWeight: "600", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                opacity: plugin.enabled ? "1" : "0.6",
            }, plugin.name);
            nameEl.title = plugin.name;
            row.append(nameEl);
            card.append(row);

            const meta = el("div", { display: "flex", alignItems: "center", gap: "8px", marginTop: "7px", fontSize: "12px" });
            meta.append(el("span", { color: plugin.enabled ? COLOR_ON : COLOR_OFF, fontWeight: "500" },
                plugin.enabled ? "已启用" : "已关闭"));
            if (plugin.enabled && plugin.node_count) {
                meta.append(el("span", {
                    padding: "1px 7px", borderRadius: "999px", fontSize: "11px",
                    background: "rgba(255,255,255,0.08)", color: "#c9d1d9",
                }, `${plugin.node_count} 节点`));
            }
            if (!plugin.is_dir) meta.append(el("span", { opacity: "0.55", fontSize: "11px" }, "单文件"));
            card.append(meta);

            card.title = `点击${plugin.enabled ? "关闭" : "启用"} ${plugin.name}`;
            card.onmouseenter = () => {
                if (state.busy) return;
                card.style.transform = "translateY(-1px)";
                card.style.borderColor = plugin.enabled ? "rgba(63,185,80,0.7)" : "rgba(255,255,255,0.25)";
                card.style.boxShadow = "0 6px 16px rgba(0,0,0,0.35)";
            };
            card.onmouseleave = () => {
                card.style.transform = "";
                card.style.borderColor = plugin.enabled ? "rgba(63,185,80,0.35)" : "rgba(255,255,255,0.09)";
                card.style.boxShadow = "";
            };
            card.onclick = () => toggle(plugin);
            grid.append(card);
        }
        grid.scrollTop = scrollTop;
    }

    async function load() {
        try {
            await apiLoad();
        } catch (e) {
            setStatus("读取插件列表失败：" + e.message, "#f85149");
        }
        render();
    }

    async function toggle(plugin) {
        if (state.busy) return;
        const enabled = !plugin.enabled;
        state.busyId = plugin.id;
        setBusy(true, `正在${enabled ? "启用" : "关闭"} ${plugin.name}…`);
        render();
        try {
            const result = await apiSetEnabled(plugin, enabled);
            state.dirty = true;
            state.busyId = null;
            await apiLoad();
            render();
            setStatus(`已${enabled ? "启用" : "关闭"} ${plugin.name} —— 点「重新加载插件」后生效`,
                enabled ? COLOR_ON : COLOR_OFF);
        } catch (e) {
            state.busyId = null;
            render();
            setStatus(`${enabled ? "启用" : "关闭"}失败：` + e.message, "#f85149");
        }
        setBusy(false);
    }

    async function reload() {
        if (!confirm("重新加载 custom_nodes 下的所有插件？\n（跳过 CJ-Nodes 自身与已关闭的插件）")) return;
        setBusy(true, "正在重新加载所有插件，请稍候…");
        try {
            const data = await apiReload();
            state.dirty = false;
            setBusy(true, "正在刷新节点定义…");
            const refreshed = await refreshNodeDefinitions();
            const extra = refreshed ? "节点定义已刷新。" : "节点定义未能自动刷新，请按 F5。";
            setStatus(`重新加载完成：成功 ${data.loaded.length} 个，失败 ${data.failed.length} 个，跳过 ${data.skipped.length} 个。${extra}`,
                data.failed.length ? "#f85149" : COLOR_ON);
            if (data.failed.length) alert(`以下插件加载失败：\n${data.failed.join("\n")}`);
            await apiLoad();
            render();
        } catch (e) {
            setStatus("重新加载失败：" + e.message, "#f85149");
        }
        setBusy(false);
    }

    function closeDialog() {
        window.removeEventListener("keydown", onKey, true);
        mask.remove();
        if (state.dirty) {
            state.dirty = false;
            alert("有插件状态改动尚未通过「重新加载插件」生效；页面刷新（F5）后也会按新状态加载。");
        }
    }
    const onKey = (e) => {
        if (e.key === "Escape") closeDialog();
    };
    reloadBtn.onclick = reload;
    closeBtn.onclick = closeDialog;
    mask.onclick = (e) => {
        if (e.target === mask) closeDialog();
    };
    window.addEventListener("keydown", onKey, true);
    // 别让画布吃到面板内的鼠标/滚轮事件
    for (const type of ["pointerdown", "pointerup", "wheel", "contextmenu"]) {
        box.addEventListener(type, (e) => e.stopPropagation());
    }
    document.body.append(mask);
    load();
}

app.registerExtension({
    name: "CJ-Nodes.PluginManager",
    setup() {
        const { ComfyButton } = window.comfyAPI.button;
        app.menu?.settingsGroup.append(
            new ComfyButton({
                icon: "puzzle",
                tooltip: "列出 custom_nodes 下的插件，点卡片即可关闭/启用（改文件夹名的 .disabled 后缀）并整体重新加载",
                content: "插件管理",
                classList: "comfyui-button cj-menu-btn",
                action: () => buildDialog(),
            })
        );
    },
});
