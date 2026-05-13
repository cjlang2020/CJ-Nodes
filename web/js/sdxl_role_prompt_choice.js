import { app } from "../../../../scripts/app.js";

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

                // 加载编辑界面
                try {
                    iframe.src = "/CJ-Nodes/sdxl_prompt.html";
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
