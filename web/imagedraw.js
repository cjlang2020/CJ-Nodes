import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "luy.imagedraw",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "ImageDrawNode") {
            // 为ImageDrawNode添加图片预览和上传功能
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                onNodeCreated?.apply(this, arguments);
                
                // 创建隐藏的文件输入
                const fileInput = document.createElement("input");
                fileInput.type = "file";
                fileInput.accept = "image/*";
                fileInput.style.display = "none";
                document.body.appendChild(fileInput);
                
                // 上传按钮控件
                const uploadWidget = this.addWidget("button", "上传图片", "", async () => {
                    fileInput.click();
                });
                
                // 图片预览控件
                const previewWidget = {
                    name: "image_preview", 
                    type: "image",
                    value: null,
                    draw: function(ctx, node, widget_width, y, H) {
                        if (this.value) {
                            // 如果有图片数据，绘制图片
                            const img = new Image();
                            img.onload = () => {
                                ctx.drawImage(img, 0, y, widget_width, H);
                            };
                            img.src = this.value;
                        } else {
                            // 绘制占位符
                            ctx.strokeStyle = "#999";
                            ctx.strokeRect(0, y, widget_width, H);
                            ctx.fillStyle = "#666";
                            ctx.font = "12px Arial";
                            ctx.textAlign = "center";
                            ctx.fillText("图片预览区域", widget_width/2, y + H/2);
                        }
                    },
                    computeSize: function(width) {
                        return [width, 200];
                    }
                };
                
                this.addWidget("custom", "image_preview", null, () => {}, previewWidget);
                
                // 文件选择事件处理
                fileInput.onchange = async (e) => {
                    const file = e.target.files[0];
                    if (file) {
                        try {
                            // 转换为Base64
                            const base64 = await new Promise((resolve, reject) => {
                                const reader = new FileReader();
                                reader.onload = () => resolve(reader.result);
                                reader.onerror = reject;
                                reader.readAsDataURL(file);
                            });
                            
                            // 发送到后端API
                            const response = await fetch("/image_draw/upload", {
                                method: "POST",
                                headers: {
                                    "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                    base64_string: base64
                                })
                            });
                            
                            const result = await response.json();
                            if (result.success) {
                                // 更新节点的base64输入框
                                const base64Widget = this.widgets.find(w => w.name === "base64_string");
                                if (base64Widget) {
                                    base64Widget.value = base64;
                                    // 触发节点更新
                                    base64Widget.element?.dispatchEvent(new Event('change'));
                                }
                                
                                // 更新预览
                                previewWidget.value = base64;
                                this.setSize(this.computeSize());
                                app.graph.setDirtyCanvas(true);
                                
                                app.ui.dialog.show("上传成功", result.message);
                            } else {
                                app.ui.dialog.show("上传失败", result.error);
                            }
                        } catch (error) {
                            app.ui.dialog.show("上传失败", "网络错误: " + error.message);
                        }
                    }
                };
                
                // 监听节点执行完成事件
                const onExecuted = this.onExecuted;
                this.onExecuted = function(message) {
                    onExecuted?.apply(this, arguments);
                    
                    if (message.images && message.images.length > 0) {
                        // 更新图片预览
                        const imgWidget = this.widgets.find(w => w.name === "image_preview");
                        if (imgWidget && !imgWidget.value) {
                            // 如果预览区域为空，使用输出的图片
                            const imageData = message.images[0];
                            if (imageData && imageData.filename) {
                                imgWidget.value = `/view?filename=${imageData.filename}`;
                                this.setSize(this.computeSize());
                            }
                        }
                    }
                };
                
                // 清理函数
                const onRemoved = this.onRemoved;
                this.onRemoved = function() {
                    onRemoved?.apply(this, arguments);
                    document.body.removeChild(fileInput);
                };
            };
            
            // 添加右键菜单选项
            const getExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
            nodeType.prototype.getExtraMenuOptions = function(_, options) {
                getExtraMenuOptions?.apply(this, arguments);
                
                options.push({
                    content: "测试API连接",
                    callback: async () => {
                        try {
                            const response = await fetch("/image_draw/status");
                            const result = await response.json();
                            app.ui.dialog.show("API状态", result.message);
                        } catch (error) {
                            app.ui.dialog.show("API测试失败", "无法连接到服务器: " + error.message);
                        }
                    }
                });
            };
        }
    }
});