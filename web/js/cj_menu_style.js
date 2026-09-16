// CJ-Nodes 顶栏按钮统一样式。
// 原来靠 .cj-menu-btn 画成红/绿色块（local_resources.js 里注入），和 ComfyUI 原生工具条
// 按钮（运行、活动任务等）放一起很突兀。这里改成跟随主题的中性按钮：
// 同一套圆角/高度/字号，图标用主色点缀，悬停时描边高亮。
const STYLE_ID = "cj-menu-style";

const CSS = `
.comfyui-button.cj-menu-btn,
.comfyui-button.cj-menu-btn-green {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    height: 28px !important;
    padding: 0 10px !important;
    border-radius: 6px !important;
    background: var(--p-content-background, var(--comfy-input-bg, #27272a)) !important;
    color: var(--p-text-color, var(--fg-color, #e5e5e5)) !important;
    border: 1px solid var(--p-content-border-color, var(--border-color, #3f3f46)) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    line-height: 1 !important;
    box-shadow: none !important;
    transition: background-color .15s ease, border-color .15s ease, color .15s ease !important;
}
.comfyui-button.cj-menu-btn:hover,
.comfyui-button.cj-menu-btn-green:hover {
    background: var(--p-content-hover-background, rgba(255, 255, 255, .08)) !important;
    border-color: var(--p-primary-color, #60a5fa) !important;
}
.comfyui-button.cj-menu-btn:active,
.comfyui-button.cj-menu-btn-green:active {
    transform: translateY(1px) !important;
}
.comfyui-button.cj-menu-btn .mdi {
    color: var(--p-primary-color, #60a5fa) !important;
    font-size: 15px !important;
}
.comfyui-button.cj-menu-btn-green .mdi {
    color: var(--p-green-400, #4ade80) !important;
    font-size: 15px !important;
}
`;

export function installCjMenuStyle() {
    const old = document.getElementById(STYLE_ID);
    if (old) old.remove();
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = CSS;
    document.head.appendChild(style);
}

installCjMenuStyle();
