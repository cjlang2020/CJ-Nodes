// 画布数据落盘：把 iframe 传来的 PNG base64 上传到服务器，widget 里只保存文件名引用。
// 与核心 LoadImage / Painter 同一模式——工作流与草稿不再内嵌图片数据（否则会撑爆
// 前端 localStorage 草稿配额，表现为“保存工作流草稿失败”）。
import { api } from "../../../../scripts/api.js";

export const CANVAS_SUBFOLDER = "cj_canvas";
const UPLOAD_DELAY = 400;

function dataUrlToBlob(dataUrl) {
    const comma = dataUrl.indexOf(",");
    const semi = dataUrl.indexOf(";");
    const mime = semi === -1 || semi > comma ? "image/png" : dataUrl.slice(5, semi);
    const bin = atob(dataUrl.slice(comma + 1));
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new Blob([bytes], { type: mime });
}

function randomToken() {
    return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function parse(raw) {
    if (!raw || raw === "empty") return {};
    try {
        return JSON.parse(raw) || {};
    } catch (e) {
        return {};
    }
}

async function upload(dataUrl, token, suffix) {
    const form = new FormData();
    form.append("image", dataUrlToBlob(dataUrl), `cj_canvas_${token}${suffix}.png`);
    form.append("type", "input");
    form.append("subfolder", CANVAS_SUBFOLDER);
    form.append("overwrite", "true");
    const resp = await api.fetchApi("/upload/image", { method: "POST", body: form });
    if (!resp.ok) throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
    const info = await resp.json();
    return info.subfolder ? `${info.subfolder}/${info.name}` : info.name;
}

// imageKeys: [{fileKey, b64Key, suffix}]，例如 {fileKey: "final_image", b64Key: "final_image_base64", suffix: ""}
export function createCanvasStore(node, widget, imageKeys) {
    let pending = null;
    let chain = Promise.resolve();

    async function flush() {
        if (!pending) return widget.value;
        const incoming = pending;
        pending = null;
        // 以已存 payload 为底，未重新上传的引用（如设计节点的原图）自然保留
        const out = { ...parse(widget.value), ...incoming };
        const token = out.token || (out.token = randomToken());
        for (const { fileKey, b64Key, suffix } of imageKeys) {
            if (incoming[b64Key]) {
                out[fileKey] = await upload(incoming[b64Key], token, suffix);
                out.updated = Date.now();
            }
            if (out[fileKey]) delete out[b64Key];
        }
        widget.value = JSON.stringify(out);
        node.drawData = widget.value;
        return widget.value;
    }

    function run() {
        clearTimeout(node._cjUploadTimer);
        chain = chain.then(flush).catch((e) => {
            // 上传失败时退回内嵌 base64：旧后端与后端解析都能跑，只是工作流会变大
            console.warn("[CJ-Nodes] 画布上传失败，回退为内嵌 base64：", e);
            if (pending) {
                widget.value = JSON.stringify(pending);
                node.drawData = widget.value;
                pending = null;
            }
        });
        return chain;
    }

    // 前端构建 prompt（graphToPrompt）会 await serializeValue，排队前把最新画布落盘，
    // 避免执行时用到上一版文件；工作流保存走同步 widget.value，所以它必须始终是文件名引用
    widget.serializeValue = async () => {
        await run();
        return widget.value;
    };

    return {
        push(jsonStr) {
            pending = parse(jsonStr);
            // 同步把尺寸等非图片字段写回，且绝不把 base64 落进 widget：
            // 草稿/工作流保存走同步 widget.value，哪怕短暂出现 base64 也会重新撞上限额
            const out = { ...parse(widget.value), ...pending };
            for (const { b64Key } of imageKeys) delete out[b64Key];
            widget.value = JSON.stringify(out);
            node.drawData = widget.value;
            clearTimeout(node._cjUploadTimer);
            node._cjUploadTimer = setTimeout(run, UPLOAD_DELAY);
        },
        flush: run,
        imageUrl(fileKey, b64Key) {
            const data = parse(widget.value);
            const ref = data[fileKey];
            if (!ref) {
                // 旧工作流：payload 里还是内嵌 base64，直接用 data URL 回填画布
                return data[b64Key] || "";
            }
            const slash = ref.lastIndexOf("/");
            const name = slash === -1 ? ref : ref.slice(slash + 1);
            const subfolder = slash === -1 ? CANVAS_SUBFOLDER : ref.slice(0, slash);
            const query = new URLSearchParams({
                filename: name,
                subfolder,
                type: "input",
                t: String(data.updated || 0),
            });
            return api.apiURL(`/view?${query.toString()}`);
        },
    };
}
