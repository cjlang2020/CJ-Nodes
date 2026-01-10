import { app } from "../../scripts/app.js";
import { ComfyDialog, $el } from "../../scripts/ui.js";
import { ComfyApp } from "../../scripts/app.js";

function addMenuHandler(nodeType, cb) {
    const getOpts = nodeType.prototype.getExtraMenuOptions;
    nodeType.prototype.getExtraMenuOptions = function () {
        const r = getOpts ? getOpts.apply(this, arguments) : []; // 兼容无默认菜单的节点
        cb.apply(this, arguments);
        return r;
    };
};

class PromptSelectoDialog extends ComfyDialog {
    static timeout = 5000;
    static instance = null;

    static getInstance() {
        if (!PromptSelectoDialog.instance) {
            PromptSelectoDialog.instance = new PromptSelectoDialog();
        }
        return PromptSelectoDialog.instance;
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
        this.iframeElement = null; // 初始化iframe元素

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
                        textWidget.element.value = event.data.msg;
                        textWidget.element.dispatchEvent(new Event('change'));
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

    // 安全获取节点的文本输入控件
    getTextWidget(node) {
        if (!node || !node.widgets || !node.widgets.length) {
            console.warn("节点没有可用的控件");
            return null;
        }

        // 尝试多种方式查找文本控件
        return node.widgets.find(w => w.type === "text") ||  // 按类型查找
               node.widgets[0] ||                           //  fallback到第一个控件
               null;
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

            // 检查节点是否有文本控件
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
            src: "extensions/CJ-Nodes/index.html",
            style: {
                width: "100%",
                height: "100%",
                border: "none",
            },
        });
        const modalContent = this.element.querySelector(".comfy-modal-content");
        // 清空内容时增加安全检查
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
                if (event.source !== this.iframeElement.contentWindow) {
                    return;
                }
                if (event.data.ready) {
                    window.removeEventListener("message", receiveMessage);
                    clearTimeout(timeoutHandle);
                    resolve();
                }
            };

            const timeoutHandle = setTimeout(() => {
                window.removeEventListener("message", receiveMessage);
                reject(new Error("等待编辑器就绪超时"));
            }, PromptSelectoDialog.timeout);

            window.addEventListener("message", receiveMessage);
        });
    }

    setCanvasJSONString(jsonString) {
        if (!this.iframeElement) {
            console.error("iframe元素未初始化，无法发送数据");
            return;
        }

        try {
            // 安全解析JSON
            const poses = jsonString ? JSON.parse(jsonString) : [];
            this.iframeElement.contentWindow.postMessage({
                modalId: 0,
                poses: poses
            }, "*");
        } catch (e) {
            console.error("解析JSON失败:", e);
            // 发送空数据避免iframe出错
            this.iframeElement.contentWindow.postMessage({
                modalId: 0,
                poses: []
            }, "*");
        }
    }
};

app.registerExtension({
    name: "luy.prompt.selector",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "PromptSelectorNode") {
            addMenuHandler(nodeType, function (_, options) {
                options.unshift({
                    content: "配置提示词",
                    callback: () => {
                        try {
                            // 保存当前节点引用
                            ComfyApp.clipspace_return_node = this;
                            const dlg = PromptSelectoDialog.getInstance();
                            dlg.show();
                        } catch (e) {
                            console.error("打开配置对话框失败:", e);
                        }
                    },
                });
            });
        }
    }
});
