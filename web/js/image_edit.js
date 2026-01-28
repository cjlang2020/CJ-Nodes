import { app } from "../../../../scripts/app.js";

// 图片编辑界面HTML模板（终极精准对齐）
const EDIT_HTML = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Editor (终极精准对齐)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            width: 100%;
            height: 100vh;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 0;
            margin: 0;
            cursor: default;
        }
        #main-toolbar {
            padding: 8px 10px;
            background: #242424;
            color: white;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
            flex-shrink: 0;
            border-bottom: 2px solid #444;
            z-index: 30;
        }
        .tool-group {
            display: flex;
            gap: 6px;
            align-items: center;
            border-right: 1px solid #555;
            padding-right: 12px;
        }
        .tool-group:last-child { border-right: none; }
        .tool-btn {
            padding: 4px 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
            background: #3498db;
            color: white;
        }
        .tool-btn.active {
            background: #2ecc71;
            box-shadow: 0 0 8px rgba(46, 204, 113, 0.5);
        }
        label { font-size: 12px; min-width: 50px; white-space: nowrap; }
        input[type="color"] {
            width: 28px;
            height: 28px;
            border: 2px solid #fff;
            border-radius: 50%;
            cursor: pointer;
            padding: 0;
        }
        input[type="range"] { width: 80px; cursor: pointer; }
        .range-value {
            min-width: 28px;
            text-align: center;
            font-size: 12px;
            color: #eee;
        }
        #canvas-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            background: #cccccc;
            padding: 10px;
            position: relative;
        }
        #edit-canvas {
            border: 2px solid #333;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            touch-action: none;
            user-select: none;
            background: #f8f8f8;
            display: none;
        }
        #crop-rect {
            position: absolute;
            border: 2px solid #3498db;
            background: rgba(52, 152, 219, 0.15);
            display: none;
            pointer-events: none;
            z-index: 10;
        }
        /* 笔触预览圆圈 - 精准对齐 */
        #brush-preview {
            position: absolute;
            border: 2px solid #0099ff;
            border-radius: 50%;
            background: rgba(0, 153, 255, 0.1);
            pointer-events: none;
            z-index: 20;
            display: none;
            transform: translate(-50%, -50%);
        }
        #status {
            padding: 4px 10px;
            background: #2c3e50;
            color: #2ecc71;
            font-size: 12px;
            text-align: left;
            flex-shrink: 0;
        }
        #image-input { display: none; }
        #upload-btn { background: #2ecc71; }
    </style>
