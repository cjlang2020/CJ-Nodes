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

    // 预览容器比例适配（保持1:1显示，内部图片按原始比例缩放）
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

// 更新预览图（严格保持原始宽高比）
function updatePreview(node, base64, width, height) {
    if (!node._base64Preview) {
        node._base64Preview = createPreviewWidget(node);
    }

    const { container, canvas, ctx } = node._base64Preview;

    if (!base64 || base64.trim() === "") {
        container.style.display = "none";
        return;
    }

    const src = base64.trim();
    if (!src.startsWith("data:")) {
        container.style.display = "none";
        return;
    }

    const img = new Image();
    img.onload = () => {
        try {
            // 使用图片原始宽高或保存的尺寸（确保比例一致）
            const imgWidth = width || img.width;
            const imgHeight = height || img.height;
            const imgRatio = imgWidth / imgHeight;

            // 预览容器尺寸
            const containerWidth = canvas.parentElement.clientWidth;
            const containerHeight = canvas.parentElement.clientHeight;
            const containerRatio = containerWidth / containerHeight;

            // 计算适配尺寸（保持原始比例）
            let drawWidth, drawHeight;
            if (imgRatio > containerRatio) {
                drawWidth = containerWidth;
                drawHeight = containerWidth / imgRatio;
            } else {
                drawHeight = containerHeight;
                drawWidth = containerHeight * imgRatio;
            }

            // 设置预览画布尺寸
            canvas.width = drawWidth;
            canvas.height = drawHeight;

// 填充白色背景并绘制图片
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, drawWidth, drawHeight);

            container.style.display = "block";
        } catch (e) {
            container.style.display = "none";
            console.error("预览图渲染失败:", e);
        }
    };
    img.onerror = () => {
        container.style.display = "none";
        console.error("预览图加载失败，无效的base64数据");
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
                width: "95vw",
                height: "95vh",
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
        // 存储完整的尺寸信息（保持原始宽高比）
        this.nodeImageData = {
            width: null,
            height: null,
            ratio: null
        };

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
                        // 保存完整的base64数据和尺寸信息
                        textWidget.element.value = event.data.data;
                        textWidget.element.dispatchEvent(new Event("change"));

                        // 同步原始宽高和比例（不做任何修改）
                        this.nodeImageData = {
                            width: event.data.width,
                            height: event.data.height,
                            ratio: event.data.ratio
                        };

                        // 更新预览图（传递原始尺寸确保比例一致）
                        updatePreview(targetNode, event.data.data, event.data.width, event.data.height);
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

    async show() {
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
                    await this.waitIframeReady();
                } catch (e) {
                    alert("加载编辑器超时，请检查扩展路径是否正确");
                    console.error("iframe加载失败:", e);
                    return;
                }
            }
            this.element.style.display = "block";
            // 传递完整数据到绘图工具（包含保存的尺寸）
            this.setCanvasData(textWidget.element.value);
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

    // 传递base64数据和尺寸信息到绘图工具
    setCanvasData(base64String) {
        if (!this.iframeElement) {
            console.error("iframe元素未初始化，无法发送数据");
            return;
        }
        try {
            this.iframeElement.contentWindow.postMessage({
                modalId: 0,
                base64: base64String || "",
                width: this.nodeImageData.width, // 传递保存的原始宽度
                height: this.nodeImageData.height // 传递保存的原始高度
            }, "*");
        } catch (e) {
            console.error("发送数据到绘图工具失败:", e);
            this.iframeElement.contentWindow.postMessage({
                modalId: 0,
                base64: "",
                width: null,
                height: null
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
                            // 初始化尺寸数据（从节点获取或留空）
                            const textWidget = this.widgets.find(w => w.name === "base64_string");
                            if (textWidget && textWidget.value) {
                                // 保持之前保存的尺寸信息
                                dlg.nodeImageData = {
                                    width: dlg.nodeImageData.width || null,
                                    height: dlg.nodeImageData.height || null,
                                    ratio: dlg.nodeImageData.ratio || null
                                };
                            }
                            dlg.show();
                        } catch (e) {
                            console.error("打开配置对话框失败:", e);
                        }
                    },
                });
            });

            // 监听文本框变化，实时更新预览（保持宽高比）
            const originalOnWidgetChange = nodeType.prototype.onWidgetChange;
            nodeType.prototype.onWidgetChange = function (widget) {
                if (originalOnWidgetChange) {
                    originalOnWidgetChange.apply(this, arguments);
                }
                if (widget.name === "base64_string") {
                    // 获取保存的尺寸信息
                    const dlg = DrawDialog.getInstance();
                    updatePreview(
                        this,
                        widget.value,
                        dlg.nodeImageData.width,
                        dlg.nodeImageData.height
                    );
                }
            };

            // 节点创建时尝试渲染预览
            const originalOnCreated = nodeType.prototype.onCreated;
            nodeType.prototype.onCreated = function () {
                if (originalOnCreated) {
                    originalOnCreated.apply(this, arguments);
                }
                const textWidget = this.widgets.find(w => w.name === "base64_string");
                if (textWidget && textWidget.value) {
                    const dlg = DrawDialog.getInstance();
                    updatePreview(
                        this,
                        textWidget.value,
                        dlg.nodeImageData.width,
                        dlg.nodeImageData.height
                    );
                }
            };
        }
    }
});