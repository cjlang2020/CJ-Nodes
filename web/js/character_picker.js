import { app } from "../../../../scripts/app.js";

app.registerExtension({
    name: "luy.characterPicker",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "CharacterPickerNode") {
            console.log("初始化角色Tag选择器节点扩展");

            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                this.promptData = "";
                this._promptPanelReady = false;
                this._resizeObserver = null;

                this.promptWidget = this.widgets.find(w => w.name === "final_prompt");
                if (this.promptWidget) {
                    this.promptData = this.promptWidget.value || "";
                }

                const iframe = document.createElement("iframe");
                iframe.style.width = "100%";
                iframe.style.height = "100%";
                iframe.style.border = "none";
                iframe.style.borderRadius = "8px";
                iframe.style.backgroundColor = "#ffffff";
                iframe.style.pointerEvents = "auto";
                iframe.setAttribute("sandbox", "allow-scripts allow-same-origin");

                try {
                    iframe.src = "/CJ-Nodes/character_prompt.html";
                } catch (e) {
                    console.error("创建iframe失败:", e);
                }

                const promptWidget = this.addDOMWidget(
                    "prompt_panel",
                    "角色Tag选择面板",
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

                promptWidget.computeSize = function(width) {
                    const w = width || 500;
                    return [w, 620];
                };

                if (promptWidget.element) {
                    promptWidget.element.style.pointerEvents = "auto";
                }

                this.promptIframe = iframe;

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

                const handleMessage = (e) => {
                    if (e.source !== iframe.contentWindow) return;

                    const data = e.data;

                    if (data.type === 'PROMPT_PANEL_READY') {
                        this._promptPanelReady = true;
                        iframe.contentWindow.postMessage({
                            type: 'INIT_PROMPT',
                            prompt: this.promptData
                        }, '*');

                        setTimeout(() => {
                            this.initResizeObserver();
                        }, 1000);

                    } else if (data.type === 'PROMPT_UPDATE') {
                        this.promptData = data.prompt;
                        if (this.promptWidget) {
                            this.promptWidget.value = data.prompt;
                            this.promptWidget.inputEl.value = data.prompt;
                        }
                        promptWidget.value = data.prompt;

                        this.flags = this.flags || {};
                        this.flags.dirty = true;
                        if (app && app.graph) {
                            app.graph.setDirtyCanvas(true, true);
                        }
                    }
                };

                window.addEventListener('message', handleMessage);

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

                this.setSize([500, 620]);

                return r;
            };
        }
    }
});

console.log("角色Tag选择器节点扩展已加载");
