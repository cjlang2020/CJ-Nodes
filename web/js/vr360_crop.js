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

                this.croppedData = "";
                this.panoramaB64 = "";
                this._iframeReady = false;
                this._resizeObserver = null;

                const croppedWidget = this.widgets.find(w => w.name === "cropped_data");
                if (croppedWidget) {
                    croppedWidget.hidden = true;
                    croppedWidget.value = this.croppedData;
                }

                const panoWidget = this.widgets.find(w => w.name === "panorama_b64");
                if (panoWidget) {
                    panoWidget.hidden = true;
                    panoWidget.value = this.panoramaB64;
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
                        getValue: () => node.croppedData || "",
                        setValue: (v) => {
                            node.croppedData = v;
                            if (croppedWidget) croppedWidget.value = v;
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
                            if (node.panoramaB64) {
                                iframe.contentWindow.postMessage({
                                    type: 'SET_PANORAMA',
                                    data: node.panoramaB64,
                                }, '*');
                            }
                            setTimeout(() => this.initResizeObserver(), 500);
                            break;
                        case 'CROP_DATA_UPDATE':
                            node.croppedData = data.data || "";
                            if (croppedWidget) croppedWidget.value = node.croppedData;
                            canvasWidget.value = node.croppedData;
                            if (panoWidget && node.panoramaB64) {
                                panoWidget.value = node.panoramaB64;
                            }
                            node.flags = node.flags || {};
                            node.flags.dirty = true;
                            if (app && app.graph) app.graph.setDirtyCanvas(true, true);
                            break;
                        case 'PANORAMA_UPLOADED':
                            node.panoramaB64 = data.data || "";
                            if (panoWidget) panoWidget.value = node.panoramaB64;
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

            const origOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                if (origOnExecuted) origOnExecuted.apply(this, arguments);
                if (message) {
                    const panoB64 = message.panorama_b64 || (message.ui && message.ui.panorama_b64);
                    if (panoB64) {
                        this.panoramaB64 = panoB64;
                        if (this._iframeReady && this.iframe && this.iframe.contentWindow) {
                            this.iframe.contentWindow.postMessage({
                                type: 'SET_PANORAMA',
                                data: panoB64,
                            }, '*');
                        }
                    }
                }
            };
        }
    }
});

console.log("✅ 360全景裁剪节点扩展加载完成（luy分类）");
