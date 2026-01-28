import { app } from "../../../../scripts/app.js";
const sdxl = window.location.origin+"/extensions/CJ-Nodes/js/sdxl.js"
// ========== 提示词面板HTML模板（带Tab切换+紧凑布局） ==========
const PROMPT_PICKER_HTML = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>提示词选择器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            width: 100%;
            height: 100vh;
            background: #f5f7fa;
            font-family: Arial, sans-serif;
            padding: 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        /* Tab 栏样式 */
        .tab-bar {
            display: flex;
            background: #e9ecef;
            border-bottom: 1px solid #dee2e6;
            overflow-x: auto;
            flex-shrink: 0;
        }
        .tab-item {
            padding: 5px;
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            cursor: pointer;
            font-size: 12px;
            color: #495057;
            white-space: nowrap;
            transition: all 0.2s;
        }
        .tab-item.active {
            border-bottom-color: #2d5aff;
            color: #2d5aff;
            font-weight: 600;
        }
        .tab-item:hover {
            background: #dee2e6;
        }
        /* 内容容器 */
        .content-container {
            flex: 1;
            padding: 8px; /* 减少内边距 */
            overflow-y: auto;
            background: white;
        }
        /* 二级分类标题 */
        .second-level-title {
            font-size: 14px;
            font-weight: 600;
            color: #4a6fa5;
            margin: 8px 0 4px 0; /* 减少上下间距 */
            padding: 3px 6px; /* 缩小标题内边距 */
            background: #e3f2fd;
            border-radius: 4px;
            display: inline-block;
        }
        /* 标签容器 - 核心紧凑化修改 */
        .tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 3px; /* 从6px改为3px，大幅减少标签间距 */
            padding: 2px 4px; /* 减少容器内边距 */
            margin-bottom: 8px; /* 减少容器底部间距 */
        }
        /* 标签按钮 - 核心紧凑化修改 */
        .tag-btn {
            padding: 2px 6px; /* 从4px 10px改为2px 6px，缩小按钮尺寸 */
            background: #e8f3ff;
            border: 1px solid #b3d8ff;
            border-radius: 3px; /* 缩小圆角 */
            cursor: pointer;
            font-size: 11px; /* 字体缩小1px */
            color: #333;
            white-space: nowrap;
            transition: all 0.2s;
            line-height: 1.4; /* 调整行高，让按钮更紧凑 */
        }
        .tag-btn:hover {
            background: #d1e7ff;
        }
        .tag-btn.active {
            background: #2d5aff;
            color: white;
            border-color: #2d5aff;
        }
        .tag-btn.active:hover {
            background: #1a46e0;
        }
        /* 空状态提示 */
        .empty-tip {
            text-align: center;
            color: #999;
            font-size: 13px;
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="tab-bar" id="tabBar"></div>
    <div class="content-container" id="contentContainer"></div>
    <script src="${sdxl}"></script>
    <script>
        // 提示词数据
        const keysWord = SDXLWord;
        // 当前选中的提示词
        let selectedPrompts = [];
        // 当前激活的Tab索引
        let activeTabIndex = 0;

        // 初始化Tab栏
        function initTabBar() {
            const tabBar = document.getElementById('tabBar');
            tabBar.innerHTML = '';

            keysWord.forEach((item, index) => {
                const tabItem = document.createElement('button');
                tabItem.className = 'tab-item';
                tabItem.textContent = item.name;
                tabItem.dataset.index = index;

                if (index === activeTabIndex) {
                    tabItem.classList.add('active');
                }

                tabItem.addEventListener('click', () => {
                    switchTab(index);
                });

                tabBar.appendChild(tabItem);
            });
        }

        // 切换Tab
        function switchTab(index) {
            activeTabIndex = index;
            // 更新Tab激活状态
            document.querySelectorAll('.tab-item').forEach((item, i) => {
                if (i === index) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
            // 渲染对应内容
            renderContent(index);
        }

        // 渲染Tab内容
        function renderContent(tabIndex) {
            const contentContainer = document.getElementById('contentContainer');
            const currentData = keysWord[tabIndex];

            if (!currentData || !currentData.child.length) {
                contentContainer.innerHTML = '<div class="empty-tip">暂无内容</div>';
                return;
            }

            contentContainer.innerHTML = '';

            // 渲染二级分类
            currentData.child.forEach(secondLevel => {
                // 二级标题
                const secondLevelEl = document.createElement('div');
                secondLevelEl.className = 'second-level-title';
                secondLevelEl.textContent = secondLevel.name;
                contentContainer.appendChild(secondLevelEl);

                // 标签容器
                const tagContainer = document.createElement('div');
                tagContainer.className = 'tag-container';

                // 渲染标签按钮
                secondLevel.child.forEach(tagItem => {
                    const tagBtn = document.createElement('button');
                    tagBtn.className = 'tag-btn';
                    tagBtn.textContent = tagItem.word;

                    // 标记已选中的标签
                    if (selectedPrompts.includes(tagItem.word)) {
                        tagBtn.classList.add('active');
                    }

                    // 点击事件
                    tagBtn.addEventListener('click', () => {
                        if (selectedPrompts.includes(tagItem.word)) {
                            // 移除
                            selectedPrompts = selectedPrompts.filter(p => p !== tagItem.word);
                            tagBtn.classList.remove('active');
                        } else {
                            // 添加
                            selectedPrompts.push(tagItem.word);
                            tagBtn.classList.add('active');
                        }
                        // 发送更新消息
                        sendPromptUpdate();
                    });

                    tagContainer.appendChild(tagBtn);
                });

                contentContainer.appendChild(tagContainer);
            });
        }

        // 发送提示词更新
        function sendPromptUpdate() {
            const finalPrompt = selectedPrompts.join(', ');
            window.parent.postMessage({
                type: 'PROMPT_UPDATE',
                prompt: finalPrompt
            }, '*');
        }

        // 初始化提示词
        function initPrompt(initialPrompt = "") {
            if (initialPrompt) {
                selectedPrompts = initialPrompt.split(",").map(p => p.trim()).filter(p => p);
            }
            // 重新渲染当前Tab的标签选中状态
            renderContent(activeTabIndex);
        }

        // 监听父窗口消息
        window.addEventListener('message', (e) => {
            try {
                const data = e.data;
                if (data.type === 'INIT_PROMPT') {
                    initPrompt(data.prompt || "");
                } else if (data.type === 'RESIZE_PANEL') {
                    document.body.style.height = '100%';
                }
            } catch (e) {
                console.error('处理父窗口消息失败:', e);
            }
        });

        // 初始化
        initTabBar();
        renderContent(activeTabIndex);

        // 通知父窗口面板就绪
        setTimeout(() => {
            window.parent.postMessage({type: 'PROMPT_PANEL_READY'}, '*');
        }, 100);
    </script>
</body>
</html>
`;

// ========== 注册ComfyUI扩展 ==========
app.registerExtension({
    name: "luy.PromptPicker",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 匹配你的节点名称
        if (nodeData.name === "PromptPickerNode" || nodeData.name === "Luy-PromptPickerNode") {
            console.log("初始化提示词选择器节点扩展");

            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                // 初始化提示词数据
                this.promptData = "";
                this._promptPanelReady = false;
                this._resizeObserver = null;

                // 找到final_prompt输入框
                this.promptWidget = this.widgets.find(w => w.name === "final_prompt");
                if (this.promptWidget) {
                    this.promptData = this.promptWidget.value || "";
                }

                // 创建iframe承载提示词面板
                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.borderRadius = "8px";
                iframe.style.backgroundColor = "#ffffff";
                iframe.style.pointerEvents = "auto";
                iframe.setAttribute("sandbox", "allow-scripts allow-same-origin");

                // 生成Blob URL加载HTML
                try {
                    const blob = new Blob([PROMPT_PICKER_HTML], { type: 'text/html;charset=utf-8' });
                    const blobUrl = URL.createObjectURL(blob);
                    iframe.src = blobUrl;
                    iframe._blobUrl = blobUrl;
                } catch (e) {
                    console.error("创建iframe失败:", e);
                    alert("创建提示词面板失败: " + e.message);
                }

                // 添加DOM Widget到节点
                const promptWidget = this.addDOMWidget(
                    "prompt_panel",
                    "提示词选择面板",
                    iframe,
                    {
                        getValue: () => node.promptData || "",
                        setValue: (v) => {
                            node.promptData = v;
                            if (node.promptWidget) {
                                node.promptWidget.value = v;
                                node.promptWidget.inputEl.value = v;
                            }
                        }
                    }
                );

                // 设置面板尺寸
                promptWidget.computeSize = function(width) {
                    const w = width || 700;
                    return [w, 800];
                };

                if (promptWidget.element) {
                    promptWidget.element.style.pointerEvents = "auto";
                }

                this.promptIframe = iframe;

                // 初始化ResizeObserver
                this.initResizeObserver = function() {
                    if (this._resizeObserver) {
                        try {
                            this._resizeObserver.disconnect();
                        } catch (e) {
                            console.warn("断开ResizeObserver失败:", e);
                        }
                    }

                    let observeTarget = promptWidget?.element || this.element || iframe;
                    if (observeTarget && window.ResizeObserver) {
                        this._resizeObserver = new ResizeObserver(entries => {
                            if (this._promptPanelReady && this.promptIframe && this.promptIframe.contentWindow) {
                                this.promptIframe.contentWindow.postMessage({
                                    type: 'RESIZE_PANEL'
                                }, '*');
                            }
                        });

                        try {
                            this._resizeObserver.observe(observeTarget);
                        } catch (e) {
                            console.error("初始化ResizeObserver失败:", e);
                        }
                    }
                };

                // 处理iframe消息
                const handleMessage = (e) => {
                    if (e.source !== iframe.contentWindow) return;

                    const data = e.data;
                    console.log("收到提示词面板消息:", data.type);

                    if (data.type === 'PROMPT_PANEL_READY') {
                        // 面板就绪，初始化提示词
                        this._promptPanelReady = true;
                        iframe.contentWindow.postMessage({
                            type: 'INIT_PROMPT',
                            prompt: this.promptData
                        }, '*');

                        // 初始化尺寸监听
                        setTimeout(() => {
                            this.initResizeObserver();
                        }, 1000);

                    } else if (data.type === 'PROMPT_UPDATE') {
                        // 更新提示词
                        this.promptData = data.prompt;
                        if (this.promptWidget) {
                            this.promptWidget.value = data.prompt;
                            this.promptWidget.inputEl.value = data.prompt;
                        }
                        promptWidget.value = data.prompt;

                        // 标记节点为脏
                        this.flags = this.flags || {};
                        this.flags.dirty = true;
                        if (app && app.graph) {
                            app.graph.setDirtyCanvas(true, true);
                        }
                    }
                };

                window.addEventListener('message', handleMessage);

                // 监听输入框变化
                const origOnWidgetChanged = this.onWidgetChanged;
                this.onWidgetChanged = function(name, value, oldValue, widget) {
                    if (origOnWidgetChanged) {
                        origOnWidgetChanged.apply(this, arguments);
                    }

                    if (name === "final_prompt" && this._promptPanelReady) {
                        this.promptData = value;
                        iframe.contentWindow.postMessage({
                            type: 'INIT_PROMPT',
                            prompt: value
                        }, '*');
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
                this.setSize([700, 800]);

                return r;
            };
        }
    }
});

console.log("提示词选择器节点扩展已加载");