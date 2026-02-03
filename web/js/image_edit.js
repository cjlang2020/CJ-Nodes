import { app } from "../../../../scripts/app.js";

// 图片编辑界面HTML模板（裁剪应用按钮+精准对齐+液化正向）
const EDIT_HTML = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Editor (裁剪应用按钮+终极精准版)</title>
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
        /* 清除按钮特殊样式 */
        #clear-btn {
            background: #e67e22;
        }
        #clear-btn:hover {
            background: #d35400;
        }
        /* 重置按钮特殊样式 */
        #reset-btn {
            background: #9b59b6;
        }
        #reset-btn:hover {
            background: #8e44ad;
        }
        /* 应用裁剪按钮特殊样式 */
        #apply-crop-btn {
            background: #e74c3c;
        }
        #apply-crop-btn:hover {
            background: #c0392b;
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
        <!-- 基础工具：上传+裁剪+应用裁剪 -->
        <div class="tool-group">
            <input type="file" id="image-input" accept="image/*">
            <button id="upload-btn" class="tool-btn">上传图片</button>
            <button id="crop-btn" class="tool-btn">裁剪画面</button>
            <button id="apply-crop-btn" class="tool-btn" disabled>应用裁剪</button>
            <button id="clear-btn" class="tool-btn">清除画布</button>
            <button id="reset-btn" class="tool-btn">重置大小</button>
        </div>
        <!-- 画笔工具：颜色+大小+透明度 -->
        <div class="tool-group">
            <button id="draw-btn" class="tool-btn">画笔</button>
            <button id="erase-btn" class="tool-btn">橡皮擦</button>
            <label>颜色:</label>
            <input type="color" id="draw-color" value="#000000">
            <label>大小:</label>
            <input type="range" id="draw-size" min="1" max="200" value="5">
            <span id="draw-size-val" class="range-value">5</span>
            <label>透明度:</label>
            <input type="range" id="draw-alpha" min="0.1" max="1" step="0.1" value="1">
            <span id="draw-alpha-val" class="range-value">1.0</span>
        </div>
        <!-- 液化工具：简化版 -->
        <div class="tool-group">
            <button id="liquify-btn" class="tool-btn">液化</button>
            <label>强度:</label>
            <input type="range" id="liquify-strength" min="0.1" max="1" step="0.1" value="0.5">
            <span id="liquify-strength-val" class="range-value">0.5</span>
        </div>
    </div>

    <div id="canvas-container">
        <canvas id="edit-canvas"></canvas>
        <div id="crop-rect"></div>
        <!-- 笔触预览圆圈 -->
        <div id="brush-preview"></div>
    </div>

    <div id="status">🟢 就绪 | 可直接绘画或上传图片 | 清除：清空画布 | 重置：恢复初始尺寸</div>

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
            initialW: 512,  // 初始画布宽度
            initialH: 512,  // 初始画布高度
            scale: 1,
            offsetX: 0,
            offsetY: 0,
            toolbarHeight: 0,
            // 裁剪状态
            cropX1: 0, cropY1: 0, cropX2: 0, cropY2: 0,
            isCropSelected: false, // 是否选择了裁剪区域
            // 画笔状态
            drawColor: '#000000',
            drawSize: 5,
            drawAlpha: 1.0,
            // 液化状态
            liquifyStrength: 0.5,
            lastLiquifyPos: null,
            // 最终编辑数据
            finalImageBase64: "",
            cropWidth: 512,
            cropHeight: 512,
            brushPreview: null,
            cropRect: null,
            applyCropBtn: null, // 应用裁剪按钮
            resizeObserver: null
        };

        // ==============================================
        // 初始化Canvas（支持保留并缩放现有内容）
        // ==============================================
        function initCanvas(w, h, saveInitial = true, preserveContent = true) {
            // 保存当前画布内容（如果需要）
            let savedImage = null;
            let oldW = state.canvasW;
            let oldH = state.canvasH;
            if (preserveContent && state.canvas && (oldW > 0 && oldH > 0) && (w !== oldW || h !== oldH)) {
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = oldW;
                tempCanvas.height = oldH;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.drawImage(state.canvas, 0, 0);
                savedImage = tempCanvas.toDataURL();
            }

            state.canvas = document.getElementById('edit-canvas');
            state.ctx = state.canvas.getContext('2d');
            state.canvas.width = w;
            state.canvas.height = h;
            state.canvasW = w;
            state.canvasH = h;
            // 如果是第一次初始化或明确要求保存，保存初始尺寸
            if (saveInitial) {
                state.initialW = w;
                state.initialH = h;
            }
            state.canvas.style.display = 'block';
            state.brushPreview = document.getElementById('brush-preview');
            // 获取裁剪框和应用裁剪按钮DOM
            state.cropRect = document.getElementById('crop-rect');
            state.applyCropBtn = document.getElementById('apply-crop-btn');
            // 获取工具栏高度（仅用于笔触预览位置计算）
            state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
            // 填充白色背景
            state.ctx.fillStyle = '#ffffff';
            state.ctx.fillRect(0, 0, w, h);
            // 如果没有上传图片，创建一个空白背景的原始图像引用
            if (!state.originalImage) {
                const blankCanvas = document.createElement('canvas');
                blankCanvas.width = w;
                blankCanvas.height = h;
                const blankCtx = blankCanvas.getContext('2d');
                blankCtx.fillStyle = '#ffffff';
                blankCtx.fillRect(0, 0, w, h);
                const blankImg = new Image();
                blankImg.onload = () => { state.originalImage = blankImg; };
                blankImg.src = blankCanvas.toDataURL();
            }

            // 如果保存了旧内容，等比缩放绘制到新画布
            if (savedImage) {
                const img = new Image();
                img.onload = () => {
                    // 计算缩放比例，等比适应新尺寸
                    const scaleX = w / oldW;
                    const scaleY = h / oldH;
                    const scale = Math.min(scaleX, scaleY);
                    const drawW = oldW * scale;
                    const drawH = oldH * scale;
                    const offsetX = (w - drawW) / 2;
                    const offsetY = (h - drawH) / 2;
                    state.ctx.drawImage(img, offsetX, offsetY, drawW, drawH);
                    // 更新原始图像引用（包含缩放后的内容）
                    state.originalImage = new Image();
                    state.originalImage.onload = () => {};
                    state.originalImage.src = state.canvas.toDataURL();
                    // 更新临时数据
                    state.tempImageData = state.ctx.getImageData(0, 0, w, h);
                    // 发送更新后的数据
                    sendToParent(true);
                    setStatus(\`📐 画布已调整并等比缩放内容 | \${w}x\${h}\`);
                };
                img.src = savedImage;
            }

            updateCanvasScale();
            if (!savedImage) {
                setStatus(\`⚙️ 画布初始化完成 | \${w}x\${h} | 可以直接绘画或上传图片\`);
            }
        }

        // ==============================================
        // 画布缩放适配
        // ==============================================
        function updateCanvasScale() {
            if (!state.canvas) return;
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
            // 绘制点不扣工具栏高度，保证与鼠标精准重合
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

            // 重置裁剪选择状态
            state.isCropSelected = false;
            // 禁用应用裁剪按钮
            if (state.applyCropBtn) state.applyCropBtn.disabled = true;

            // 笔触预览和裁剪框互斥显示
            if (tool === 'draw' || tool === 'liquify' || tool === 'erase') {
                updateBrushPreviewSize();
                state.brushPreview.style.display = 'block';
                if (state.cropRect) state.cropRect.style.display = 'none';
            } else if (tool === 'crop') {
                state.brushPreview.style.display = 'none';
                // 裁剪工具激活时显示裁剪框（如果有选择区域）
                if (state.isCropSelected && state.cropRect) {
                    state.cropRect.style.display = 'block';
                }
            } else {
                state.brushPreview.style.display = 'none';
                if (state.cropRect) state.cropRect.style.display = 'none';
            }

            // 激活当前工具并更新提示
            switch(tool) {
                case 'crop':
                    document.getElementById('crop-btn').classList.add('active');
                    setStatus(\`✂️ 裁剪工具 | 拖拽选择裁剪区域，点击「应用裁剪」确认\`);
                    break;
                case 'draw':
                    document.getElementById('draw-btn').classList.add('active');
                    setStatus(\`🖌️ 画笔工具 | 颜色:\${state.drawColor} 大小:\${state.drawSize}\`);
                    break;
                case 'liquify':
                    document.getElementById('liquify-btn').classList.add('active');
                    setStatus(\`🌀 液化工具 | 大小:\${state.drawSize} 强度:\${state.liquifyStrength}\`);
                    break;
                case 'erase':
                    document.getElementById('erase-btn').classList.add('active');
                    setStatus(\`🧽 橡皮擦工具 | 大小:\${state.drawSize}\`);
                    break;
                default:
                    setStatus(\`🟢 就绪 | 选择工具开始编辑（裁剪/画笔/液化/橡皮擦）| 清除：清空画布 | 重置：恢复初始尺寸\`);
            }
        }

        // ==============================================
        // 更新笔触预览大小
        // ==============================================
        function updateBrushPreviewSize() {
            if (!state.brushPreview) return;
            const size = state.drawSize;
            const displaySize = size * state.scale * 2;
            state.brushPreview.style.width = \`\${displaySize}px\`;
            state.brushPreview.style.height = \`\${displaySize}px\`;
        }

        // ==============================================
        // 更新笔触预览位置（精准对齐）
        // ==============================================
        function updateBrushPreviewPos(clientX, clientY) {
            if (!state.brushPreview || state.currentTool === 'none' || state.currentTool === 'crop') return;
            // 笔触预览扣工具栏高度，保证视觉与鼠标重合
            const adjustedY = clientY - state.toolbarHeight;
            state.brushPreview.style.left = \`\${clientX}px\`;
            state.brushPreview.style.top = \`\${adjustedY}px\`;
        }

        // ==============================================
        // 更新裁剪矩形框显示（核心修复：保证蓝色框正常渲染）
        // ==============================================
        function updateCropRect() {
            if (!state.cropRect || !state.isCropSelected) return;
            // 计算裁剪框在容器中的实际坐标（适配画布缩放和偏移）
            const x1 = state.cropX1 * state.scale + state.offsetX;
            const y1 = state.cropY1 * state.scale + state.offsetY;
            const x2 = state.cropX2 * state.scale + state.offsetX;
            const y2 = state.cropY2 * state.scale + state.offsetY;
            // 设置裁剪框样式，保证可见
            state.cropRect.style.left = \`\${Math.min(x1, x2)}px\`;
            state.cropRect.style.top = \`\${Math.min(y1, y2)}px\`;
            state.cropRect.style.width = \`\${Math.abs(x2 - x1)}px\`;
            state.cropRect.style.height = \`\${Math.abs(y2 - y1)}px\`;
            state.cropRect.style.display = 'block';
            // 启用应用裁剪按钮
            if (state.applyCropBtn) state.applyCropBtn.disabled = false;
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
        function sendToParent(shouldUpdateSize = false) {
            state.finalImageBase64 = getCanvasBase64();
            const sendData = {
                final_image_base64: state.finalImageBase64,
                crop_width: state.canvasW,
                crop_height: state.canvasH
            };
            try {
                window.parent.postMessage({
                    type: 'DRAW_DATA_UPDATE',
                    data: JSON.stringify(sendData)
                }, '*');
                // 只有在裁剪或重置等真正改变尺寸时才更新尺寸widget
                if (shouldUpdateSize) {
                    window.parent.postMessage({
                        type: 'UPDATE_CANVAS_SIZE',
                        width: state.canvasW,
                        height: state.canvasH
                    }, '*');
                }
            } catch (e) {
                setStatus(\`❌ 数据发送失败: \${e.message}\`);
            }
        }

        // ==============================================
        // 裁剪执行：裁剪Canvas并更新为裁剪后的图片（点击应用后执行）
        // ==============================================
        function execCrop() {
            if (!state.isCropSelected) return;
            // 保证裁剪区域有效（最小10px，避免空裁剪）
            const x1 = Math.max(0, Math.min(state.canvasW, state.cropX1));
            const y1 = Math.max(0, Math.min(state.canvasH, state.cropY1));
            const x2 = Math.max(x1 + 10, Math.min(state.canvasW, state.cropX2));
            const y2 = Math.max(y1 + 10, Math.min(state.canvasH, state.cropY2));

            // 获取裁剪区域的图片数据
            const cropImageData = state.ctx.getImageData(x1, y1, x2 - x1, y2 - y1);
            // 重新初始化Canvas为裁剪尺寸（不保存初始尺寸）
            initCanvas(x2 - x1, y2 - y1, false);
            // 绘制裁剪后的图片
            state.ctx.putImageData(cropImageData, 0, 0);
            // 更新裁剪尺寸和原始图（橡皮擦后续还原用）
            state.cropWidth = x2 - x1;
            state.cropHeight = y2 - y1;
            const tempImg = new Image();
            tempImg.onload = () => { state.originalImage = tempImg; };
            tempImg.src = getCanvasBase64();

            // 裁剪完成后隐藏裁剪框
            if (state.cropRect) state.cropRect.style.display = 'none';
            // 禁用应用裁剪按钮
            if (state.applyCropBtn) state.applyCropBtn.disabled = true;
            // 重置裁剪选择状态
            state.isCropSelected = false;

            // 发送裁剪后数据到后端
            sendToParent(true);
            setStatus(\`✅ 裁剪完成 | 新尺寸: \${state.cropWidth}x\${state.cropHeight}\`);
        }

        // ==============================================
        // 清除功能：完全清除画布上的所有内容（包括上传的图片）
        // ==============================================
        function execClear() {
            // 完全清空画布，填充白色背景
            state.ctx.fillStyle = '#ffffff';
            state.ctx.fillRect(0, 0, state.canvasW, state.canvasH);
            
            // 清除所有状态
            state.isUploaded = false;
            state.originalImage = null;
            state.tempImageData = null;
            state.cropWidth = state.canvasW;
            state.cropHeight = state.canvasH;
            
            // 创建新的空白背景图片用于橡皮擦
            const blankCanvas = document.createElement('canvas');
            blankCanvas.width = state.canvasW;
            blankCanvas.height = state.canvasH;
            const blankCtx = blankCanvas.getContext('2d');
            blankCtx.fillStyle = '#ffffff';
            blankCtx.fillRect(0, 0, state.canvasW, state.canvasH);
            state.originalImage = new Image();
            state.originalImage.src = blankCanvas.toDataURL();
            
            sendToParent(false);
            setStatus(\`🧹 画布已完全清除 | 所有内容已清空\`);
        }

        // ==============================================
        // 重置功能：恢复到初始画布尺寸
        // ==============================================
        function execReset() {
            // 如果尺寸没有变化，不需要重置
            if (state.canvasW === state.initialW && state.canvasH === state.initialH) {
                setStatus(\`ℹ️ 画布尺寸已是初始尺寸 (\${state.initialW}x\${state.initialH})\`);
                return;
            }

            // 保存当前画布内容
            let savedImage = null;
            if (state.canvas) {
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = state.canvasW;
                tempCanvas.height = state.canvasH;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.drawImage(state.canvas, 0, 0);
                savedImage = tempCanvas.toDataURL();
            }

            // 重新初始化为初始尺寸（不保存初始尺寸，保持原有值）
            initCanvas(state.initialW, state.initialH, false);

                    // 如果有保存的图像内容，重新绘制（适应新尺寸）
                    if (savedImage) {
                        const img = new Image();
                        img.onload = () => {
                            // 计算缩放以适应新尺寸
                            const scaleX = state.canvasW / state.initialW;
                            const scaleY = state.canvasH / state.initialH;
                            const scale = Math.min(scaleX, scaleY, 1);
                            const drawW = state.initialW * scale;
                            const drawH = state.initialH * scale;
                            const offsetX = (state.canvasW - drawW) / 2;
                            const offsetY = (state.canvasH - drawH) / 2;
                            state.ctx.drawImage(img, offsetX, offsetY, drawW, drawH);

                            // 更新临时数据
                            state.tempImageData = state.ctx.getImageData(0, 0, state.canvasW, state.canvasH);
                            // 重置后更新尺寸widget
                            sendToParent(true);
                        };
                        img.src = savedImage;
                    } else {
                        // 重置后更新尺寸widget
                        sendToParent(true);
                    }

            state.cropWidth = state.initialW;
            state.cropHeight = state.initialH;

            // 隐藏裁剪框
            if (state.cropRect) state.cropRect.style.display = 'none';
            if (state.applyCropBtn) state.applyCropBtn.disabled = true;
            state.isCropSelected = false;

            setStatus(\`🔄 已重置为初始尺寸 | \${state.initialW}x\${state.initialH}\`);
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
        // 液化工具：像素跟随鼠标移动（方向完全一致，中心最强）
        // ==============================================
        function execLiquify(x, y) {
            if (!state.tempImageData || !state.canvas || !state.lastLiquifyPos) return;
            const size = state.drawSize;
            const strength = state.liquifyStrength;
            const imgData = state.ctx.getImageData(0, 0, state.canvasW, state.canvasH);
            const pixels = imgData.data;
            const width = state.canvasW;
            const height = state.canvasH;
            // 计算鼠标移动向量
            const dxMove = x - state.lastLiquifyPos.x;
            const dyMove = y - state.lastLiquifyPos.y;
            const moveDist = Math.sqrt(dxMove * dxMove + dyMove * dyMove);
            if (moveDist < 0.1) return; // 移动过小时不执行，优化性能
            const radiusSq = size * size;
            // 遍历液化画笔范围内的所有像素
            for (let dy = -size; dy <= size; dy++) {
                for (let dx = -size; dx <= size; dx++) {
                    const currX = Math.floor(x + dx);
                    const currY = Math.floor(y + dy);
                    // 边界检查，避免越界
                    if (currX < 0 || currX >= width || currY < 0 || currY >= height) continue;
                    // 计算到圆心的距离平方，判断是否在画笔范围内
                    const distSq = dx * dx + dy * dy;
                    if (distSq > radiusSq) continue;
                    // 圆形衰减计算：圆心1.0 → 边缘0.0，平方衰减更自然
                    const decay = 1.0 - (distSq / radiusSq);
                    const finalStrength = strength * decay;
                    // 像素偏移量（与鼠标移动方向完全一致）
                    const offsetX = dxMove * finalStrength;
                    const offsetY = dyMove * finalStrength;
                    // 修正源像素坐标：保证像素跟随鼠标移动
                    const srcX = Math.floor(currX - offsetX);
                    const srcY = Math.floor(currY - offsetY);
                    // 源像素边界检查
                    if (srcX < 0 || srcX >= width || srcY < 0 || srcY >= height) continue;
                    // 赋值像素（RGBA四通道）
                    const srcIdx = (srcY * width + srcX) * 4;
                    const tarIdx = (currY * width + currX) * 4;
                    pixels[tarIdx] = state.tempImageData.data[srcIdx];
                    pixels[tarIdx + 1] = state.tempImageData.data[srcIdx + 1];
                    pixels[tarIdx + 2] = state.tempImageData.data[srcIdx + 2];
                    pixels[tarIdx + 3] = state.tempImageData.data[srcIdx + 3];
                }
            }
            // 将变形后的像素写回Canvas
            state.ctx.putImageData(imgData, 0, 0);
            // 更新临时图片数据（下次操作基于最新状态）
            state.tempImageData = state.ctx.getImageData(0, 0, width, height);
            // 更新上一帧液化位置
            state.lastLiquifyPos = {x, y};
        }

        // ==============================================
        // 橡皮擦工具：流畅连续擦除，恢复原始图片或绘制白色
        // ==============================================
        function execErase(x, y, isContinuous = false) {
            if (!state.canvas) return;

            const size = state.drawSize;
            const halfSize = size / 2;

            if (state.isUploaded && state.originalImage) {
                // 有上传图片：恢复原始图片内容
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
            } else {
                // 没有上传图片：绘制白色擦除画笔痕迹
                state.ctx.save();
                state.ctx.beginPath();
                state.ctx.fillStyle = '#ffffff';
                if (isContinuous) {
                    state.ctx.arc(x, y, halfSize, 0, Math.PI * 2);
                    state.ctx.fill();
                } else {
                    state.ctx.arc(x, y, halfSize, 0, Math.PI * 2);
                    state.ctx.fill();
                }
                state.ctx.restore();
            }
        }

        // ==============================================
        // 初始化事件监听：所有交互逻辑绑定
        // ==============================================
        function initEvent() {
            // 1. 上传图片
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
                        // 不保存初始尺寸，不保留原有内容，完全按照图片大小调整画布
                        initCanvas(img.width, img.height, false, false);
                        state.ctx.drawImage(img, 0, 0);
                        state.originalImage = img;
                        state.tempImageData = state.ctx.getImageData(0, 0, img.width, img.height);
                        state.isUploaded = true;
                        state.cropWidth = img.width;
                        state.cropHeight = img.height;
                        // 上传图片后更新尺寸widget
                        sendToParent(true);
                        setStatus(\`✅ 图片上传成功 | 原始尺寸: \${img.width}x\${img.height}\`);
                    };
                    img.src = ev.target.result;
                };
                reader.readAsDataURL(file);
            });

            // 2. 工具按钮点击
            document.getElementById('crop-btn').onclick = () => switchTool('crop');
            document.getElementById('draw-btn').onclick = () => switchTool('draw');
            document.getElementById('liquify-btn').onclick = () => switchTool('liquify');
            document.getElementById('erase-btn').onclick = () => switchTool('erase');

            // 3. 新增：应用裁剪按钮点击事件
            document.getElementById('apply-crop-btn').addEventListener('click', () => {
                execCrop();
            });

            // 3.1 清除按钮点击事件
            document.getElementById('clear-btn').addEventListener('click', () => {
                execClear();
            });

            // 3.2 重置按钮点击事件
            document.getElementById('reset-btn').addEventListener('click', () => {
                execReset();
            });

            // 4. 画笔参数调节（实时更新）
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
                // 所有绘画类工具共用同一个大小
                if (state.currentTool === 'draw' || state.currentTool === 'liquify' || state.currentTool === 'erase') {
                    switchTool(state.currentTool);
                }
            };
            drawAlpha.oninput = (e) => {
                state.drawAlpha = parseFloat(e.target.value);
                drawAlphaVal.textContent = state.drawAlpha.toFixed(1);
                switchTool('draw');
            };

            // 5. 液化参数调节（实时更新，使用统一画笔大小）
            const liquifyStrength = document.getElementById('liquify-strength');
            const liquifyStrengthVal = document.getElementById('liquify-strength-val');
            liquifyStrength.oninput = (e) => {
                state.liquifyStrength = parseFloat(e.target.value);
                liquifyStrengthVal.textContent = state.liquifyStrength.toFixed(1);
                switchTool('liquify');
            };

            // 6. 橡皮擦工具使用统一画笔大小，无需额外配置

            // 7. 鼠标移动：更新预览/裁剪框/实时操作
            document.addEventListener('mousemove', (e) => {
                // 实时更新笔触预览位置
                updateBrushPreviewPos(e.clientX, e.clientY);
                if (!state.isMouseDown) return;
                const [x, y] = getCanvasXY(e.clientX, e.clientY);
                // 根据当前工具执行对应操作
                switch(state.currentTool) {
                    case 'crop':
                        state.cropX2 = x; state.cropY2 = y;
                        updateCropRect(); // 实时更新裁剪框
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

            // 8. Canvas核心鼠标交互：按下/松开
            const canvas = document.getElementById('edit-canvas');
            // 鼠标按下
            canvas.addEventListener('mousedown', (e) => {
                e.preventDefault();
                state.isMouseDown = true;
                const [x, y] = getCanvasXY(e.clientX, e.clientY);
                switch(state.currentTool) {
                    case 'crop':
                        // 初始化裁剪坐标，标记已选择裁剪区域
                        state.cropX1 = x; state.cropY1 = y;
                        state.cropX2 = x; state.cropY2 = y;
                        state.isCropSelected = true;
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

            // 鼠标松开：仅停止操作，不再自动裁剪
            document.addEventListener('mouseup', () => {
                if (!state.isMouseDown) return;
                state.isMouseDown = false;
                switch(state.currentTool) {
                    case 'crop':
                        // 裁剪工具松开鼠标仅更新裁剪框，不执行裁剪
                        updateCropRect();
                        break;
                    case 'draw':
                    case 'liquify':
                    case 'erase':
                        sendToParent(false); // 发送编辑后数据，不更新尺寸
                        break;
                }
            });

            // 9. 鼠标进入画布：恢复绘制状态（修复鼠标离开画布后绘制中断的问题）
            canvas.addEventListener('mouseenter', (e) => {
                if (e.buttons === 1 && state.isMouseDown === false &&
                    (state.currentTool === 'draw' || state.currentTool === 'liquify' || state.currentTool === 'erase')) {
                    state.isMouseDown = true;
                    const [x, y] = getCanvasXY(e.clientX, e.clientY);
                    if (state.currentTool === 'draw') {
                        initDrawStyle();
                        state.ctx.moveTo(x, y);
                    } else if (state.currentTool === 'liquify') {
                        state.tempImageData = state.ctx.getImageData(0, 0, state.canvasW, state.canvasH);
                        state.lastLiquifyPos = {x, y};
                    } else if (state.currentTool === 'erase') {
                        execErase(x, y, false);
                    }
                }
            });

            // 10. 窗口大小变化：重新适配
            window.addEventListener('resize', () => {
                state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
                updateCanvasScale();
                updateBrushPreviewSize();
                // 窗口变化时更新裁剪框位置
                if (state.currentTool === 'crop' && state.isCropSelected) {
                    updateCropRect();
                }
            });

            // 11. ResizeObserver：监听容器大小变化，精准适配
            if (window.ResizeObserver) {
                state.resizeObserver = new ResizeObserver(() => {
                    state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
                    updateCanvasScale();
                    updateBrushPreviewSize();
                    // 容器变化时更新裁剪框位置
                    if (state.currentTool === 'crop' && state.isCropSelected) {
                        updateCropRect();
                    }
                });
                state.resizeObserver.observe(document.getElementById('canvas-container'));
            }
        }

        // ==============================================
        // 初始化：执行事件绑定+基础画布创建
        // ==============================================
        window.onload = () => {
            // 不保存初始尺寸，等待 INIT_CANVAS 消息从 widget 获取正确尺寸
            initCanvas(512, 512, false);
            initEvent();
            // 通知父窗口Canvas就绪
            setTimeout(() => {
                window.parent.postMessage({type: 'DRAW_CANVAS_READY'}, '*');
            }, 100);
        };

        // ==============================================
        // 清理资源：页面卸载时释放
        // ==============================================
        window.addEventListener('unload', () => {
            if (state.resizeObserver) state.resizeObserver.disconnect();
        });

        // ==============================================
        // 监听父窗口消息：接收Canvas初始化/缩放指令
        // ==============================================
        window.addEventListener('message', (e) => {
            try {
                if (e.data.type === 'INIT_CANVAS') {
                    // 保存初始尺寸
                    initCanvas(e.data.width || 512, e.data.height || 512, true);
                } else if (e.data.type === 'RESIZE_CANVAS') {
                    state.toolbarHeight = document.getElementById('main-toolbar').offsetHeight;
                    updateCanvasScale();
                    updateBrushPreviewSize();
                    // 响应父窗口缩放指令时更新裁剪框
                    if (state.currentTool === 'crop' && state.isCropSelected) {
                        updateCropRect();
                    }
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
    name: "luy.imageEditCropApplyBtn",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "ImageEditNode") {
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

console.log("✅ 带应用裁剪按钮的图片编辑节点扩展加载完成（luy分类）");