</head>
<body>
    <div id="main-toolbar">
        <!-- 基础工具：上传+裁剪 -->
        <div class="tool-group">
            <input type="file" id="image-input" accept="image/*">
            <button id="upload-btn" class="tool-btn">上传图片</button>
            <button id="crop-btn" class="tool-btn">裁剪</button>
        </div>
        <!-- 画笔工具：颜色+大小+透明度 -->
        <div class="tool-group">
            <button id="draw-btn" class="tool-btn">画笔</button>
            <label>颜色:</label>
            <input type="color" id="draw-color" value="#000000">
            <label>大小:</label>
            <input type="range" id="draw-size" min="1" max="60" value="5">
            <span id="draw-size-val" class="range-value">5</span>
            <label>透明度:</label>
            <input type="range" id="draw-alpha" min="0.1" max="1" step="0.1" value="1">
            <span id="draw-alpha-val" class="range-value">1.0</span>
        </div>
        <!-- 液化工具：简化版 -->
        <div class="tool-group">
            <button id="liquify-btn" class="tool-btn">液化</button>
            <label>大小:</label>
            <input type="range" id="liquify-size" min="5" max="120" value="20">
            <span id="liquify-size-val" class="range-value">20</span>
            <label>强度:</label>
            <input type="range" id="liquify-strength" min="0.1" max="1" step="0.1" value="0.5">
            <span id="liquify-strength-val" class="range-value">0.5</span>
        </div>
        <!-- 橡皮擦工具：大小调节 -->
        <div class="tool-group">
            <button id="erase-btn" class="tool-btn">橡皮擦</button>
            <label>大小:</label>
            <input type="range" id="erase-size" min="5" max="120" value="10">
            <span id="erase-size-val" class="range-value">10</span>
        </div>
    </div>

    <div id="canvas-container">
        <canvas id="edit-canvas"></canvas>
        <div id="crop-rect"></div>
        <!-- 笔触预览圆圈 -->
        <div id="brush-preview"></div>
    </div>

    <div id="status">🟢 就绪 | 请先上传图片开始编辑</div>

    <script>
        // 全局状态管理
        const state = {
            currentTool: 'none',
            isUploaded: false,
            isMouseDown: false,
            ctx: null,
            canvas: null,
            originalImage: null,
            tempImageData: null,
            canvasW: 512,
            canvasH: 512,
            scale: 1,
            offsetX: 0,
            offsetY: 0,
            toolbarHeight: 0,
            // 画笔状态
            drawColor: '#000000',
            drawSize: 5,
            drawAlpha: 1.0,
            // 液化状态
            liquifySize: 20,
            liquifyStrength: 0.5,
            lastLiquifyPos: null,
            // 橡皮擦状态
            eraseSize: 10,
            // 最终编辑数据
            finalImageBase64: "",
            cropWidth: 512,
            cropHeight: 512,
            brushPreview: null,
            resizeObserver: null
        };

        // ==============================================
        // 初始化Canvas
        // ==============================================
        function initCanvas(w, h) {
            state.canvas = document.getElementById('edit-canvas');
            state.ctx = state.canvas.getContext('2d');
            state.canvas.width = w;
            state.canvas.height = h;
            state.canvasW = w;
            state.canvasH = h;
            state.canvas.style.display = 'block';
            state.brushPreview = document.getElementById('brush-preview');
            // 获取工具栏高度（仅用于笔触预览位置计算）
            state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
            updateCanvasScale();
            setStatus(\`⚙️ 画布初始化完成 | \${w}x\${h}\`);
        }

        // ==============================================
        // 画布缩放适配
        // ==============================================
        function updateCanvasScale() {
            if (!state.isUploaded || !state.canvas) return;
            const container = document.getElementById('canvas-container');
            const containerStyle = window.getComputedStyle(container);
            const padL = parseFloat(containerStyle.paddingLeft) || 0;
            const padR = parseFloat(containerStyle.paddingRight) || 0;
            const padT = parseFloat(containerStyle.paddingTop) || 0;
            const padB = parseFloat(containerStyle.paddingBottom) || 0;
            const contW = container.clientWidth - padL - padR;
            const contH = container.clientHeight - padT - padB;
            const scaleX = contW / state.canvasW;
            const scaleY = contH / state.canvasH;
            state.scale = Math.min(scaleX, scaleY, 1);
            const dispW = state.canvasW * state.scale;
            const dispH = state.canvasH * state.scale;
            state.offsetX = (contW - dispW) / 2 + padL;
            state.offsetY = (contH - dispH) / 2 + padT;
            state.canvas.style.width = \`\${dispW}px\`;
            state.canvas.style.height = \`\${dispH}px\`;
            state.canvas.style.left = \`\${state.offsetX}px\`;
            state.canvas.style.top = \`\${state.offsetY}px\`;
            state.canvas.style.position = 'absolute';
        }

        // ==============================================
        // 坐标转换：屏幕坐标 → Canvas实际坐标（1:1精准对齐）
        // ==============================================
        function getCanvasXY(clientX, clientY) {
            if (!state.canvas) return [0, 0];
            // 绘制点不需要减去工具栏高度，直接使用原始鼠标坐标
            const rect = state.canvas.getBoundingClientRect();
            const x = (clientX - rect.left) / state.scale;
            const y = (clientY - rect.top) / state.scale;
            return [
                Math.max(0, Math.min(state.canvasW, x)),
                Math.max(0, Math.min(state.canvasH, y))
            ];
        }

        // ==============================================
        // 状态提示
        // ==============================================
        function setStatus(text) {
            document.getElementById('status').textContent = text;
        }

        // ==============================================
        // 工具切换
        // ==============================================
        function switchTool(tool) {
            document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
            state.currentTool = tool;
            if (tool === 'draw' || tool === 'liquify' || tool === 'erase') {
                updateBrushPreviewSize();
                state.brushPreview.style.display = 'block';
            } else {
                state.brushPreview.style.display = 'none';
            }
            switch(tool) {
                case 'crop':
                    document.getElementById('crop-btn').classList.add('active');
                    setStatus(\`✂️ 裁剪工具 | 拖拽选择裁剪区域\`);
                    break;
                case 'draw':
                    document.getElementById('draw-btn').classList.add('active');
                    setStatus(\`🖌️ 画笔工具 | 颜色:\${state.drawColor} 大小:\${state.drawSize}\`);
                    break;
                case 'liquify':
                    document.getElementById('liquify-btn').classList.add('active');
                    setStatus(\`🌀 液化工具 | 大小:\${state.liquifySize} 强度:\${state.liquifyStrength}\`);
                    break;
                case 'erase':
                    document.getElementById('erase-btn').classList.add('active');
                    setStatus(\`🧽 橡皮擦工具 | 大小:\${state.eraseSize}\`);
                    break;
                default:
                    state.brushPreview.style.display = 'none';
                    setStatus(\`🟢 就绪 | 选择工具开始编辑\`);
            }
            document.getElementById('crop-rect').style.display = 'none';
        }

        // ==============================================
        // 更新笔触预览大小
        // ==============================================
        function updateBrushPreviewSize() {
            if (!state.brushPreview) return;
            let size = 0;
            switch(state.currentTool) {
                case 'draw': size = state.drawSize; break;
                case 'liquify': size = state.liquifySize; break;
                case 'erase': size = state.eraseSize; break;
                default: return;
            }
            const displaySize = size * state.scale * 2;
            state.brushPreview.style.width = \`\${displaySize}px\`;
            state.brushPreview.style.height = \`\${displaySize}px\`;
        }

        // ==============================================
        // 更新笔触预览位置（精准对齐）
        // ==============================================
        function updateBrushPreviewPos(clientX, clientY) {
            if (!state.brushPreview || state.currentTool === 'none' || state.currentTool === 'crop') return;
            // 笔触预览需要减去工具栏高度，保证视觉上与鼠标重合
            const adjustedY = clientY - state.toolbarHeight;
            state.brushPreview.style.left = \`\${clientX}px\`;
            state.brushPreview.style.top = \`\${adjustedY}px\`;
        }

        // ==============================================
        // 画布转Base64
        // ==============================================
        function getCanvasBase64() {
            return state.canvas.toDataURL('image/png', 1.0);
        }

        // ==============================================
        // 发送数据到后端
        // ==============================================
        function sendToParent() {
            state.finalImageBase64 = getCanvasBase64();
            const sendData = {
                final_image_base64: state.finalImageBase64,
                crop_width: state.cropWidth,
                crop_height: state.cropHeight
            };
            try {
                window.parent.postMessage({
                    type: 'DRAW_DATA_UPDATE',
                    data: JSON.stringify(sendData)
                }, '*');
                window.parent.postMessage({
                    type: 'UPDATE_CANVAS_SIZE',
                    width: state.cropWidth,
                    height: state.cropHeight
                }, '*');
            } catch (e) {
                setStatus(\`❌ 数据发送失败: \${e.message}\`);
            }
        }

        // ==============================================
        // 裁剪执行
        // ==============================================
        function execCrop() {
            const x1 = Math.max(0, Math.min(state.canvasW, state.cropX1));
            const y1 = Math.max(0, Math.min(state.canvasH, state.cropY1));
            const x2 = Math.max(x1 + 10, Math.min(state.canvasW, state.cropX2));
            const y2 = Math.max(y1 + 10, Math.min(state.canvasH, state.cropY2));
            const cropImageData = state.ctx.getImageData(x1, y1, x2 - x1, y2 - y1);
            initCanvas(x2 - x1, y2 - y1);
            state.ctx.putImageData(cropImageData, 0, 0);
            state.cropWidth = x2 - x1;
            state.cropHeight = y2 - y1;
            const tempImg = new Image();
            tempImg.onload = () => { state.originalImage = tempImg; };
            tempImg.src = getCanvasBase64();
            sendToParent();
            setStatus(\`✅ 裁剪完成 | 新尺寸: \${state.cropWidth}x\${state.cropHeight}\`);
        }

        // ==============================================
        // 画笔工具：初始化画笔样式
        // ==============================================
        function initDrawStyle() {
            state.ctx.globalAlpha = state.drawAlpha;
            state.ctx.strokeStyle = state.drawColor;
            state.ctx.lineWidth = state.drawSize;
            state.ctx.lineCap = 'round';
            state.ctx.lineJoin = 'round';
            state.ctx.beginPath();
        }

        // ==============================================
        // 液化工具：像素跟随鼠标移动（方向完全一致）
        // ==============================================
        function execLiquify(x, y) {
            if (!state.tempImageData || !state.canvas || !state.lastLiquifyPos) return;
            const size = state.liquifySize;
            const strength = state.liquifyStrength;
            const imgData = state.ctx.getImageData(0, 0, state.canvasW, state.canvasH);
            const pixels = imgData.data;
            const width = state.canvasW;
            const height = state.canvasH;
            // 计算鼠标移动向量
            const dxMove = x - state.lastLiquifyPos.x;
            const dyMove = y - state.lastLiquifyPos.y;
            const moveDist = Math.sqrt(dxMove * dxMove + dyMove * dyMove);
            if (moveDist < 0.1) return;
            const radiusSq = size * size;
            for (let dy = -size; dy <= size; dy++) {
                for (let dx = -size; dx <= size; dx++) {
                    const currX = Math.floor(x + dx);
                    const currY = Math.floor(y + dy);
                    if (currX < 0 || currX >= width || currY < 0 || currY >= height) continue;
                    const distSq = dx * dx + dy * dy;
                    if (distSq > radiusSq) continue;
                    const decay = 1.0 - (distSq / radiusSq);
                    const finalStrength = strength * decay;
                    // 修正方向：像素移动方向与鼠标方向完全一致
                    const offsetX = dxMove * finalStrength;
                    const offsetY = dyMove * finalStrength;
                    // 修正源像素坐标：currX - offsetX → 确保像素跟随鼠标移动
                    const srcX = Math.floor(currX - offsetX);
                    const srcY = Math.floor(currY - offsetY);
                    if (srcX < 0 || srcX >= width || srcY < 0 || srcY >= height) continue;
                    const srcIdx = (srcY * width + srcX) * 4;
                    const tarIdx = (currY * width + currX) * 4;
                    pixels[tarIdx] = state.tempImageData.data[srcIdx];
                    pixels[tarIdx + 1] = state.tempImageData.data[srcIdx + 1];
                    pixels[tarIdx + 2] = state.tempImageData.data[srcIdx + 2];
                    pixels[tarIdx + 3] = state.tempImageData.data[srcIdx + 3];
                }
            }
            state.ctx.putImageData(imgData, 0, 0);
            state.tempImageData = state.ctx.getImageData(0, 0, width, height);
            state.lastLiquifyPos = {x, y};
        }

        // ==============================================
        // 橡皮擦工具：流畅连续擦除
        // ==============================================
        function execErase(x, y, isContinuous = false) {
            if (!state.originalImage || !state.canvas) return;
            const size = state.eraseSize;
            const halfSize = size / 2;
            if (isContinuous) {
                state.ctx.save();
                state.ctx.beginPath();
                state.ctx.arc(x, y, halfSize, 0, Math.PI * 2);
                state.ctx.clip();
                state.ctx.drawImage(
                    state.originalImage,
                    x - halfSize, y - halfSize, size, size,
                    x - halfSize, y - halfSize, size, size
                );
                state.ctx.restore();
            } else {
                state.ctx.drawImage(
                    state.originalImage,
                    x - halfSize, y - halfSize, size, size,
                    x - halfSize, y - halfSize, size, size
                );
            }
        }

        // ==============================================
        // 初始化事件监听
        // ==============================================
        function initEvent() {
            // 上传图片
            document.getElementById('upload-btn').addEventListener('click', () => {
                document.getElementById('image-input').click();
            });
            document.getElementById('image-input').addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file || !file.type.startsWith('image/')) return;
                const reader = new FileReader();
                reader.onload = (ev) => {
                    const img = new Image();
                    img.onload = () => {
                        initCanvas(img.width, img.height);
                        state.ctx.drawImage(img, 0, 0);
                        state.originalImage = img;
                        state.tempImageData = state.ctx.getImageData(0, 0, img.width, img.height);
                        state.isUploaded = true;
                        state.cropWidth = img.width;
                        state.cropHeight = img.height;
                        sendToParent();
                        setStatus(\`✅ 图片上传成功 | 原始尺寸: \${img.width}x\${img.height}\`);
                    };
                    img.src = ev.target.result;
                };
                reader.readAsDataURL(file);
            });

            // 工具按钮
            document.getElementById('crop-btn').onclick = () => switchTool('crop');
            document.getElementById('draw-btn').onclick = () => switchTool('draw');
            document.getElementById('liquify-btn').onclick = () => switchTool('liquify');
            document.getElementById('erase-btn').onclick = () => switchTool('erase');

            // 画笔参数
            const drawColor = document.getElementById('draw-color');
            const drawSize = document.getElementById('draw-size');
            const drawAlpha = document.getElementById('draw-alpha');
            const drawSizeVal = document.getElementById('draw-size-val');
            const drawAlphaVal = document.getElementById('draw-alpha-val');
            drawColor.oninput = (e) => { state.drawColor = e.target.value; switchTool('draw'); };
            drawSize.oninput = (e) => {
                state.drawSize = parseInt(e.target.value);
                drawSizeVal.textContent = state.drawSize;
                updateBrushPreviewSize();
                switchTool('draw');
            };
            drawAlpha.oninput = (e) => {
                state.drawAlpha = parseFloat(e.target.value);
                drawAlphaVal.textContent = state.drawAlpha.toFixed(1);
                switchTool('draw');
            };

            // 液化参数
            const liquifySize = document.getElementById('liquify-size');
            const liquifyStrength = document.getElementById('liquify-strength');
            const liquifySizeVal = document.getElementById('liquify-size-val');
            const liquifyStrengthVal = document.getElementById('liquify-strength-val');
            liquifySize.oninput = (e) => {
                state.liquifySize = parseInt(e.target.value);
                liquifySizeVal.textContent = state.liquifySize;
                updateBrushPreviewSize();
                switchTool('liquify');
            };
            liquifyStrength.oninput = (e) => {
                state.liquifyStrength = parseFloat(e.target.value);
                liquifyStrengthVal.textContent = state.liquifyStrength.toFixed(1);
                switchTool('liquify');
            };

            // 橡皮擦参数
            const eraseSize = document.getElementById('erase-size');
            const eraseSizeVal = document.getElementById('erase-size-val');
            eraseSize.oninput = (e) => {
                state.eraseSize = parseInt(e.target.value);
                eraseSizeVal.textContent = state.eraseSize;
                updateBrushPreviewSize();
                switchTool('erase');
            };

            // 鼠标移动
            document.addEventListener('mousemove', (e) => {
                updateBrushPreviewPos(e.clientX, e.clientY);
                if (!state.isMouseDown || !state.isUploaded) return;
                const [x, y] = getCanvasXY(e.clientX, e.clientY);
                switch(state.currentTool) {
                    case 'crop':
                        state.cropX2 = x; state.cropY2 = y;
                        updateCropRect();
                        break;
                    case 'draw':
                        state.ctx.lineTo(x, y);
                        state.ctx.stroke();
                        state.ctx.beginPath();
                        state.ctx.moveTo(x, y);
                        break;
                    case 'liquify':
                        execLiquify(x, y);
                        break;
                    case 'erase':
                        execErase(x, y, true);
                        break;
                }
            });

            // Canvas鼠标交互
            const canvas = document.getElementById('edit-canvas');
            canvas.addEventListener('mousedown', (e) => {
                if (!state.isUploaded) return;
                e.preventDefault();
                state.isMouseDown = true;
                const [x, y] = getCanvasXY(e.clientX, e.clientY);
                switch(state.currentTool) {
                    case 'crop':
                        state.cropX1 = x; state.cropY1 = y;
                        state.cropX2 = x; state.cropY2 = y;
                        document.getElementById('crop-rect').style.display = 'block';
                        updateCropRect();
                        break;
                    case 'draw':
                        initDrawStyle();
                        state.ctx.moveTo(x, y);
                        break;
                    case 'liquify':
                        state.tempImageData = state.ctx.getImageData(0, 0, state.canvasW, state.canvasH);
                        state.lastLiquifyPos = {x, y};
                        break;
                    case 'erase':
                        execErase(x, y, false);
                        break;
                }
            });

            document.addEventListener('mouseup', () => {
                if (!state.isMouseDown || !state.isUploaded) return;
                state.isMouseDown = false;
                switch(state.currentTool) {
                    case 'crop':
                        execCrop();
                        break;
                    case 'draw':
                    case 'liquify':
                    case 'erase':
                        sendToParent();
                        break;
                }
            });

            canvas.addEventListener('mouseleave', () => {
                if (state.isMouseDown) {
                    state.isMouseDown = false;
                    if (state.currentTool === 'draw' || state.currentTool === 'erase') {
                        sendToParent();
                    }
                }
            });

            // 窗口大小变化
            window.addEventListener('resize', () => {
                state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
                updateCanvasScale();
                updateBrushPreviewSize();
            });

            // ResizeObserver
            if (window.ResizeObserver) {
                state.resizeObserver = new ResizeObserver(() => {
                    state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
                    updateCanvasScale();
                    updateBrushPreviewSize();
                });
                state.resizeObserver.observe(document.getElementById('canvas-container'));
            }
        }

        // ==============================================
        // 初始化
        // ==============================================
        window.onload = () => {
            initCanvas(512, 512);
            initEvent();
            setTimeout(() => {
                window.parent.postMessage({type: 'DRAW_CANVAS_READY'}, '*');
            }, 100);
        };

        // ==============================================
        // 清理资源
        // ==============================================
        window.addEventListener('unload', () => {
            if (state.resizeObserver) state.resizeObserver.disconnect();
        });

        // ==============================================
        // 监听父窗口消息
        // ==============================================
        window.addEventListener('message', (e) => {
            try {
                if (e.data.type === 'INIT_CANVAS') {
                    initCanvas(e.data.width || 512, e.data.height || 512);
                } else if (e.data.type === 'RESIZE_CANVAS') {
                    state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
                    updateCanvasScale();
                    updateBrushPreviewSize();
                }
            } catch (e) {
                console.error('处理父窗口消息失败:', e);
            }
        });
    </script>
</body>
</html>
`;

// 注册ComfyUI扩展
app.registerExtension({
    name: "luy.imageEditUltimatePrecise",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ImageEditNode") {
            console.log("✅ 初始化终极精准对齐图片编辑节点扩展");

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
                    const blob = new Blob([EDIT_HTML], { type: 'text/html;charset=utf-8' });
                    const blobUrl = URL.createObjectURL(blob);
                    iframe.src = blobUrl;
                    iframe._blobUrl = blobUrl;
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
                                this.widthWidget.callback(this.widthWidget.value);
                            }
                            if (this.heightWidget && data.height) {
                                this.heightWidget.value = Math.max(1, Math.min(4096, data.height));
                                this.heightWidget.callback(this.heightWidget.value);
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
                    if (iframe._blobUrl) URL.revokeObjectURL(iframe._blobUrl);
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

console.log("✅ 终极精准对齐图片编辑节点扩展加载完成（luy分类）");