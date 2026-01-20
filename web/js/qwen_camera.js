import { app } from "../../../../scripts/app.js";
import { VIEWER_HTML } from "./camera_viewer.js";

/**
 * ComfyUI Extension for Qwen Multiangle Lightning Node
 * Provides a 3D lighting control widget with color preview
 */

app.registerExtension({
    name: "qwen.multiangle.lightning",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "QwenMultiangleLightningNode") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                // Add custom drawing for color preview
                const origOnDrawForeground = this.onDrawForeground;
                this.onDrawForeground = function(ctx) {
                    if (origOnDrawForeground) {
                        origOnDrawForeground.apply(this, arguments);
                    }

                    // Find color widget and draw preview
                    const colorWidget = this.widgets?.find(w => w.name === "light_color_hex");
                    if (colorWidget && colorWidget.last_y !== undefined) {
                        const color = colorWidget.value || "#FFFFFF";
                        const x = this.size[0] - 35;
                        const y = colorWidget.last_y + 5;
                        const size = 20;

                        // Draw color preview box with border
                        ctx.save();
                        ctx.fillStyle = color;
                        ctx.strokeStyle = "#888";
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.roundRect(x, y, size, size, 4);
                        ctx.fill();
                        ctx.stroke();

                        // Draw inner highlight
                        ctx.strokeStyle = "rgba(255,255,255,0.3)";
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.roundRect(x + 2, y + 2, size - 4, size - 4, 2);
                        ctx.stroke();
                        ctx.restore();
                    }
                };

                // Create iframe for 3D viewer
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.backgroundColor = "#0a0a0f";
                iframe.style.borderRadius = "8px";
                iframe.style.display = "block";

                // Create blob URL from inline HTML
                const blob = new Blob([VIEWER_HTML], { type: 'text/html' });
                const blobUrl = URL.createObjectURL(blob);
                iframe.src = blobUrl;

                iframe.addEventListener('load', () => {
                    iframe._blobUrl = blobUrl;
                });

                // Add widget
                const widget = this.addDOMWidget("viewer", "LIGHTING_3D_VIEW", iframe, {
                    getValue() { return ""; },
                    setValue(v) { }
                });

                widget.computeSize = function (width) {
                    const w = width || 320;
                    return [w, 360];
                };

                widget.element = iframe;
                this._viewerIframe = iframe;
                this._viewerReady = false;

                // Message handler
                const onMessage = (event) => {
                    if (event.source !== iframe.contentWindow) return;
                    const data = event.data;

                    if (data.type === 'VIEWER_READY') {
                        this._viewerReady = true;
                        // Send pending image if any
                        if (this._pendingImageSend) {
                            this._pendingImageSend();
                            delete this._pendingImageSend;
                        }
                        // Send initial values
                        const hWidget = node.widgets.find(w => w.name === "light_azimuth");
                        const vWidget = node.widgets.find(w => w.name === "light_elevation");
                        const zWidget = node.widgets.find(w => w.name === "light_intensity");
                        const colorWidget = node.widgets.find(w => w.name === "light_color_hex");
                        const cinematicWidget = node.widgets.find(w => w.name === "cinematic_mode");

                        iframe.contentWindow.postMessage({
                            type: "INIT",
                            horizontal: hWidget?.value || 0,
                            vertical: vWidget?.value || 30,
                            zoom: zWidget?.value || 5.0,
                            lightColor: colorWidget?.value || "#FFFFFF",
                            useDefaultPrompts: cinematicWidget?.value || true,
                            cameraView: false
                        }, "*");
                    } else if (data.type === 'ANGLE_UPDATE') {
                        // Update node widgets from 3D view
                        const hWidget = node.widgets.find(w => w.name === "light_azimuth");
                        const vWidget = node.widgets.find(w => w.name === "light_elevation");
                        const zWidget = node.widgets.find(w => w.name === "light_intensity");

                        if (hWidget) hWidget.value = data.horizontal;
                        if (vWidget) vWidget.value = data.vertical;
                        if (zWidget) zWidget.value = data.zoom;

                        // Mark graph as changed
                        app.graph.setDirtyCanvas(true, true);
                    }
                };
                window.addEventListener('message', onMessage);

                // Resize handling
                const notifyIframeResize = () => {
                    if (iframe.contentWindow) {
                        const rect = iframe.getBoundingClientRect();
                        iframe.contentWindow.postMessage({
                            type: 'RESIZE',
                            width: rect.width,
                            height: rect.height
                        }, '*');
                    }
                };

                // ResizeObserver for responsive updates
                let resizeTimeout = null;
                let lastSize = { width: 0, height: 0 };
                const resizeObserver = new ResizeObserver((entries) => {
                    const entry = entries[0];
                    const newWidth = entry.contentRect.width;
                    const newHeight = entry.contentRect.height;

                    if (Math.abs(newWidth - lastSize.width) < 1 && Math.abs(newHeight - lastSize.height) < 1) {
                        return;
                    }
                    lastSize = { width: newWidth, height: newHeight };

                    if (resizeTimeout) {
                        clearTimeout(resizeTimeout);
                    }
                    resizeTimeout = setTimeout(() => {
                        notifyIframeResize();
                    }, 50);
                });
                resizeObserver.observe(iframe);

                // Sync slider widgets to 3D view
                const syncTo3DView = () => {
                    if (!this._viewerReady || !iframe.contentWindow) return;

                    const hWidget = node.widgets.find(w => w.name === "light_azimuth");
                    const vWidget = node.widgets.find(w => w.name === "light_elevation");
                    const zWidget = node.widgets.find(w => w.name === "light_intensity");
                    const colorWidget = node.widgets.find(w => w.name === "light_color_hex");
                    const cinematicWidget = node.widgets.find(w => w.name === "cinematic_mode");

                    iframe.contentWindow.postMessage({
                        type: "SYNC_ANGLES",
                        horizontal: hWidget?.value || 0,
                        vertical: vWidget?.value || 30,
                        zoom: zWidget?.value || 5.0,
                        lightColor: colorWidget?.value || "#FFFFFF",
                        useDefaultPrompts: cinematicWidget?.value || true,
                        cameraView: false
                    }, "*");
                };

                // Override widget callback to sync
                const origCallback = this.onWidgetChanged;
                this.onWidgetChanged = function (name, value, old_value, widget) {
                    if (origCallback) {
                        origCallback.apply(this, arguments);
                    }
                    if (name === "light_azimuth" || name === "light_elevation" || name === "light_intensity" || name === "light_color_hex" || name === "cinematic_mode") {
                        syncTo3DView();
                    }
                };

                // Handle execution - receive image from backend
                const onExecuted = this.onExecuted;
                this.onExecuted = function (message) {
                    onExecuted?.apply(this, arguments);

                    if (message?.image_base64 && message.image_base64[0]) {
                        const imageData = message.image_base64[0];

                        const sendImage = () => {
                            if (iframe.contentWindow) {
                                iframe.contentWindow.postMessage({
                                    type: "UPDATE_IMAGE",
                                    imageUrl: imageData
                                }, "*");
                            }
                        };

                        if (this._viewerReady) {
                            sendImage();
                        } else {
                            this._pendingImageSend = sendImage;
                        }
                    }
                };

                // Clean up on node removal
                const originalOnRemoved = this.onRemoved;
                this.onRemoved = function () {
                    resizeObserver.disconnect();
                    window.removeEventListener('message', onMessage);
                    if (resizeTimeout) {
                        clearTimeout(resizeTimeout);
                    }
                    delete this._pendingImageSend;
                    if (iframe._blobUrl) {
                        URL.revokeObjectURL(iframe._blobUrl);
                    }
                    if (originalOnRemoved) {
                        originalOnRemoved.apply(this, arguments);
                    }
                };

                // Set initial node size
                this.setSize([350, 520]);

                return r;
            };
        }
    }
});
