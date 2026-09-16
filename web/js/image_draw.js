import { app } from "../../../../scripts/app.js";
import { createCanvasStore } from "./canvas_upload.js";

// 画布页会被浏览器启发式缓存（旧缓存条目不会因服务端 no-cache 而重新校验），
// 带上“本次页面加载”的版本参数，保证刷新页面后一定拿到最新页面
const PANEL_VERSION = Date.now();

// 注册ComfyUI扩展
app.registerExtension({
    name: "luy.drawphoto",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "DrawPhotoNode") {
            console.log("✅ 初始化带应用裁剪按钮的图片编辑节点扩展");

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                // 初始化编辑数据
                this.drawData = "empty";
                this._drawCanvasReady = false;
                this._resizeObserver = null;

                // 隐藏edit_data参数
                const drawDataWidget = this.widgets.find(w => w.name === "edit_data");
                if (drawDataWidget) {
                    drawDataWidget.hidden = true;
                    drawDataWidget.value = this.drawData;
                }

                // 绑定画布尺寸参数
                this.widthWidget = this.widgets.find(w => w.name === "canvas_width");
                this.heightWidget = this.widgets.find(w => w.name === "canvas_height");

                // 监听画布尺寸变化
                const handleSizeChange = () => {
                    if (this._drawCanvasReady && this.drawIframe.contentWindow) {
                        const w = this.widthWidget?.value || 512;
                        const h = this.heightWidget?.value || 512;
                        this.drawIframe.contentWindow.postMessage({
                            type: 'INIT_CANVAS',
                            width: w,
                            height: h
                        }, '*');
                    }
                };

                if (this.widthWidget) {
                    const origWidthCallback = this.widthWidget.callback;
                    this.widthWidget.callback = function(value) {
                        handleSizeChange();
                        if (origWidthCallback) origWidthCallback.call(this, value);
                    };
                }

                if (this.heightWidget) {
                    const origHeightCallback = this.heightWidget.callback;
                    this.heightWidget.callback = function(value) {
                        handleSizeChange();
                        if (origHeightCallback) origHeightCallback.call(this, value);
                    };
                }

                // 创建iframe
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.borderRadius = "8px";
                iframe.style.backgroundColor = "#fff";
                iframe.style.pointerEvents = "auto";
                iframe.setAttribute("sandbox", "allow-scripts allow-same-origin");

                // 加载编辑界面
                try {
                    iframe.src = `/CJ-Nodes/image_draw.html?v=${PANEL_VERSION}`;
                } catch (e) {
                    console.error("❌ 创建编辑面板失败:", e);
                    alert("图片编辑节点初始化失败: " + e.message);
                }

                // 添加DOM Widget
                const canvasWidget = this.addDOMWidget(
                    "draw_canvas",
                    "图片编辑面板",
                    iframe,
                    {
                        getValue: () => node.drawData || "empty",
                        setValue: (v) => {
                            node.drawData = v;
                            if (drawDataWidget) drawDataWidget.value = v;
                        }
                    }
                );
                // 画布数据已由 edit_data 承载，这里不再重复序列化：
                // 否则工作流/草稿会存两份 PNG base64，撑爆 localStorage 草稿配额（表现为“保存工作流草稿失败”）
                canvasWidget.serialize = false;
                canvasWidget.options.serialize = false;

                // 画布 PNG 上传到服务器，edit_data 只保留文件名引用（见 canvas_upload.js）
                const canvasStore = createCanvasStore(node, drawDataWidget, [
                    { fileKey: "final_image", b64Key: "final_image_base64", suffix: "" },
                ]);

                // 加载工作流时 READY 与 widgets_values 应用的先后顺序不固定（READY 可能更早），
                // 所以两处都尝试下发；dataReady=父窗口确认节点数据已应用完，iframe 据此才允许回写
                this.sendInitCanvas = function(dataReady) {
                    if (!this._drawCanvasReady || !iframe.contentWindow) return;
                    iframe.contentWindow.postMessage({
                        type: 'INIT_CANVAS',
                        width: this.widthWidget?.value || 512,
                        height: this.heightWidget?.value || 512,
                        image_url: canvasStore.imageUrl("final_image", "final_image_base64"),
                        data_ready: !!dataReady,
                    }, '*');
                };
                const origOnConfigure = this.onConfigure;
                this.onConfigure = function() {
                    const r = origOnConfigure ? origOnConfigure.apply(this, arguments) : undefined;
                    this.sendInitCanvas(true);
                    return r;
                };

                // 高度跟随节点：不能给 DOM widget 写 computeSize（会退化成固定高度、拿不到弹性空间），
                // 只给最小高度，剩余高度由前端弹性分配（通用做法见 CJ-Nodes/AGENTS.md）
                iframe.style.setProperty("--comfy-widget-min-height", "420px");
                if (canvasWidget.element) canvasWidget.element.style.pointerEvents = "auto";
                this.drawIframe = iframe;

                // 初始化ResizeObserver
                this.initResizeObserver = function() {
                    if (this._resizeObserver) this._resizeObserver.disconnect();
                    const observeTarget = canvasWidget.element || this.element || iframe;
                    if (observeTarget && window.ResizeObserver) {
                        this._resizeObserver = new ResizeObserver(() => {
                            if (this._drawCanvasReady && this.drawIframe.contentWindow) {
                                this.drawIframe.contentWindow.postMessage({type: 'RESIZE_CANVAS'}, '*');
                            }
                        });
                        this._resizeObserver.observe(observeTarget);
                    }
                };

                // 监听前端消息
                const handleMessage = (e) => {
                    if (e.source !== iframe.contentWindow) return;
                    const data = e.data;
                    switch(data.type) {
                        case 'DRAW_CANVAS_READY':
                            this._drawCanvasReady = true;
                            this.sendInitCanvas(false);
                            // 兜底：新建节点没有 widgets_values 可应用、不会触发 onConfigure，
                            // 超时后放行回写，避免画布一直无法上传
                            setTimeout(() => this.sendInitCanvas(true), 500);
                            setTimeout(() => this.initResizeObserver(), 1000);
                            break;
                        case 'DRAW_DATA_UPDATE':
                            this.drawData = data.data;
                            canvasStore.push(data.data);
                            this.flags = this.flags || {};
                            this.flags.dirty = true;
                            if (app && app.graph) app.graph.setDirtyCanvas(true, true);
                            break;
                        case 'UPDATE_CANVAS_SIZE':
                            if (this.widthWidget && data.width) {
                                this.widthWidget.value = Math.max(1, Math.min(4096, data.width));
                                // 不再调用 callback，避免循环触发
                            }
                            if (this.heightWidget && data.height) {
                                this.heightWidget.value = Math.max(1, Math.min(4096, data.height));
                                // 不再调用 callback，避免循环触发
                            }
                            break;
                    }
                };
                window.addEventListener('message', handleMessage);

                // 节点移除时清理资源
                const origOnRemoved = this.onRemoved;
                this.onRemoved = function() {
                    window.removeEventListener('message', handleMessage);
                    if (this._resizeObserver) this._resizeObserver.disconnect();
                    if (origOnRemoved) origOnRemoved.apply(this, arguments);
                };

                // 设置节点初始大小
                this.setSize([600, 850]);
                return r;
            };

            // 节点执行完成后的回调
            const origOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                if (origOnExecuted) origOnExecuted.apply(this, arguments);
                console.log("✅ 图片编辑节点执行完成，已输出编辑后的图片张量");
            };
        }
    }
});

console.log("✅ 带应用裁剪按钮的图片编辑节点扩展加载完成（luy分类）");