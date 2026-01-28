import { app } from "../../../../scripts/app.js";

// 裁剪界面HTML模板（移除按钮，简化交互）
const CROP_HTML = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Image Crop Tool</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            width: 100%;
            height: 100vh;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 0 !important;
            margin: 0 !important;
        }
        #toolbar {
            padding: 10px;
            background: #242424;
            color: white;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            flex-shrink: 0;
        }
        #upload-btn {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
            background: #2ecc71;
            color: white;
        }
        #upload-btn:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        #canvas-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden !important;
            background: #ddd;
            padding: 10px;
            position: relative;
            width: 100%;
            height: calc(100% - 60px);
        }
        #crop-image {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            display: none;
            border: 2px solid #383838;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            touch-action: none;
            user-select: none;
            pointer-events: auto;
        }
        #crop-rect {
            position: absolute;
            border: 2px solid #3498db;
            background: rgba(52, 152, 219, 0.1);
            display: none;
            pointer-events: none;
        }
        #status {
            padding: 5px 10px;
            background: #2c3e50;
            color: #2ecc71;
            font-size: 12px;
            text-align: center;
            flex-shrink: 0;
        }
        #image-input {
            display: none;
        }
    </style>
</head>
<body>
    <div id="toolbar">
        <input type="file" id="image-input" accept="image/*">
        <button id="upload-btn">上传图片</button>
    </div>
    <div id="canvas-container">
        <img id="crop-image" alt="请上传图片">
        <div id="crop-rect"></div>
    </div>
    <div id="status">准备上传图片</div>

    <script>
        const state = {
            isDrawing: false,
            isUploaded: false,
            cropX1: 0,
            cropY1: 0,
            cropX2: 0,
            cropY2: 0,
            canvasWidth: 512,
            canvasHeight: 512,
            imageNaturalW: 0,
            imageNaturalH: 0,
            imageDisplayW: 0,
            imageDisplayH: 0,
            imageOffsetX: 0,
            imageOffsetY: 0,
            scale: 1,
            resizeObserver: null,
            imageBase64: ""
        };

        function initCanvas(width, height) {
            try {
                state.canvasWidth = width;
                state.canvasHeight = height;
                updateCanvasScale();
                console.log('Crop canvas initialized:', width + 'x' + height);
            } catch (e) {
                console.error('Crop canvas init failed:', e);
                document.getElementById('status').textContent = '初始化失败: ' + e.message;
            }
        }

        function updateCanvasScale() {
            const image = document.getElementById('crop-image');
            const container = document.getElementById('canvas-container');
            if (!state.isUploaded || !image) return;

            const containerStyles = window.getComputedStyle(container);
            const paddingLeft = parseFloat(containerStyles.paddingLeft) || 0;
            const paddingRight = parseFloat(containerStyles.paddingRight) || 0;
            const paddingTop = parseFloat(containerStyles.paddingTop) || 0;
            const paddingBottom = parseFloat(containerStyles.paddingBottom) || 0;

            const containerInnerWidth = container.clientWidth - paddingLeft - paddingRight;
            const containerInnerHeight = container.clientHeight - paddingTop - paddingBottom;

            const scaleX = containerInnerWidth / state.imageNaturalW;
            const scaleY = containerInnerHeight / state.imageNaturalH;
            state.scale = Math.min(scaleX, scaleY, 1);

            state.imageDisplayW = state.imageNaturalW * state.scale;
            state.imageDisplayH = state.imageNaturalH * state.scale;
            state.imageOffsetX = (containerInnerWidth - state.imageDisplayW) / 2 + paddingLeft;
            state.imageOffsetY = (containerInnerHeight - state.imageDisplayH) / 2 + paddingTop;

            image.style.width = state.imageDisplayW + 'px';
            image.style.height = state.imageDisplayH + 'px';
            image.style.position = 'absolute';
            image.style.left = state.imageOffsetX + 'px';
            image.style.top = state.imageOffsetY + 'px';
            image.style.margin = 0;
        }

        function getCanvasCoords(clientX, clientY) {
            const image = document.getElementById('crop-image');
            if (!image) return [0, 0];
            const rect = image.getBoundingClientRect();
            return [
                Math.max(0, Math.min(state.imageNaturalW, (clientX - rect.left) / state.scale)),
                Math.max(0, Math.min(state.imageNaturalH, (clientY - rect.top) / state.scale))
            ];
        }

        // 发送裁剪数据并更新画布尺寸
        function sendCropDataToParent() {
            // 计算裁剪区域的实际尺寸
            const cropWidth = Math.abs(state.cropX2 - state.cropX1);
            const cropHeight = Math.abs(state.cropY2 - state.cropY1);

            const cropData = {
                image_base64: state.imageBase64,
                crop_coords: [state.cropX1, state.cropY1, state.cropX2, state.cropY2],
                crop_width: cropWidth,
                crop_height: cropHeight
            };

            try {
                const jsonStr = JSON.stringify(cropData);
                // 发送裁剪数据
                window.parent.postMessage({
                    type: 'DRAW_DATA_UPDATE',
                    data: jsonStr
                }, '*');

                // 发送画布尺寸更新请求
                window.parent.postMessage({
                    type: 'UPDATE_CANVAS_SIZE',
                    width: cropWidth,
                    height: cropHeight
                }, '*');

                document.getElementById('status').textContent =
                    '裁剪完成: ' + cropWidth + 'x' + cropHeight;

            } catch (e) {
                console.error('发送裁剪数据失败:', e);
                document.getElementById('status').textContent = '裁剪失败: ' + e.message;
            }
        }

        function setupEventListeners() {
            // 上传图片
            document.getElementById('upload-btn').addEventListener('click', () => {
                document.getElementById('image-input').click();
            });

            // 处理图片上传
            document.getElementById('image-input').addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file || !file.type.startsWith('image/')) return;

                const reader = new FileReader();
                reader.onload = (ev) => {
                    state.imageBase64 = ev.target.result;
                    const image = document.getElementById('crop-image');
                    image.src = state.imageBase64;
                    image.onload = () => {
                        state.isUploaded = true;
                        state.imageNaturalW = image.naturalWidth;
                        state.imageNaturalH = image.naturalHeight;
                        image.style.display = 'block';
                        updateCanvasScale();

                        // 初始化裁剪坐标为整图
                        state.cropX1 = 0;
                        state.cropY1 = 0;
                        state.cropX2 = state.imageNaturalW;
                        state.cropY2 = state.imageNaturalH;

                        document.getElementById('status').textContent =
                            '图片已上传: ' + state.imageNaturalW + 'x' + state.imageNaturalH +
                            ' → 拖拽选择裁剪区域';
                    };
                };
                reader.readAsDataURL(file);
            });

            // 绘制裁剪矩形（核心：绘制完成后立即裁剪）
            const container = document.getElementById('canvas-container');
            let isMouseDown = false;

            container.addEventListener('mousedown', (e) => {
                if (!state.isUploaded) return;
                e.preventDefault();
                e.stopPropagation();
                isMouseDown = true;
                state.isDrawing = true;

                const [x, y] = getCanvasCoords(e.clientX, e.clientY);
                state.cropX1 = x;
                state.cropY1 = y;
                state.cropX2 = x;
                state.cropY2 = y;

                document.getElementById('crop-rect').style.display = 'block';
                updateCropRect();
                document.getElementById('status').textContent = '绘制裁剪区域中...';
            });

            document.addEventListener('mousemove', (e) => {
                if (!isMouseDown || !state.isDrawing || !state.isUploaded) return;

                const [x, y] = getCanvasCoords(e.clientX, e.clientY);
                state.cropX2 = x;
                state.cropY2 = y;
                updateCropRect();
            });

            // 鼠标松开后立即执行裁剪（核心改动）
            document.addEventListener('mouseup', () => {
                if (isMouseDown && state.isDrawing) {
                    isMouseDown = false;
                    state.isDrawing = false;

                    // 确保裁剪区域有效
                    if (Math.abs(state.cropX2 - state.cropX1) < 10 ||
                        Math.abs(state.cropY2 - state.cropY1) < 10) {
                        document.getElementById('status').textContent = '裁剪区域过小，请重新选择';
                        document.getElementById('crop-rect').style.display = 'none';
                        return;
                    }

                    // 立即执行裁剪逻辑
                    sendCropDataToParent();
                }
            });

            // ResizeObserver
            if (container && window.ResizeObserver) {
                state.resizeObserver = new ResizeObserver(entries => {
                    updateCanvasScale();
                    updateCropRect();
                });
                state.resizeObserver.observe(container);
            }

            window.addEventListener('resize', () => {
                updateCanvasScale();
                updateCropRect();
            });
        }

        function updateCropRect() {
            const rect = document.getElementById('crop-rect');
            if (!rect || !state.isUploaded) return;

            const x1 = state.cropX1 * state.scale + state.imageOffsetX;
            const y1 = state.cropY1 * state.scale + state.imageOffsetY;
            const x2 = state.cropX2 * state.scale + state.imageOffsetX;
            const y2 = state.cropY2 * state.scale + state.imageOffsetY;

            rect.style.left = Math.min(x1, x2) + 'px';
            rect.style.top = Math.min(y1, y2) + 'px';
            rect.style.width = Math.abs(x2 - x1) + 'px';
            rect.style.height = Math.abs(y2 - y1) + 'px';
        }

        // 监听父窗口消息
        window.addEventListener('message', (e) => {
            try {
                const data = e.data;
                if (data.type === 'INIT_CANVAS') {
                    initCanvas(data.width || 512, data.height || 512);
                    document.getElementById('status').textContent =
                        '画布初始化: ' + (data.width || 512) + 'x' + (data.height || 512);
                } else if (data.type === 'RESIZE_CANVAS') {
                    updateCanvasScale();
                    updateCropRect();
                }
            } catch (e) {
                console.error('处理父窗口消息失败:', e);
            }
        });

        setupEventListeners();
        initCanvas(512, 512);

        setTimeout(() => {
            window.parent.postMessage({type: 'DRAW_CANVAS_READY'}, '*');
        }, 100);

        window.addEventListener('unload', () => {
            if (state.resizeObserver) {
                state.resizeObserver.disconnect();
            }
        });
    </script>
