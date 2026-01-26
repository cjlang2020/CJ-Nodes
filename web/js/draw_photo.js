import { app } from "../../../../scripts/app.js";

// 绘图界面HTML模板（完整保留）
const DRAW_HTML = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mouse Drawing Board</title>
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
        .tool-group {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        label {
            font-size: 14px;
            min-width: 20px;
        }
        input[type="color"] {
            width: 30px;
            height: 30px;
            border: 2px solid #fff;
            border-radius: 50%;
            cursor: pointer;
            padding: 0;
        }
        input[type="range"] {
            width: 100px;
            cursor: pointer;
        }
        button {
            padding: 2px 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        #pen-btn {
            background: #2ecc71;
            color: white;
        }
        #eraser-btn {
            background: #e74c3c;
            color: white;
        }
        #clear-btn {
            background: #f39c12;
            color: white;
        }
        #apply-bg {
            background: #3498db;
            color: white;
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
        #draw-canvas {
            border: 2px solid #383838;
            background: white;
            cursor: crosshair;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            touch-action: none;
            user-select: none;
            pointer-events: auto;
            display: block;
        }
        #status {
            padding: 5px 10px;
            background: #2c3e50;
            color: #2ecc71;
            font-size: 12px;
            text-align: center;
            flex-shrink: 0;
        }
        .size-display {
            min-width: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="toolbar">
        <div class="tool-group">
            <label>颜色:</label>
            <input type="color" id="pen-color" value="#000000">
        </div>
        <div class="tool-group">
            <label>大小:</label>
            <input type="range" id="pen-size" min="3" max="50" value="3">
            <span id="pen-size-value" class="size-display">5</span>
        </div>
        <div class="tool-group">
            <label>背景色:</label>
            <input type="color" id="bg-color" value="#ffffff">
            <button id="apply-bg">应用</button>
        </div>
        <div class="tool-group">
            <button id="pen-btn">画笔</button>
            <button id="eraser-btn">橡皮檫</button>
            <button id="clear-btn">清空</button>
        </div>
    </div>
    <div id="canvas-container">
        <canvas id="draw-canvas"></canvas>
    </div>
    <div id="status">准备绘制</div>

    <script>
        const state = {
            isDrawing: false,
            isEraser: false,
            penColor: '#000000',
            penSize: 5,
            bgColor: '#ffffff',
            currentPath: [],
            paths: [],
            canvasWidth: 512,
            canvasHeight: 512,
            canvas: null,
            ctx: null,
            scale: 1,
            offsetX: 0,
            offsetY: 0,
            resizeObserver: null
        };

        function initCanvas(width, height) {
            try {
                state.canvasWidth = width;
                state.canvasHeight = height;
                const canvas = document.getElementById('draw-canvas');
                const container = document.getElementById('canvas-container');
                canvas.width = width;
                canvas.height = height;
                updateCanvasScale();
                state.canvas = canvas;
                state.ctx = canvas.getContext('2d');
                resetCanvas();
                redrawAllPaths();
                console.log('Canvas initialized:', width + 'x' + height);
            } catch (e) {
                console.error('Canvas init failed:', e);
                document.getElementById('status').textContent = 'Init failed: ' + e.message;
            }
        }

        function updateCanvasScale() {
            const canvas = document.getElementById('draw-canvas');
            const container = document.getElementById('canvas-container');
            const containerStyles = window.getComputedStyle(container);
            const paddingLeft = parseFloat(containerStyles.paddingLeft) || 0;
            const paddingRight = parseFloat(containerStyles.paddingRight) || 0;
            const paddingTop = parseFloat(containerStyles.paddingTop) || 0;
            const paddingBottom = parseFloat(containerStyles.paddingBottom) || 0;
            const containerInnerWidth = container.clientWidth - paddingLeft - paddingRight;
            const containerInnerHeight = container.clientHeight - paddingTop - paddingBottom;
            const scaleX = containerInnerWidth / state.canvasWidth;
            const scaleY = containerInnerHeight / state.canvasHeight;
            state.scale = Math.min(scaleX, scaleY, 1);
            const displayWidth = state.canvasWidth * state.scale;
            const displayHeight = state.canvasHeight * state.scale;
            canvas.style.width = displayWidth + 'px';
            canvas.style.height = displayHeight + 'px';
            state.offsetX = (containerInnerWidth - displayWidth) / 2 + paddingLeft;
            state.offsetY = (containerInnerHeight - displayHeight) / 2 + paddingTop;
            canvas.style.position = 'absolute';
            canvas.style.left = state.offsetX + 'px';
            canvas.style.top = state.offsetY + 'px';
            canvas.style.margin = 0;
        }

        function resetCanvas() {
            const ctx = state.ctx;
            if (!ctx) return;
            ctx.fillStyle = state.bgColor;
            ctx.fillRect(0, 0, state.canvasWidth, state.canvasHeight);
        }

        function redrawAllPaths() {
            resetCanvas();
            const ctx = state.ctx;
            if (!ctx) return;
            state.paths.forEach(path => {
                if (path.points.length < 2) return;
                ctx.strokeStyle = path.is_eraser ? state.bgColor : path.color;
                ctx.lineWidth = path.size;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.beginPath();
                ctx.moveTo(path.points[0][0], path.points[0][1]);
                for (let i = 1; i < path.points.length; i++) {
                    ctx.lineTo(path.points[i][0], path.points[i][1]);
                }
                ctx.stroke();
                path.points.forEach(([x, y]) => {
                    ctx.fillStyle = path.is_eraser ? state.bgColor : path.color;
                    ctx.beginPath();
                    ctx.arc(x, y, path.size/2, 0, Math.PI*2);
                    ctx.fill();
                });
            });
        }

        function getCanvasCoords(clientX, clientY) {
            if (!state.canvas) return [0, 0];
            const rect = state.canvas.getBoundingClientRect();
            return [
                Math.max(0, Math.min(state.canvasWidth, (clientX - rect.left) / state.scale)),
                Math.max(0, Math.min(state.canvasHeight, (clientY - rect.top) / state.scale))
            ];
        }

        function sendDrawDataToParent() {
            const drawData = {
                bg_color: state.bgColor,
                paths: state.paths
            };
            try {
                const jsonStr = JSON.stringify(drawData);
                console.log('Sending draw data:', jsonStr.length, 'bytes');
                window.parent.postMessage({
                    type: 'DRAW_DATA_UPDATE',
                    data: jsonStr
                }, '*');
            } catch (e) {
                console.error('发送数据失败:', e);
            }
        }

        function setupEventListeners() {
            const container = document.getElementById('canvas-container');
            if (container && window.ResizeObserver) {
                state.resizeObserver = new ResizeObserver(entries => {
                    updateCanvasScale();
                    redrawAllPaths();
                });
                state.resizeObserver.observe(container);
            }

            document.getElementById('pen-color').addEventListener('input', (e) => {
                state.penColor = e.target.value;
                state.isEraser = false;
                document.getElementById('status').textContent = '画笔颜色设置: ' + state.penColor;
            });

            const penSize = document.getElementById('pen-size');
            const penSizeValue = document.getElementById('pen-size-value');
            penSize.addEventListener('input', (e) => {
                state.penSize = parseInt(e.target.value);
                penSizeValue.textContent = state.penSize;
                document.getElementById('status').textContent = '画笔大小设置: ' + state.penSize;
            });

            document.getElementById('bg-color').addEventListener('input', (e) => {
                state.bgColor = e.target.value;
            });

            document.getElementById('apply-bg').addEventListener('click', () => {
                resetCanvas();
                redrawAllPaths();
                sendDrawDataToParent();
                document.getElementById('status').textContent = '背景色: ' + state.bgColor;
            });

            document.getElementById('eraser-btn').addEventListener('click', () => {
                state.isEraser = true;
                document.getElementById('status').textContent = '工具: 橡皮檫 (size: ' + state.penSize + ')';
            });

            document.getElementById('pen-btn').addEventListener('click', () => {
                state.isEraser = false;
                document.getElementById('status').textContent = '工具: 画笔 (color: ' + state.penColor + ', size: ' + state.penSize + ')';
            });

            document.getElementById('clear-btn').addEventListener('click', () => {
                state.paths = [];
                state.currentPath = [];
                resetCanvas();
                sendDrawDataToParent();
                document.getElementById('status').textContent = '画布清除';
            });

            const canvas = document.getElementById('draw-canvas');
            let isMouseDown = false;

            canvas.addEventListener('mousedown', (e) => {
                e.preventDefault();
                e.stopPropagation();
                isMouseDown = true;
                state.isDrawing = true;

                const [x, y] = getCanvasCoords(e.clientX, e.clientY);
                console.log('开始绘制 at:', x, y);

                state.paths.push({
                    color: state.penColor,
                    size: state.penSize,
                    is_eraser: state.isEraser,
                    points: [[x, y]]
                });

                state.currentPath = [[x, y]];
                document.getElementById('status').textContent = '绘制中...';
            });

            document.addEventListener('mousemove', (e) => {
                if (!isMouseDown || !state.isDrawing) return;

                const rect = canvas.getBoundingClientRect();
                const inCanvas = e.clientX >= rect.left && e.clientX <= rect.right &&
                               e.clientY >= rect.top && e.clientY <= rect.bottom;

                if (!inCanvas) return;

                const [x, y] = getCanvasCoords(e.clientX, e.clientY);
                state.currentPath.push([x, y]);

                const currentPathObj = state.paths[state.paths.length - 1];
                if (currentPathObj) {
                    currentPathObj.points.push([x, y]);

                    const ctx = state.ctx;
                    if (ctx && state.currentPath.length > 1) {
                        ctx.strokeStyle = state.isEraser ? state.bgColor : state.penColor;
                        ctx.lineWidth = state.penSize;
                        ctx.lineCap = 'round';
                        ctx.lineJoin = 'round';

                        ctx.beginPath();
                        ctx.moveTo(state.currentPath[state.currentPath.length - 2][0],
                                   state.currentPath[state.currentPath.length - 2][1]);
                        ctx.lineTo(x, y);
                        ctx.stroke();

                        ctx.fillStyle = state.isEraser ? state.bgColor : state.penColor;
                        ctx.beginPath();
                        ctx.arc(x, y, state.penSize/2, 0, Math.PI*2);
                        ctx.fill();
                    }
                }
            });

            document.addEventListener('mouseup', () => {
                if (isMouseDown && state.isDrawing) {
                    isMouseDown = false;
                    state.isDrawing = false;
                    sendDrawDataToParent();
                    document.getElementById('status').textContent = '绘制完成 - 总路径: ' + state.paths.length;
                    console.log('绘制结束，总路径数:', state.paths.length);
                }
            });

            document.addEventListener('mouseleave', () => {
                if (isMouseDown) {
                    isMouseDown = false;
                    state.isDrawing = false;
                }
            });

            canvas.addEventListener('touchstart', (e) => {
                e.preventDefault();
                const touch = e.touches[0];
                const mouseEvent = new MouseEvent('mousedown', {
                    clientX: touch.clientX,
                    clientY: touch.clientY
                });
                canvas.dispatchEvent(mouseEvent);
            });

            canvas.addEventListener('touchmove', (e) => {
                e.preventDefault();
                const touch = e.touches[0];
                const mouseEvent = new MouseEvent('mousemove', {
                    clientX: touch.clientX,
                    clientY: touch.clientY
                });
                document.dispatchEvent(mouseEvent);
            });

            canvas.addEventListener('touchend', (e) => {
                e.preventDefault();
                const mouseEvent = new MouseEvent('mouseup', {});
                document.dispatchEvent(mouseEvent);
            });

            window.addEventListener('resize', () => {
                updateCanvasScale();
                redrawAllPaths();
            });
        }

        window.addEventListener('message', (e) => {
            try {
                const data = e.data;

                if (data.type === 'INIT_CANVAS') {
                    initCanvas(data.width || 512, data.height || 512);
                    document.getElementById('status').textContent = '画布初始化: ' + (data.width || 512) + 'x' + (data.height || 512);
                } else if (data.type === 'SYNC_SETTINGS') {
                    if (data.bgColor) {
                        state.bgColor = data.bgColor;
                        document.getElementById('bg-color').value = data.bgColor;
                    }
                    if (data.penColor) {
                        state.penColor = data.penColor;
                        document.getElementById('pen-color').value = data.penColor;
                    }
                    if (data.penSize) {
                        state.penSize = data.penSize;
                        document.getElementById('pen-size').value = data.penSize;
                        document.getElementById('pen-size-value').textContent = data.penSize;
                    }
                    redrawAllPaths();
                } else if (data.type === 'RESIZE_CANVAS') {
                    updateCanvasScale();
                    redrawAllPaths();
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

// 注册ComfyUI扩展（核心修改版）
app.registerExtension({
    name: "luy.mouseDraw",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "MouseDrawNode") {
            console.log("初始化鼠标绘图节点扩展");

            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                // 初始化绘图数据
                this.drawData = "empty";
                this._drawCanvasReady = false;
                this._resizeObserver = null;

                // ========== 关键1：隐藏draw_data的String Widget ==========
                const drawDataWidget = this.widgets.find(w => w.name === "draw_data");
                if (drawDataWidget) {
                    // 隐藏Widget，用户不可见
                    drawDataWidget.hidden = true;
                    // 初始化值
                    drawDataWidget.value = this.drawData;
                    console.log("✅ 已初始化并隐藏draw_data Widget");
                } else {
                    console.error("❌ 未找到draw_data Widget，请检查后端INPUT_TYPES配置");
                }

                // 创建iframe元素
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.borderRadius = "8px";
                iframe.style.backgroundColor = "#ffffff";
                iframe.style.pointerEvents = "auto";
                iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-popups allow-modals");

                // 创建Blob URL并设置src
                try {
                    const blob = new Blob([DRAW_HTML], { type: 'text/html;charset=utf-8' });
                    const blobUrl = URL.createObjectURL(blob);
                    iframe.src = blobUrl;
                    iframe._blobUrl = blobUrl;
                } catch (e) {
                    console.error("创建iframe失败:", e);
                    alert("创建绘图面板失败: " + e.message);
                }

                // 添加DOM Widget到节点
                const canvasWidget = this.addDOMWidget(
                    "draw_canvas",
                    "绘图画布",
                    iframe,
                    {
                        getValue: () => {
                            return node.drawData || "empty";
                        },
                        setValue: (v) => {
                            node.drawData = v;
                            // 同步到隐藏的draw_data Widget
                            const drawDataWidget = node.widgets.find(w => w.name === "draw_data");
                            if (drawDataWidget) {
                                drawDataWidget.value = v;
                            }
                            console.log('更新绘图数据:', v ? v.length : 0, 'bytes');
                        }
                    }
                );

                // 强制设置Widget尺寸
                canvasWidget.computeSize = function(width) {
                    const w = width || 400;
                    return [w, 800];
                };

                // 确保widget容器允许鼠标事件
                if (canvasWidget.element) {
                    canvasWidget.element.style.pointerEvents = "auto";
                }

                // 存储iframe引用
                this.drawIframe = iframe;

                // ResizeObserver 修复
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
                            console.log("ResizeObserver已初始化，监听元素:", observeTarget.tagName);
                        } catch (e) {
                            console.error("初始化ResizeObserver失败:", e);
                            this.startSizeCheckTimer();
                        }
                    } else {
                        console.warn("未找到有效的观察目标，使用定时器降级方案");
                        this.startSizeCheckTimer();
                    }
                };

                // 降级方案：使用定时器检查大小变化
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

                // 消息处理函数
                const handleMessage = (e) => {
                    if (e.source !== iframe.contentWindow) return;

                    const data = e.data;
                    console.log("收到绘图面板消息:", data.type);

                    if (data.type === 'DRAW_CANVAS_READY') {
                        this._drawCanvasReady = true;
                        const widthWidget = this.widgets.find(w => w.name === "canvas_width");
                        const heightWidget = this.widgets.find(w => w.name === "canvas_height");
                        console.log("widthWidget===:", widthWidget);

                        iframe.contentWindow.postMessage({
                            type: 'INIT_CANVAS',
                            width: widthWidget?.value || 512,
                            height: heightWidget?.value || 512
                        }, '*');

                        setTimeout(() => {
                            this.initResizeObserver();
                        }, 1000);

                    } else if (data.type === 'DRAW_DATA_UPDATE') {
                        // 更新绘图数据
                        this.drawData = data.data;
                        console.log("this.drawData===:", this.drawData);

                        // ========== 关键2：同步更新隐藏的draw_data Widget ==========
                        const drawDataWidget = this.widgets.find(w => w.name === "draw_data");
                        if (drawDataWidget) {
                            drawDataWidget.value = this.drawData;
                            console.log("✅ 已同步绘图数据到隐藏Widget，长度:", this.drawData.length);
                        }

                        // 同步到画布Widget
                        canvasWidget.value = this.drawData;
                        console.log("widget===:", canvasWidget);

                        // 标记节点为脏，触发参数刷新
                        this.flags = this.flags || {};
                        this.flags.dirty = true;
                        if (app && app.graph) {
                            app.graph.setDirtyCanvas(true, true);
                        }

                        console.log('绘图数据已更新，长度:', this.drawData ? this.drawData.length : 0);
                    }
                };

                // 添加消息监听
                window.addEventListener('message', handleMessage);

                // 监听Widget变化（画布尺寸调整）
                const origOnWidgetChanged = this.onWidgetChanged;
                this.onWidgetChanged = function(name, value, oldValue, widget) {
                    if (origOnWidgetChanged) {
                        origOnWidgetChanged.apply(this, arguments);
                    }

                    if ((name === "canvas_width" || name === "canvas_height") && this._drawCanvasReady) {
                        const widthWidget = this.widgets.find(w => w.name === "canvas_width");
                        const heightWidget = this.widgets.find(w => w.name === "canvas_height");

                        setTimeout(() => {
                            iframe.contentWindow.postMessage({
                                type: 'INIT_CANVAS',
                                width: widthWidget?.value || 512,
                                height: heightWidget?.value || 512
                            }, '*');

                            iframe.contentWindow.postMessage({
                                type: 'RESIZE_CANVAS'
                            }, '*');
                        }, 50);
                    }
                };

                // 清理函数（节点被删除时）
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
                    console.log("绘图完成，生成图片预览");
                }
            };
        }
    }
});

console.log("鼠标绘图节点扩展已加载");