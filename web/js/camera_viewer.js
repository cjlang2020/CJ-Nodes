const currentOrigin = window.location.origin+"/extensions/CJ-Nodes/js/three.min.js"
export const VIEWER_HTML = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            width: 100%;
            height: 100vh;
            overflow: hidden;
            background: radial-gradient(circle, #555555 0%, #2a2a2a 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        #container {
            width: 100%;
            height: 100%;
            position: relative;
        }

        #threejs-container {
            width: 100%;
            height: 100%;
        }

        #prompt-preview {
            position: absolute;
            top: 8px;
            left: 8px;
            right: 8px;
            background: rgba(10, 10, 15, 0.9);
            border: 1px solid rgba(233, 61, 130, 0.3);
            border-radius: 6px;
	padding: 6px 10px;
            font-size: 11px;
            color: #E93D82;
            backdrop-filter: blur(4px);
            font-family: 'Consolas', 'Monaco', monospace;
            word-break: break-all;
            line-height: 1.4;
        }

        #info-panel {
            position: absolute;
            bottom: 8px;
            left: 8px;
            right: 8px;
            background: rgba(10, 10, 15, 0.9);
            border: 1px solid rgba(233, 61, 130, 0.3);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            color: #e0e0e0;
            display: flex;
            justify-content: space-around;
            backdrop-filter: blur(4px);
        }

        .param-item {
            text-align: center;
        }

        .param-label {
            color: #888;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .param-value {
            color: #E93D82;
            font-weight: 600;
            font-size: 13px;
        }

        .param-value.elevation {
            color: #00FFD0;
        }

        .param-value.zoom {
            color: #FFB800;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="threejs-container"></div>
        <div id="prompt-preview">front view, eye level, medium shot</div>
        <div id="info-panel">
            <div class="param-item">
                <div class="param-label">水平</div>
                <div class="param-value" id="h-value">0°</div>
            </div>
            <div class="param-item">
                <div class="param-label">垂直</div>
                <div class="param-value elevation" id="v-value">0°</div>
            </div>
            <div class="param-item">
                <div class="param-label">远近</div>
                <div class="param-value zoom" id="z-value">5.0</div>
            </div>
        </div>
    </div>

    <script src="${currentOrigin}"></script>
    <script>
        let state = {
            azimuth: 0,
            elevation: 0,
            distance: 5,
            imageUrl: null
        };

        let threeScene = null;
        const BASE_PANEL_HEIGHT = 1.2;
        const PANEL_FRONT_COLOR = 0xAAAAAA;
        const PANEL_BACK_COLOR = 0xFFFFFF;
        const GRID_COLOR = 0xAAAAAA;
        let backTextTexture = null;

        const container = document.getElementById('threejs-container');
        const hValueEl = document.getElementById('h-value');
        const vValueEl = document.getElementById('v-value');
        const zValueEl = document.getElementById('z-value');
        const promptPreviewEl = document.getElementById('prompt-preview');

        function createBackTextTexture() {
            const canvas = document.createElement('canvas');
            canvas.width = 512;
            canvas.height = 512;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.translate(canvas.width / 2, canvas.height / 2);
            ctx.scale(-1, 1);
            ctx.translate(-canvas.width / 2, -canvas.height / 2);
            ctx.fillStyle = '#000000';
            ctx.font = 'bold 60px Microsoft YaHei, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('X_X', canvas.width / 2, canvas.height / 2);
            const texture = new THREE.CanvasTexture(canvas);
            texture.needsUpdate = true;
            texture.flipY = false;
            return texture;
        }

        function generatePromptPreview() {
            const h_angle = state.azimuth % 360;
            let h_direction;
            if (h_angle < 22.5 || h_angle >= 337.5) {
                h_direction = "front view";
            } else if (h_angle < 67.5) {
                h_direction = "front-right view";
            } else if (h_angle < 112.5) {
                h_direction = "right side view";
            } else if (h_angle < 157.5) {
                h_direction = "back-right view";
            } else if (h_angle < 202.5) {
                h_direction = "back view";
            } else if (h_angle < 247.5) {
                h_direction = "back-left view";
            } else if (h_angle < 292.5) {
                h_direction = "left side view";
            } else {
                h_direction = "front-left view";
            }

            let v_direction;
            if (state.elevation < -15) {
                v_direction = "low angle";
            } else if (state.elevation < 15) {
                v_direction = "eye level";
            } else if (state.elevation < 45) {
                v_direction = "high angle";
            } else if (state.elevation < 75) {
                v_direction = "bird's eye view";
            } else {
                v_direction = "top-down view";
            }

            // ========== 核心修改：完全反转 zoom(distance) 和镜头提示词的映射关系 ==========
            let distance;
            if (state.distance < 2) {
                distance = "close-up";          // 数值最小 → 镜头最近 → 特写
            } else if (state.distance < 4) {
                distance = "medium close-up";   // 数值偏小 → 镜头较近 → 中特写
            } else if (state.distance < 6) {
                distance = "medium shot";       // 数值中等 → 镜头适中 → 中景
            } else if (state.distance < 8) {
                distance = "medium-wide shot";  // 数值偏大 → 镜头较远 → 中全景
            } else {
                distance = "wide shot";         // 数值最大 → 镜头最远 → 全景
            }

            return h_direction + ", " + v_direction + ", " + distance;
        }

        function updateDisplay() {
            hValueEl.textContent = Math.round(state.azimuth) + '°';
            vValueEl.textContent = Math.round(state.elevation) + '°';
            zValueEl.textContent = state.distance.toFixed(1);
            promptPreviewEl.textContent = generatePromptPreview();
        }

        function sendAngleUpdate() {
            window.parent.postMessage({
                type: 'ANGLE_UPDATE',
                horizontal: Math.round(state.azimuth),
                vertical: Math.round(state.elevation),
                zoom: Math.round(state.distance * 10) / 10
            }, '*');
        }

        function initThreeJS() {
            const width = container.clientWidth;
            const height = container.clientHeight;
            backTextTexture = createBackTextTexture();

            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x2a2a2a);

            const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);

            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);

            const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
            scene.add(ambientLight);
            const frontLight = new THREE.DirectionalLight(0xffffff, 1.5);
            frontLight.position.set(0, 1, 5);
            scene.add(frontLight);
            const topLight = new THREE.DirectionalLight(0xffffff, 1.2);
            topLight.position.set(0, 5, 0);
            scene.add(topLight);
            const leftLight = new THREE.DirectionalLight(0xffffff, 1.0);
            leftLight.position.set(-5, 1, 0);
            scene.add(leftLight);
            const rightLight = new THREE.DirectionalLight(0xffffff, 1.0);
            rightLight.position.set(5, 1, 0);
            scene.add(rightLight);

            const gridHelper = new THREE.GridHelper(6, 24, GRID_COLOR, GRID_COLOR);
            gridHelper.position.y = -0.01;
            scene.add(gridHelper);

            const frontPlaneGeo = new THREE.PlaneGeometry(BASE_PANEL_HEIGHT, BASE_PANEL_HEIGHT);
            const frontPlaneMat = new THREE.MeshLambertMaterial({
                color: PANEL_FRONT_COLOR,
                side: THREE.FrontSide,
                transparent: false
            });
            const frontImagePlane = new THREE.Mesh(frontPlaneGeo, frontPlaneMat);
            frontImagePlane.position.set(0, BASE_PANEL_HEIGHT / 2, 0);
            scene.add(frontImagePlane);

            const backPlaneGeo = new THREE.PlaneGeometry(BASE_PANEL_HEIGHT, BASE_PANEL_HEIGHT);
            const backPlaneMat = new THREE.MeshBasicMaterial({
                color: PANEL_BACK_COLOR,
                map: backTextTexture,
                side: THREE.BackSide,
                transparent: false
            });
            const backImagePlane = new THREE.Mesh(backPlaneGeo, backPlaneMat);
            backImagePlane.position.copy(frontImagePlane.position);
            scene.add(backImagePlane);

            let isRendering = false;
            const render = () => {
                if (isRendering) return;
                isRendering = true;
                requestAnimationFrame(() => {
                    renderer.render(scene, camera);
                    isRendering = false;
                });
            };

            function updateCameraPosition() {
                const azRad = THREE.MathUtils.degToRad(state.azimuth);
                const elRad = THREE.MathUtils.degToRad(state.elevation);
                const lookAtPoint = frontImagePlane.position;

                camera.position.x = lookAtPoint.x + state.distance * Math.sin(azRad) * Math.cos(elRad);
                camera.position.y = lookAtPoint.y + state.distance * Math.sin(elRad);
                camera.position.z = lookAtPoint.z + state.distance * Math.cos(azRad) * Math.cos(elRad);

                camera.lookAt(lookAtPoint);
                render();
            }

            function updatePanelByImageRatio(imgW, imgH) {
                const imgAspect = imgW / imgH;
                const panelWidth = BASE_PANEL_HEIGHT * imgAspect;
                frontImagePlane.geometry.dispose();
                frontImagePlane.geometry = new THREE.PlaneGeometry(panelWidth, BASE_PANEL_HEIGHT);
                backImagePlane.geometry.dispose();
                backImagePlane.geometry = new THREE.PlaneGeometry(panelWidth, BASE_PANEL_HEIGHT);
                updateCameraPosition();
            }

            let isMouseDown = false;
            let lastMouseX = 0;
            let lastMouseY = 0;
            const rotateSensitivity = 0.7;
            const zoomSensitivity = 0.005;

            function onMouseDown(event) {
                isMouseDown = true;
                lastMouseX = event.clientX;
                lastMouseY = event.clientY;
                renderer.domElement.style.cursor = 'grabbing';
                event.preventDefault();
            }

            function onMouseMove(event) {
                if (!isMouseDown) return;

                const deltaX = event.clientX - lastMouseX;
                const deltaY = event.clientY - lastMouseY;

                state.azimuth -= deltaX * rotateSensitivity;
                state.azimuth %= 360;
                if (state.azimuth < 0) state.azimuth += 360;

                state.elevation += deltaY * rotateSensitivity;
                state.elevation = THREE.MathUtils.clamp(state.elevation, -30, 90);

                updateDisplay();
                updateCameraPosition();
                sendAngleUpdate();

                lastMouseX = event.clientX;
                lastMouseY = event.clientY;
            }

            function onMouseUp() {
                isMouseDown = false;
                renderer.domElement.style.cursor = 'grab';
            }

            function onMouseWheel(event) {
                event.preventDefault();
                const delta = event.deltaY || -event.detail;
                state.distance += delta * zoomSensitivity;
                state.distance = THREE.MathUtils.clamp(state.distance, 0.5, 10);

                updateDisplay();
                updateCameraPosition();
                sendAngleUpdate();
            }

            renderer.domElement.addEventListener('mousedown', onMouseDown);
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            document.addEventListener('mouseleave', onMouseUp);
            renderer.domElement.addEventListener('wheel', onMouseWheel, { passive: false });
            renderer.domElement.addEventListener('DOMMouseScroll', onMouseWheel, { passive: false });

            renderer.domElement.addEventListener('touchstart', (e) => {
                e.preventDefault();
                onMouseDown({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
            }, { passive: false });
            renderer.domElement.addEventListener('touchmove', (e) => {
                e.preventDefault();
                onMouseMove({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
            }, { passive: false });
            renderer.domElement.addEventListener('touchend', onMouseUp);

            function onResize() {
                const w = container.clientWidth;
                const h = container.clientHeight;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
                render();
            }
            window.addEventListener('resize', onResize);

            threeScene = {
                syncFromState: () => {
                    updateDisplay();
                    updateCameraPosition();
                },
                updateImage: (url) => {
                    if (url) {
                        const img = new Image();
                        if (!url.startsWith('data:')) img.crossOrigin = 'anonymous';

                        img.onload = () => {
                            const tex = new THREE.Texture(img);
                            tex.needsUpdate = true;
                            tex.encoding = THREE.sRGBEncoding;
                            frontPlaneMat.map = tex;
                            frontPlaneMat.needsUpdate = true;
                            updatePanelByImageRatio(img.width, img.height);
                        };

                        img.onerror = () => {
                            frontPlaneMat.map = null;
                            frontPlaneMat.color.set(0xFF0000);
                            frontPlaneMat.needsUpdate = true;
                            frontImagePlane.geometry.dispose();
                            frontImagePlane.geometry = new THREE.PlaneGeometry(BASE_PANEL_HEIGHT, BASE_PANEL_HEIGHT);
                            backImagePlane.geometry.dispose();
                            backImagePlane.geometry = new THREE.PlaneGeometry(BASE_PANEL_HEIGHT, BASE_PANEL_HEIGHT);
                        };
                        img.src = url;
                    } else {
                        frontPlaneMat.map = null;
                        frontPlaneMat.color.set(PANEL_FRONT_COLOR);
                        frontPlaneMat.needsUpdate = true;
                        frontImagePlane.geometry.dispose();
                        frontImagePlane.geometry = new THREE.PlaneGeometry(BASE_PANEL_HEIGHT, BASE_PANEL_HEIGHT);
                        backImagePlane.geometry.dispose();
                        backImagePlane.geometry = new THREE.PlaneGeometry(BASE_PANEL_HEIGHT, BASE_PANEL_HEIGHT);
                        render();
                    }
                }
            };
            updateCameraPosition();
        }

        window.addEventListener('message', (event) => {
            const data = event.data;
            if (data.type === 'INIT' || data.type === 'SYNC_ANGLES') {
                state.azimuth = data.horizontal || 0;
                state.elevation = data.vertical || 0;
                state.distance = data.zoom || 5;
                threeScene?.syncFromState();
            } else if (data.type === 'UPDATE_IMAGE') {
                state.imageUrl = data.imageUrl;
                threeScene?.updateImage(data.imageUrl);
            }
        });

        initThreeJS();
        updateDisplay();
        window.parent.postMessage({ type: 'VIEWER_READY' }, '*');
    </script>
</body>
</html>
`;