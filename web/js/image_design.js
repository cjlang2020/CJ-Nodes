import { app } from "../../../../scripts/app.js";

// 注册ComfyUI扩展
app.registerExtension({
    name: "luy.imagedesign",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ImageDesign") {
            console.log("✅ 初始化图片设计节点扩展");

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

                // 加载设计界面
                try {
                    iframe.src = "/CJ-Nodes/image_design.html";
                } catch (e) {
                    console.error("❌ 创建设计面板失败:", e);
                    alert("图片设计节点初始化失败: " + e.message);
                }

                // 添加DOM Widget
                const canvasWidget = this.addDOMWidget(
                    "design_canvas",
                    "图片设计面板",
                    iframe,
                    {
                        getValue: () => node.drawData || "empty",
                        setValue: (v) => {
                            node.drawData = v;
                            if (drawDataWidget) drawDataWidget.value = v;
                        }
                    }
                );

                // 设置面板尺寸
                canvasWidget.computeSize = function(width) {
                    const w = width || 400;
                    return [w, 800];
                };
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
                            const w = this.widthWidget?.value || 512;
                            const h = this.heightWidget?.value || 512;
                            iframe.contentWindow.postMessage({type: 'INIT_CANVAS', width: w, height: h}, '*');
                            setTimeout(() => this.initResizeObserver(), 1000);
                            break;
                        case 'DRAW_DATA_UPDATE':
                            this.drawData = data.data;
                            if (drawDataWidget) drawDataWidget.value = this.drawData;
                            canvasWidget.value = this.drawData;
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
                console.log("✅ 图片设计节点执行完成，已输出设计后的图片张量");
            };
        }
    }
});

console.log("✅ 图片设计节点扩展加载完成（luy分类）");