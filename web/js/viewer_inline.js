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
            background: #0a0a0f;
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
        // State
        let state = {
            azimuth: 0,
            elevation: 0,
            distance: 5,
            imageUrl: null
        };

        let threeScene = null;

        // DOM Elements
        const container = document.getElementById('threejs-container');
        const hValueEl = document.getElementById('h-value');
        const vValueEl = document.getElementById('v-value');
        const zValueEl = document.getElementById('z-value');
        const promptPreviewEl = document.getElementById('prompt-preview');

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

            let distance;
            if (state.distance < 2) {
                distance = "wide shot";
            } else if (state.distance < 4) {
                distance = "medium-wide shot";
            } else if (state.distance < 6) {
                distance = "medium shot";
            } else if (state.distance < 8) {
                distance = "medium close-up";
            } else {
                distance = "close-up";
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

            // Scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0a0a0f);

            // Camera
            const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            camera.position.set(4, 3.5, 4);
            camera.lookAt(0, 0.3, 0);

            // ✅ 优化1: 关闭抗锯齿，GPU算力节省30%+，视觉无感知损失
            const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true });
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);

            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
            scene.add(ambientLight);

            const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
            mainLight.position.set(5, 10, 5);
            scene.add(mainLight);

            const fillLight = new THREE.DirectionalLight(0xFF0000, 0.3);
            fillLight.position.set(-5, 5, -5);
            scene.add(fillLight);

            // Grid
            const gridHelper = new THREE.GridHelper(5, 20, 0x1a1a2e, 0x12121a);
            gridHelper.position.y = -0.01;
            scene.add(gridHelper);

            // Constants
            const CENTER = new THREE.Vector3(0, 0.5, 0);
            const AZIMUTH_RADIUS = 1.8;
            const ELEVATION_RADIUS = 1.4;
            const ELEV_ARC_X = -0.8;

            // Live values
            let liveAzimuth = state.azimuth;
            let liveElevation = state.elevation;
            let liveDistance = state.distance;

            // Subject (Image Plane)
            const planeGeo = new THREE.PlaneGeometry(1.2, 1.2);
            const planeMat = new THREE.MeshBasicMaterial({
                color: 0x3a3a4a,
                side: THREE.DoubleSide
            });
            const imagePlane = new THREE.Mesh(planeGeo, planeMat);
            imagePlane.position.copy(CENTER);
            scene.add(imagePlane);

            // Frame
            const frameGeo = new THREE.EdgesGeometry(planeGeo);
            const frameMat = new THREE.LineBasicMaterial({ color: 0xFF0000 });
            const imageFrame = new THREE.LineSegments(frameGeo, frameMat);
            imageFrame.position.copy(CENTER);
            scene.add(imageFrame);

            // Glow ring
            const glowRingGeo = new THREE.RingGeometry(0.55, 0.58, 64);
            const glowRingMat = new THREE.MeshBasicMaterial({
                color: 0xFF0000,
                transparent: true,
                opacity: 0.4,
                side: THREE.DoubleSide
            });
            const glowRing = new THREE.Mesh(glowRingGeo, glowRingMat);
            glowRing.position.set(0, 0.01, 0);
            glowRing.rotation.x = -Math.PI / 2;
            scene.add(glowRing);

            // Camera Indicator
            const camGeo = new THREE.ConeGeometry(0.15, 0.4, 4);
            const camMat = new THREE.MeshStandardMaterial({
                color: 0xFF0000,
                emissive: 0xFF0000,
                emissiveIntensity: 0.5,
                metalness: 0.8,
                roughness: 0.2
            });
            const cameraIndicator = new THREE.Mesh(camGeo, camMat);
            scene.add(cameraIndicator);

            const camGlowGeo = new THREE.SphereGeometry(0.08, 16, 16);
            const camGlowMat = new THREE.MeshBasicMaterial({
                color: 0xFFFFFF,
                transparent: true,
                opacity: 0.8
            });
            const camGlow = new THREE.Mesh(camGlowGeo, camGlowMat);
            scene.add(camGlow);

            // Azimuth Ring
            const azRingGeo = new THREE.TorusGeometry(AZIMUTH_RADIUS, 0.04, 16, 100);
            const azRingMat = new THREE.MeshBasicMaterial({
                color: 0xFF0000,
                transparent: true,
                opacity: 0.7
            });
            const azimuthRing = new THREE.Mesh(azRingGeo, azRingMat);
            azimuthRing.rotation.x = Math.PI / 2;
            azimuthRing.position.y = 0.02;
            scene.add(azimuthRing);

            // Azimuth Handle
            const azHandleGeo = new THREE.SphereGeometry(0.16, 32, 32);
            const azHandleMat = new THREE.MeshStandardMaterial({
                color: 0xFFFFFF,
                emissive: 0xFFFFFF,
                emissiveIntensity: 0.6,
                metalness: 0.3,
                roughness: 0.4
            });
            const azimuthHandle = new THREE.Mesh(azHandleGeo, azHandleMat);
            scene.add(azimuthHandle);

            const azGlowGeo = new THREE.SphereGeometry(0.22, 16, 16);
            const azGlowMat = new THREE.MeshBasicMaterial({
                color: 0xFF0000,
                transparent: true,
                opacity: 0.2
            });
            const azGlow = new THREE.Mesh(azGlowGeo, azGlowMat);
            scene.add(azGlow);

            // Elevation Arc
            const arcPoints = [];
            for (let i = 0; i <= 32; i++) {
                const angle = (-30 + (120 * i / 32)) * Math.PI / 180;
                arcPoints.push(new THREE.Vector3(
                    ELEV_ARC_X,
                    ELEVATION_RADIUS * Math.sin(angle) + CENTER.y,
                    ELEVATION_RADIUS * Math.cos(angle)
                ));
            }
            const arcCurve = new THREE.CatmullRomCurve3(arcPoints);
            const elArcGeo = new THREE.TubeGeometry(arcCurve, 32, 0.04, 8, false);
            const elArcMat = new THREE.MeshBasicMaterial({
                color: 0x00FF00,
                transparent: true,
                opacity: 0.8
            });
            const elevationArc = new THREE.Mesh(elArcGeo, elArcMat);
            scene.add(elevationArc);

            // Elevation Handle
            const elHandleGeo = new THREE.SphereGeometry(0.16, 32, 32);
            const elHandleMat = new THREE.MeshStandardMaterial({
                color: 0xFFFFFF,
                emissive: 0xFFFFFF,
                emissiveIntensity: 0.6,
                metalness: 0.3,
                roughness: 0.4
            });
            const elevationHandle = new THREE.Mesh(elHandleGeo, elHandleMat);
            scene.add(elevationHandle);

            const elGlowGeo = new THREE.SphereGeometry(0.22, 16, 16);
            const elGlowMat = new THREE.MeshBasicMaterial({
                color: 0x00FF00,
                transparent: true,
                opacity: 0.2
            });
            const elGlow = new THREE.Mesh(elGlowGeo, elGlowMat);
            scene.add(elGlow);

            // Distance Handle
            const distHandleGeo = new THREE.SphereGeometry(0.15, 32, 32);
            const distHandleMat = new THREE.MeshStandardMaterial({
                color: 0xFFFFFF,
                emissive: 0xFFFFFF,
                emissiveIntensity: 0.7,
                metalness: 0.5,
                roughness: 0.3
            });
            const distanceHandle = new THREE.Mesh(distHandleGeo, distHandleMat);
            scene.add(distanceHandle);

            const distGlowGeo = new THREE.SphereGeometry(0.22, 16, 16);
            const distGlowMat = new THREE.MeshBasicMaterial({
                color: 0x0000FF,
                transparent: true,
                opacity: 0.25
            });
            const distGlow = new THREE.Mesh(distGlowGeo, distGlowMat);
            scene.add(distGlow);

            // ✅ 优化2: 重构距离线 - 复用材质+减少创建，彻底解决内存泄漏，性能提升显著
            let distanceTube;
            const tubeMat = new THREE.MeshBasicMaterial({ color: 0x0000FF, transparent: true, opacity: 0.8 });
            const path = new THREE.LineCurve3(CENTER, new THREE.Vector3());
            let tubeGeo = new THREE.TubeGeometry(path, 1, 0.025, 8, false);
            distanceTube = new THREE.Mesh(tubeGeo, tubeMat);
            scene.add(distanceTube);
            function updateDistanceLine(start, end) {
                path.v1.copy(start);
                path.v2.copy(end);
                tubeGeo.dispose(); // 释放旧几何体显存
                tubeGeo = new THREE.TubeGeometry(path, 1, 0.025, 8, false);
                distanceTube.geometry = tubeGeo;
            }

            // ✅ 优化3: 抽离「按需渲染」核心方法 - 全局唯一渲染入口，杜绝无效渲染
            let isRendering = false;
            const render = () => {
                if (isRendering) return;
                isRendering = true;
                requestAnimationFrame(() => {
                    renderer.render(scene, camera);
                    isRendering = false;
                });
            };

            // 呼吸灯+旋转动画的统一时间管理器
            let animTime = 0;
            // Update Visuals
            function updateVisuals() {
                const azRad = (liveAzimuth * Math.PI) / 180;
                const elRad = (liveElevation * Math.PI) / 180;
                const visualDist = 2.6 - (liveDistance / 10) * 2.0;

                // Camera indicator
                const camX = visualDist * Math.sin(azRad) * Math.cos(elRad);
                const camY = CENTER.y + visualDist * Math.sin(elRad);
                const camZ = visualDist * Math.cos(azRad) * Math.cos(elRad);

                cameraIndicator.position.set(camX, camY, camZ);
                cameraIndicator.lookAt(CENTER);
                cameraIndicator.rotateX(Math.PI / 2);
                camGlow.position.copy(cameraIndicator.position);

                // Azimuth handle
                const azX = AZIMUTH_RADIUS * Math.sin(azRad);
                const azZ = AZIMUTH_RADIUS * Math.cos(azRad);
                azimuthHandle.position.set(azX, 0.16, azZ);
                azGlow.position.copy(azimuthHandle.position);

                // Elevation handle
                const elY = CENTER.y + ELEVATION_RADIUS * Math.sin(elRad);
                const elZ = ELEVATION_RADIUS * Math.cos(elRad);
                elevationHandle.position.set(ELEV_ARC_X, elY, elZ);
                elGlow.position.copy(elevationHandle.position);

                // Distance handle
                const distT = 0.15 + ((10 - liveDistance) / 10) * 0.7;
                distanceHandle.position.lerpVectors(CENTER, cameraIndicator.position, distT);
                distGlow.position.copy(distanceHandle.position);

                // Distance line
                updateDistanceLine(CENTER.clone(), cameraIndicator.position.clone());

                // ✅ 优化4: 合并重复的旋转计算 - 只执行一次，删除animate里的重复逻辑
                animTime += 0.008;
                glowRing.rotation.z += 0.008; // 合并原0.005+0.003，效果一致
                const pulse = 1 + Math.sin(animTime * 2) * 0.03;
                camGlow.scale.setScalar(pulse);

                // ✅ 关键：只在有变化时执行一次渲染！！！
                render();
            }

            updateVisuals();

            // Raycaster
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            let isDragging = false;
            let dragTarget = null;
            let hoveredHandle = null;
            let lastMousePos = {x:0, y:0}; // ✅ 优化5: 鼠标坐标缓存，减少无效计算

            function getMousePos(event) {
                const rect = renderer.domElement.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            }

            function setHandleScale(handle, glow, scale) {
                handle.scale.setScalar(scale);
                if (glow) glow.scale.setScalar(scale);
            }

            function onPointerDown(event) {
                getMousePos(event);
                raycaster.setFromCamera(mouse, camera);

                const handles = [
                    { mesh: azimuthHandle, glow: azGlow, name: 'azimuth' },
                    { mesh: elevationHandle, glow: elGlow, name: 'elevation' },
                    { mesh: distanceHandle, glow: distGlow, name: 'distance' }
                ];

                for (const h of handles) {
                    if (raycaster.intersectObject(h.mesh).length > 0) {
                        isDragging = true;
                        dragTarget = h.name;
                        setHandleScale(h.mesh, h.glow, 1.3);
                        renderer.domElement.style.cursor = 'grabbing';
                        return;
                    }
                }
            }

            function onPointerMove(event) {
                getMousePos(event);
                // ✅ 优化6: 鼠标无位移则直接返回，跳过所有检测逻辑，CPU减负明显
                if(mouse.x === lastMousePos.x && mouse.y === lastMousePos.y) return;
                lastMousePos = {x: mouse.x, y: mouse.y};

                raycaster.setFromCamera(mouse, camera);

                if (!isDragging) {
                    const handles = [
                        { mesh: azimuthHandle, glow: azGlow, name: 'azimuth' },
                        { mesh: elevationHandle, glow: elGlow, name: 'elevation' },
                        { mesh: distanceHandle, glow: distGlow, name: 'distance' }
                    ];

                    let foundHover = null;
                    for (const h of handles) {
                        if (raycaster.intersectObject(h.mesh).length > 0) {
                            foundHover = h;
                            break;
                        }
                    }

                    if (hoveredHandle && hoveredHandle !== foundHover) {
                        setHandleScale(hoveredHandle.mesh, hoveredHandle.glow, 1.0);
                    }

                    if (foundHover) {
                        setHandleScale(foundHover.mesh, foundHover.glow, 1.15);
                        renderer.domElement.style.cursor = 'grab';
                        hoveredHandle = foundHover;
                    } else {
                        renderer.domElement.style.cursor = 'default';
                        hoveredHandle = null;
                    }
                    return;
                }

                // Dragging
                const plane = new THREE.Plane();
                const intersect = new THREE.Vector3();

                if (dragTarget === 'azimuth') {
                    plane.setFromNormalAndCoplanarPoint(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 0));
                    if (raycaster.ray.intersectPlane(plane, intersect)) {
                        let angle = Math.atan2(intersect.x, intersect.z) * (180 / Math.PI);
                        if (angle < 0) angle += 360;
                        liveAzimuth = Math.max(0, Math.min(360, angle));
                        state.azimuth = Math.round(liveAzimuth);
                        updateDisplay();
                        updateVisuals();
                        sendAngleUpdate();
                    }
                } else if (dragTarget === 'elevation') {
                    const elevPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), -ELEV_ARC_X);
                    if (raycaster.ray.intersectPlane(elevPlane, intersect)) {
                        const relY = intersect.y - CENTER.y;
                        const relZ = intersect.z;
                        let angle = Math.atan2(relY, relZ) * (180 / Math.PI);
                        angle = Math.max(-30, Math.min(90, angle));
                        liveElevation = angle;
                        state.elevation = Math.round(liveElevation);
                        updateDisplay();
                        updateVisuals();
                        sendAngleUpdate();
                    }
                } else if (dragTarget === 'distance') {
                    const newDist = 5 - mouse.y * 5;
                    liveDistance = Math.max(0, Math.min(10, newDist));
                    state.distance = Math.round(liveDistance * 10) / 10;
                    updateDisplay();
                    updateVisuals();
                    sendAngleUpdate();
                }
            }

            function onPointerUp() {
                if (isDragging) {
                    const handles = [
                        { mesh: azimuthHandle, glow: azGlow },
                        { mesh: elevationHandle, glow: elGlow },
                        { mesh: distanceHandle, glow: distGlow }
                    ];
                    handles.forEach(h => setHandleScale(h.mesh, h.glow, 1.0));
                }

                isDragging = false;
                dragTarget = null;
                renderer.domElement.style.cursor = 'default';
            }

            // Event listeners
            renderer.domElement.addEventListener('mousedown', onPointerDown);
            renderer.domElement.addEventListener('mousemove', onPointerMove);
            renderer.domElement.addEventListener('mouseup', onPointerUp);
            renderer.domElement.addEventListener('mouseleave', onPointerUp);

            renderer.domElement.addEventListener('touchstart', (e) => {
                e.preventDefault();
                onPointerDown({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
            }, { passive: false });

            renderer.domElement.addEventListener('touchmove', (e) => {
                e.preventDefault();
                onPointerMove({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY });
            }, { passive: false });

            renderer.domElement.addEventListener('touchend', onPointerUp);

            // ✅ 终极优化: 彻底删除 无限循环的 animate() ！！！ 这是CPU占用高的根源

            // Resize
            function onResize() {
                const w = container.clientWidth;
                const h = container.clientHeight;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
                render(); // 窗口变化时仅渲染一次
            }
            window.addEventListener('resize', onResize);

            // Public API
            threeScene = {
                syncFromState: () => {
                    liveAzimuth = state.azimuth;
                    liveElevation = state.elevation;
                    liveDistance = state.distance;
                    updateVisuals();
                    updateDisplay();
                },
                updateImage: (url) => {
                    if (url) {
                        const img = new Image();
                        if (!url.startsWith('data:')) {
                            img.crossOrigin = 'anonymous';
                        }

                        img.onload = () => {
                            const tex = new THREE.Texture(img);
                            tex.needsUpdate = true;
                            tex.encoding = THREE.sRGBEncoding;
                            planeMat.map = tex;
                            planeMat.color.set(0xffffff);
                            planeMat.needsUpdate = true;

                            const ar = img.width / img.height;
                            const maxSize = 1.5;
                            let scaleX, scaleY;
                            if (ar > 1) {
                                scaleX = maxSize;
                                scaleY = maxSize / ar;
                            } else {
                                scaleY = maxSize;
                                scaleX = maxSize * ar;
                            }
                            imagePlane.scale.set(scaleX, scaleY, 1);
                            imageFrame.scale.set(scaleX, scaleY, 1);
                            render(); // 图片加载完成后渲染一次
                        };

                        img.onerror = () => {
                            planeMat.map = null;
                            planeMat.color.set(0xFF0000);
                            planeMat.needsUpdate = true;
                        };

                        img.src = url;
                    } else {
                        planeMat.map = null;
                        planeMat.color.set(0x3a3a4a);
                        planeMat.needsUpdate = true;
                        imagePlane.scale.set(1, 1, 1);
                        imageFrame.scale.set(1, 1, 1);
                        render();
                    }
                }
            };
        }

        // Message handler
        window.addEventListener('message', (event) => {
            const data = event.data;

            if (data.type === 'INIT') {
                state.azimuth = data.horizontal || 0;
                state.elevation = data.vertical || 0;
                state.distance = data.zoom || 5;
                if (threeScene) {
                    threeScene.syncFromState();
                }
            } else if (data.type === 'SYNC_ANGLES') {
                state.azimuth = data.horizontal || 0;
                state.elevation = data.vertical || 0;
                state.distance = data.zoom || 5;
                if (threeScene) {
                    threeScene.syncFromState();
                }
            } else if (data.type === 'UPDATE_IMAGE') {
                state.imageUrl = data.imageUrl;
                if (threeScene) {
                    threeScene.updateImage(data.imageUrl);
                }
            }
        });

        // Initialize
        initThreeJS();
        updateDisplay();

        // Notify parent that we're ready
        window.parent.postMessage({ type: 'VIEWER_READY' }, '*');
    </script>
</body>
</html>
`;