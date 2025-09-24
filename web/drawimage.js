import { app } from "../../scripts/app.js";
import { ComfyDialog, $el } from "../../scripts/ui.js";
import { ComfyApp } from "../../scripts/app.js";

function addMenuHandler(nodeType, cb) {
    const getOpts = nodeType.prototype.getExtraMenuOptions;
    nodeType.prototype.getExtraMenuOptions = function () {
        const r = getOpts ? getOpts.apply(this, arguments) : [];
        cb.apply(this, arguments);
        return r;
    };
}

// 创建预览容器
function createPreviewWidget(node) {
    const previewContainer = document.createElement("div");
    previewContainer.style.cssText = `
        width:100%;
        margin-top:8px;
        border:1px dashed #ccc;
        border-radius:4px;
        overflow:hidden;
        display:none;
        background:#f9f9f9;
        position:relative;
    `;

    // 使用 padding-bottom 实现正方形比例
    previewContainer.style.paddingBottom = "100%";

    const canvas = document.createElement("canvas");
    canvas.style.cssText = `
        position:absolute;
        top:0;
        left:0;
        width:100%;
        height:100%;
        object-fit:contain;
        display:block;
    `;

    previewContainer.appendChild(canvas);

    const widgetContainer = node.widgets?.[0]?.element?.parentElement;
    if (widgetContainer) {
        widgetContainer.appendChild(previewContainer);
    }

    return {
        container: previewContainer,
        canvas: canvas,
        ctx: canvas.getContext("2d")
    };
}

// 更新预览图
function updatePreview(node, base64) {
    if (!node._base64Preview) {
        node._base64Preview = createPreviewWidget(node);
    }

    const { container, canvas, ctx } = node._base64Preview;

    if (!base64 || base64.trim() === "") {
        container.style.display = "none";
        return;
    }

    let src = base64.trim();
    if (!src.startsWith("data:")) {
        // 如果没有 data URL 前缀，尝试添加
        if (src.includes(",")) {
            src = "data:image/png;base64," + src.split(",")[1];
        } else {
            src = "data:image/png;base64," + src;
        }
    }

    const img = new Image();
    img.onload = () => {
        try {
            const ratio = Math.min(1, canvas.parentElement.clientWidth / img.width || 1);
            canvas.width = img.width * ratio;
            canvas.height = img.height * ratio;

            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            container.style.display = "block";
        } catch (e) {
            container.style.display = "none";
        }
    };
    img.onerror = () => {
        container.style.display = "none";
    };
    img.crossOrigin = "anonymous";
    img.src = src;
}

class DrawDialog extends ComfyDialog {
    static timeout = 5000;
    static instance = null;

    static getInstance() {
        if (!DrawDialog.instance) {
            DrawDialog.instance = new DrawDialog();
        }
        return DrawDialog.instance;
    }

    constructor() {
        super();
        this.element = $el("div.comfy-modal", {
            parent: document.body,
            style: {
                width: "80vw",
                height: "80vh",
            },
        }, [
            $el("div.comfy-modal-content", {
                style: {
                    width: "100%",
                    height: "100%",
                    padding: "5px",
                    boxSizing: "border-box"
                },
            }),
        ]);
        this.is_layout_created = false;
        this.iframeElement = null;

        window.addEventListener("message", (event) => {
            if (event.source !== this.iframeElement?.contentWindow) {
                return;
            }
            const message = event.data;
            if (message.Id === 0) {
                try {
                    const targetNode = ComfyApp.clipspace_return_node;
                    const textWidget = this.getTextWidget(targetNode);
                    if (textWidget) {
                        textWidget.element.value = event.data.data;
                        textWidget.element.dispatchEvent(new Event("change"));

                        // 数据更新后直接渲染预览
                        updatePreview(targetNode, event.data.data);
                    } else {
                        console.warn("未找到文本输入控件，无法更新数据");
                    }
                    this.close();
                } catch (e) {
                    console.error("处理返回数据失败:", e);
                }
            }
        });
    }

