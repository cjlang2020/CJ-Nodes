import { app } from "../../../../scripts/app.js";

app.registerExtension({
    name: "luy.vr360crop",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "VR360Crop") {
            console.log("✅ 初始化360全景裁剪节点扩展");

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                this.cropData = "empty";
                this._iframeReady = false;
                this._resizeObserver = null;

                const cropDataWidget = this.widgets.find(w => w.name === "crop_data");
                if (cropDataWidget) {
                    cropDataWidget.hidden = true;
                    cropDataWidget.value = this.cropData;
                }

                this.widthWidget = this.widgets.find(w => w.name === "output_width");
                this.heightWidget = this.widgets.find(w => w.name === "output_height");

                const handleSizeChange = () => {
                    if (this._iframeReady && this.iframe && this.iframe.contentWindow) {
                        const w = this.widthWidget?.value || 1024;
                        const h = this.heightWidget?.value || 512;
                        this.iframe.contentWindow.postMessage({
                            type: 'SET_OUTPUT_SIZE',
                            width: w,
                            height: h
                        }, '*');
                    }
                };

                if (this.widthWidget) {
                    const origCb = this.widthWidget.callback;
                    this.widthWidget.callback = function(value) {
                        handleSizeChange();
                        if (origCb) origCb.call(this, value);
                    };
                }
                if (this.heightWidget) {
                    const origCb = this.heightWidget.callback;
                    this.heightWidget.callback = function(value) {
                        handleSizeChange();
                        if (origCb) origCb.call(this, value);
                    };
                }

                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.borderRadius = "8px";
                iframe.style.backgroundColor = "#111";
                iframe.style.pointerEvents = "auto";
                iframe.setAttribute("sandbox", "allow-scripts allow-same-origin");

                try {
                    iframe.src = "/CJ-Nodes/vr360_crop.html";
                } catch (e) {
                    console.error("❌ 创建VR360面板失败:", e);
                }

                const canvasWidget = this.addDOMWidget(
                    "vr360_canvas",
                    "360全景裁剪",
                    iframe,
                    {
                        getValue: () => node.cropData || "empty",
                        setValue: (v) => {
                            node.cropData = v;
                            if (cropDataWidget) cropDataWidget.value = v;
                        }
                    }
                );

                canvasWidget.computeSize = function(width) {
                    const w = width || 400;
                    return [w, 600];
                };
                if (canvasWidget.element) canvasWidget.element.style.pointerEvents = "auto";
                this.iframe = iframe;

                this.initResizeObserver = function() {
                    if (this._resizeObserver) this._resizeObserver.disconnect();
                    const target = canvasWidget.element || this.element || iframe;
                    if (target && window.ResizeObserver) {
                        this._resizeObserver = new ResizeObserver(() => {
                            if (this._iframeReady && this.iframe.contentWindow) {
                                this.iframe.contentWindow.postMessage({type: 'RESIZE_CANVAS'}, '*');
                            }
                        });
                        this._resizeObserver.observe(target);
                    }
                };

                const handleMessage = (e) => {
                    if (e.source !== iframe.contentWindow) return;
                    const data = e.data;
                    switch(data.type) {
                        case 'DRAW_CANVAS_READY':
                            this._iframeReady = true;
                            const w = this.widthWidget?.value || 1024;
                            const h = this.heightWidget?.value || 512;
                            iframe.contentWindow.postMessage({type: 'SET_OUTPUT_SIZE', width: w, height: h}, '*');
                            if (node.cropData && node.cropData !== "empty") {
                                iframe.contentWindow.postMessage({
                                    type: 'SET_CROP_DATA',
                                    data: node.cropData,
                                }, '*');
                            }
                            setTimeout(() => this.initResizeObserver(), 500);
                            break;
                        case 'CROP_DATA_UPDATE':
                            node.cropData = data.data;
                            if (cropDataWidget) cropDataWidget.value = node.cropData;
                            canvasWidget.value = node.cropData;
                            node.flags = node.flags || {};
                            node.flags.dirty = true;
                            if (app && app.graph) app.graph.setDirtyCanvas(true, true);
                            break;
                        case 'PANORAMA_UPLOADED':
                            break;
                        case 'LOG':
                            console.log("[VR360Crop]", data.data);
                            break;
                    }
                };
                window.addEventListener('message', handleMessage);

                const origOnRemoved = this.onRemoved;
                this.onRemoved = function() {
                    window.removeEventListener('message', handleMessage);
                    if (this._resizeObserver) this._resizeObserver.disconnect();
                    if (origOnRemoved) origOnRemoved.apply(this, arguments);
                };

                this.setSize([600, 650]);
                return r;
            };
        }
    }
});

console.log("✅ 360全景裁剪节点扩展加载完成（luy分类）");
