import { app } from "../../../../scripts/app.js";
const sdxl = window.location.origin+"/extensions/CJ-Nodes/js/sdxl_prompt.js"

// ========== 提示词面板HTML模板（左右分栏紧凑布局） ==========
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
            height: 600px;
            background: #f5f7fa;
            font-family: Arial, sans-serif;
            overflow: hidden;
            display: flex;
        }
        /* 左侧分组列表 */
        .left-panel {
            width: 120px;
            min-width: 120px;
            background: #e9ecef;
            border-right: 1px solid #dee2e6;
            overflow-y: auto;
            overflow-x: hidden;
            flex-shrink: 0;
            height: 600px;
            max-height: 600px;
        }
        /* 左侧滚动条样式 */
        .left-panel::-webkit-scrollbar {
            width: 5px;
        }
        .left-panel::-webkit-scrollbar-track {
            background: #e9ecef;
        }
        .left-panel::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        .left-panel::-webkit-scrollbar-thumb:hover {
            background: #a1a1a1;
        }
        .group-item {
            padding: 6px 8px;
            background: transparent;
            border: none;
            border-bottom: 1px solid #dee2e6;
            cursor: pointer;
            font-size: 11px;
            color: #495057;
            text-align: left;
            width: 100%;
            transition: all 0.2s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .group-item:hover {
            background: #dee2e6;
        }
        .group-item.active {
            background: #2d5aff;
            color: white;
        }
        /* 右侧内容区域 */
        .right-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            height: 600px;
        }
        /* 子项列表 */
        .subitem-container {
            flex: 1;
            padding: 6px;
            overflow-y: auto;
            overflow-x: hidden;
            background: white;
            display: flex;
            flex-wrap: wrap;
            align-content: flex-start;
            gap: 4px;
            max-height: calc(600px - 30px);
        }
        .subitem-btn {
            display: inline-block;
            width: auto;
            padding: 3px 8px;
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
            color: #333;
            text-align: left;
            transition: all 0.2s;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .subitem-btn:hover {
            background: #e3f2fd;
            border-color: #90caf9;
        }
        .subitem-btn.active {
            background: #2d5aff;
            color: white;
            border-color: #2d5aff;
        }
        .subitem-btn.active:hover {
            background: #1a46e0;
        }
        /* 滚动条样式 */
        .subitem-container::-webkit-scrollbar {
            width: 6px;
        }
        .subitem-container::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        .subitem-container::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }
        .subitem-container::-webkit-scrollbar-thumb:hover {
            background: #a1a1a1;
        }
        /* 空状态提示 */
        .empty-tip {
            text-align: center;
            color: #999;
            font-size: 12px;
            margin-top: 40px;
        }
        /* 分组标题 */
        .group-title {
            padding: 4px 8px;
            background: #e3f2fd;
            color: #1976d2;
            font-size: 11px;
            font-weight: 600;
            border-bottom: 1px solid #bbdefb;
            flex-shrink: 0;
            height: 24px;
            line-height: 16px;
        }
    </style>
</head>
<body>
    <div class="left-panel" id="leftPanel"></div>
    <div class="right-panel">
        <div class="group-title" id="groupTitle">请选择分组</div>
        <div class="subitem-container" id="subitemContainer">
            <div class="empty-tip">点击左侧分组查看内容</div>
        </div>
    </div>
    <script src="${sdxl}"></script>
    <script>
        // 提示词数据
        const keysWord = SDXLWord;
        // 当前选中的分组索引
        let activeGroupIndex = -1;
        // 当前选中的子项prompt
        let selectedPrompt = "";

        // 初始化左侧分组列表
        function initLeftPanel() {
            const leftPanel = document.getElementById('leftPanel');
            leftPanel.innerHTML = '';

            keysWord.forEach((item, index) => {
                const groupBtn = document.createElement('button');
                groupBtn.className = 'group-item';
                groupBtn.textContent = item.groupName;
                groupBtn.dataset.index = index;

                if (index === activeGroupIndex) {
                    groupBtn.classList.add('active');
                }

                groupBtn.addEventListener('click', () => {
                    selectGroup(index);
                });

                leftPanel.appendChild(groupBtn);
            });
        }

        // 选择分组
        function selectGroup(index) {
            activeGroupIndex = index;
            
            // 更新左侧激活状态
            document.querySelectorAll('.group-item').forEach((item, i) => {
                if (i === index) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });

            // 渲染右侧内容
            renderSubItems(index);
        }

        // 渲染右侧子项
        function renderSubItems(groupIndex) {
            const container = document.getElementById('subitemContainer');
            const titleEl = document.getElementById('groupTitle');
            const groupData = keysWord[groupIndex];

            if (!groupData) {
                titleEl.textContent = '请选择分组';
                container.innerHTML = '<div class="empty-tip">点击左侧分组查看内容</div>';
                return;
            }

            // 更新分组标题
            titleEl.textContent = groupData.groupName;

            // 清空并渲染子项
            container.innerHTML = '';

            if (!groupData.subItem || groupData.subItem.length === 0) {
                container.innerHTML = '<div class="empty-tip">该分组暂无内容</div>';
                return;
            }

            groupData.subItem.forEach((subItem, index) => {
                const btn = document.createElement('button');
                btn.className = 'subitem-btn';
                btn.textContent = subItem.name;
                btn.dataset.prompt = subItem.prompt;

                // 标记当前选中的项
                if (selectedPrompt === subItem.prompt) {
                    btn.classList.add('active');
                }

                // 点击事件 - 替换模式
                btn.addEventListener('click', () => {
                    // 更新选中状态
                    document.querySelectorAll('.subitem-btn').forEach(b => {
                        b.classList.remove('active');
                    });
                    btn.classList.add('active');

                    // 记录选中的prompt并发送
                    selectedPrompt = subItem.prompt;
                    sendPromptUpdate(subItem.prompt);
                });

                container.appendChild(btn);
            });
        }

        // 发送提示词更新（替换模式）
        function sendPromptUpdate(prompt) {
            window.parent.postMessage({
                type: 'PROMPT_UPDATE',
                prompt: prompt
            }, '*');
        }

        // 初始化提示词（接收外部传入的初始值）
        function initPrompt(initialPrompt = "") {
            if (initialPrompt) {
                selectedPrompt = initialPrompt;
                // 查找并高亮匹配的子项
                highlightMatchingSubItem(initialPrompt);
            }
        }

        // 高亮匹配的子项
        function highlightMatchingSubItem(prompt) {
            document.querySelectorAll('.subitem-btn').forEach(btn => {
                if (btn.dataset.prompt === prompt) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
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
        initLeftPanel();
        
        // 默认选中第一个分组
        if (keysWord.length > 0) {
            selectGroup(0);
        }

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
    name: "luy.sdxlPromptPicker",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 匹配你的节点名称
        if (nodeData.name === "SDXLPromptPickerNode" || nodeData.name === "Luy-SDXLPromptPickerNode") {
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

                // 设置面板尺寸 - 固定高度600px
                promptWidget.computeSize = function(width) {
                    const w = width || 500;
                    return [w, 620];
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
                        // 更新提示词（替换模式）
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

                // 设置节点初始大小 - 固定高度600px
                this.setSize([500, 620]);

                return r;
            };
        }
    }
});

console.log("提示词选择器节点扩展已加载");