</body>
</html>
`;

// 注册ComfyUI扩展（新增画布尺寸更新逻辑）
app.registerExtension({
    name: "luy.imageCrop",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ImageCropNode") {
            console.log("初始化自动裁剪图片节点扩展");

            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                // 初始化裁剪数据
                this.drawData = "empty";
                this._drawCanvasReady = false;
                this._resizeObserver = null;

                // 隐藏crop_data参数
                const drawDataWidget = this.widgets.find(w => w.name === "crop_data");
                if (drawDataWidget) {
                    drawDataWidget.hidden = true;
                    drawDataWidget.value = this.drawData;
                    console.log("✅ 已隐藏crop_data参数");
                }

                // 找到画布尺寸参数（用于自动更新）
                this.widthWidget = this.widgets.find(w => w.name === "canvas_width");
                this.heightWidget = this.widgets.find(w => w.name === "canvas_height");

                // 创建iframe
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.borderRadius = "8px";
                iframe.style.backgroundColor = "#ffffff";
                iframe.style.pointerEvents = "auto";
                iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-popups allow-modals");

                try {
                    const blob = new Blob([CROP_HTML], { type: 'text/html;charset=utf-8' });
                    const blobUrl = URL.createObjectURL(blob);
                    iframe.src = blobUrl;
                    iframe._blobUrl = blobUrl;
                } catch (e) {
                    console.error("创建iframe失败:", e);
                    alert("创建裁剪面板失败: " + e.message);
                }

                // 添加DOM Widget
                const canvasWidget = this.addDOMWidget(
                    "draw_canvas",
                    "裁剪画布",
                    iframe,
                    {
                        getValue: () => node.drawData || "empty",
                        setValue: (v) => {
                            node.drawData = v;
                            if (drawDataWidget) drawDataWidget.value = v;
                        }
                    }
                );

                canvasWidget.computeSize = function(width) {
                    const w = width || 400;
                    return [w, 800];
                };

                if (canvasWidget.element) {
                    canvasWidget.element.style.pointerEvents = "auto";
                }

                this.drawIframe = iframe;

                // ResizeObserver（参考代码逻辑）
                this.initResizeObserver = function() {
                    if (this._resizeObserver) {
                        try {
                            this._resizeObserver.disconnect();
                        } catch (e) {
                            console.warn("断开ResizeObserver失败:", e);
                        }
                    }

                    let observeTarget = null;
                    if (canvasWidget && canvasWidget.element) {
                        observeTarget = canvasWidget.element;
                    } else if (this.element && this.element instanceof Element) {
                        observeTarget = this.element;
                    } else if (iframe && iframe instanceof Element) {
                        observeTarget = iframe;
                    }

                    if (observeTarget && window.ResizeObserver) {
                        this._resizeObserver = new ResizeObserver(entries => {
                            if (this._drawCanvasReady && this.drawIframe && this.drawIframe.contentWindow) {
                                this.drawIframe.contentWindow.postMessage({
                                    type: 'RESIZE_CANVAS'
                                }, '*');
                            }
                        });

                        try {
                            this._resizeObserver.observe(observeTarget);
                        } catch (e) {
                            console.error("初始化ResizeObserver失败:", e);
                            this.startSizeCheckTimer();
                        }
                    } else {
                        console.warn("使用定时器降级方案");
                        this.startSizeCheckTimer();
                    }
                };

                this.startSizeCheckTimer = function() {
                    let lastWidth = 0;
                    let lastHeight = 0;

                    this._sizeCheckTimer = setInterval(() => {
                        if (!this._drawCanvasReady || !this.drawIframe) return;

                        let currentWidth = 0;
                        let currentHeight = 0;

                        if (canvasWidget && canvasWidget.element) {
                            const rect = canvasWidget.element.getBoundingClientRect();
                            currentWidth = rect.width;
                            currentHeight = rect.height;
                        }

                        if (currentWidth !== lastWidth || currentHeight !== lastHeight) {
                            lastWidth = currentWidth;
                            lastHeight = currentHeight;
                            this.drawIframe.contentWindow.postMessage({
                                type: 'RESIZE_CANVAS'
                            }, '*');
                        }
                    }, 1000);
                };

                // 消息处理（核心：新增画布尺寸更新）
                const handleMessage = (e) => {
                    if (e.source !== iframe.contentWindow) return;

                    const data = e.data;
                    console.log("收到裁剪面板消息:", data.type);

                    if (data.type === 'DRAW_CANVAS_READY') {
                        this._drawCanvasReady = true;
                        const width = this.widthWidget?.value || 512;
                        const height = this.heightWidget?.value || 512;

                        iframe.contentWindow.postMessage({
                            type: 'INIT_CANVAS',
                            width: width,
                            height: height
                        }, '*');

                        setTimeout(() => {
                            this.initResizeObserver();
                        }, 1000);

                    } else if (data.type === 'DRAW_DATA_UPDATE') {
                        // 更新裁剪数据
                        this.drawData = data.data;
                        if (drawDataWidget) {
                            drawDataWidget.value = this.drawData;
                        }
                        canvasWidget.value = this.drawData;

                        // 标记节点为脏
                        this.flags = this.flags || {};
                        this.flags.dirty = true;
                        if (app && app.graph) {
                            app.graph.setDirtyCanvas(true, true);
                        }

                    } else if (data.type === 'UPDATE_CANVAS_SIZE') {
                        // 自动更新画布尺寸参数（核心改动）
                        if (this.widthWidget && data.width) {
                            this.widthWidget.value = Math.max(1, Math.min(2048, data.width));
                            this.widthWidget.callback(this.widthWidget.value);
                        }
                        if (this.heightWidget && data.height) {
                            this.heightWidget.value = Math.max(1, Math.min(2048, data.height));
                            this.heightWidget.callback(this.heightWidget.value);
                        }
                        console.log("✅ 画布尺寸已更新:", data.width + 'x' + data.height);
                    }
                };

                window.addEventListener('message', handleMessage);

                // 监听Widget变化
                const origOnWidgetChanged = this.onWidgetChanged;
                this.onWidgetChanged = function(name, value, oldValue, widget) {
                    if (origOnWidgetChanged) {
                        origOnWidgetChanged.apply(this, arguments);
                    }

                    if ((name === "canvas_width" || name === "canvas_height") && this._drawCanvasReady) {
                        const width = this.widthWidget?.value || 512;
                        const height = this.heightWidget?.value || 512;

                        setTimeout(() => {
                            iframe.contentWindow.postMessage({
                                type: 'INIT_CANVAS',
                                width: width,
                                height: height
                            }, '*');
                            iframe.contentWindow.postMessage({
                                type: 'RESIZE_CANVAS'
                            }, '*');
                        }, 50);
                    }
                };

                // 清理函数
                const origOnRemoved = this.onRemoved;
                this.onRemoved = function() {
                    window.removeEventListener('message', handleMessage);

                    if (this._resizeObserver) {
                        try {
                            this._resizeObserver.disconnect();
                        } catch (e) {
                            console.warn("断开ResizeObserver失败:", e);
                        }
                        this._resizeObserver = null;
                    }

                    if (this._sizeCheckTimer) {
                        clearInterval(this._sizeCheckTimer);
                        this._sizeCheckTimer = null;
                    }

                    if (iframe._blobUrl) {
                        try {
                            URL.revokeObjectURL(iframe._blobUrl);
                        } catch (e) {
                            console.warn("清理Blob URL失败:", e);
                        }
                    }

                    if (origOnRemoved) {
                        origOnRemoved.apply(this, arguments);
                    }
                };

                // 设置节点初始大小
                this.setSize([450, 600]);

                return r;
            };

            // 执行完成后的回调
            const origOnExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                if (origOnExecuted) {
                    origOnExecuted.apply(this, arguments);
                }

                if (message?.image_base64) {
                    console.log("裁剪完成，生成图片预览");
                }
            };
        }
    }
});

console.log("自动裁剪图片节点扩展已加载");