    getTextWidget(node) {
        if (!node || !node.widgets || !node.widgets.length) {
            console.warn("节点没有可用的控件");
            return null;
        }
        return node.widgets.find(w => w.type === "text") || node.widgets[0] || null;
    }

    close() {
        super.close();
    }

    show() {
        try {
            const targetNode = ComfyApp.clipspace_return_node;
            if (!targetNode) {
                alert("未找到目标节点，请重试");
                return;
            }
            const textWidget = this.getTextWidget(targetNode);
            if (!textWidget) {
                alert("目标节点没有可用的文本输入控件");
                return;
            }
            if (!this.is_layout_created) {
                this.createLayout();
                this.is_layout_created = true;
                try {
                    this.waitIframeReady();
                } catch (e) {
                    alert("加载编辑器超时，请检查扩展路径是否正确");
                    console.error("iframe加载失败:", e);
                    return;
                }
            }
            this.element.style.display = "block";
            this.setCanvasJSONString(textWidget.element.value);
        } catch (e) {
            console.error("显示对话框失败:", e);
            alert("操作失败: " + e.message);
        }
    }

    createLayout() {
        this.iframeElement = $el("iframe", {
            src: "extensions/CJ-Nodes/drawimage.html",
            style: {
                width: "100%",
                height: "100%",
                border: "none",
            },
        });
        const modalContent = this.element.querySelector(".comfy-modal-content");
        while (modalContent?.firstChild) {
            modalContent.removeChild(modalContent.firstChild);
        }
        if (modalContent) {
            modalContent.appendChild(this.iframeElement);
        } else {
            console.error("未找到模态框内容容器");
        }
    }

    waitIframeReady() {
        return new Promise((resolve, reject) => {
            if (!this.iframeElement) {
                reject(new Error("iframe元素未初始化"));
                return;
            }
            const receiveMessage = (event) => {
                if (event.source !== this.iframeElement.contentWindow) return;
                if (event.data.ready) {
                    window.removeEventListener("message", receiveMessage);
                    clearTimeout(timeoutHandle);
                    resolve();
                }
            };
            const timeoutHandle = setTimeout(() => {
                window.removeEventListener("message", receiveMessage);
                reject(new Error("等待编辑器就绪超时"));
            }, DrawDialog.timeout);
            window.addEventListener("message", receiveMessage);
        });
    }

    setCanvasJSONString(jsonString) {
        if (!this.iframeElement) {
            console.error("iframe元素未初始化，无法发送数据");
            return;
        }
        try {
            const poses = jsonString ? JSON.parse(jsonString) : [];
            this.iframeElement.contentWindow.postMessage({
                modalId: 0,
                poses: poses
            }, "*");
        } catch (e) {
            console.error("解析JSON失败:", e);
            this.iframeElement.contentWindow.postMessage({
                modalId: 0,
                poses: []
            }, "*");
        }
    }
}

app.registerExtension({
    name: "luy.draw",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "ImageDrawNode") {
            addMenuHandler(nodeType, function (_, options) {
                options.unshift({
                    content: "开始涂鸦",
                    callback: () => {
                        try {
                            ComfyApp.clipspace_return_node = this;
                            const dlg = DrawDialog.getInstance();
                            dlg.show();
                        } catch (e) {
                            console.error("打开配置对话框失败:", e);
                        }
                    },
                });
            });

            // 监听文本框变化，实时更新预览
            const originalOnWidgetChange = nodeType.prototype.onWidgetChange;
            nodeType.prototype.onWidgetChange = function (widget) {
                if (originalOnWidgetChange) {
                    originalOnWidgetChange.apply(this, arguments);
                }
                if (widget.name === "base64_string") {
                    updatePreview(this, widget.value);
                }
            };

            // 节点创建时也尝试渲染预览
            const originalOnCreated = nodeType.prototype.onCreated;
            nodeType.prototype.onCreated = function () {
                if (originalOnCreated) {
                    originalOnCreated.apply(this, arguments);
                }
                const textWidget = this.widgets.find(w => w.name === "base64_string");
                if (textWidget && textWidget.value) {
                    updatePreview(this, textWidget.value);
                }
            };
        }
    }
});