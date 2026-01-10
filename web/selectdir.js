import { app } from "../../scripts/app.js";
import { ComfyApp } from "../../scripts/app.js";

function addMenuHandler(nodeType, cb) {
    const getOpts = nodeType.prototype.getExtraMenuOptions;
    nodeType.prototype.getExtraMenuOptions = function () {
        const r = getOpts ? getOpts.apply(this, arguments) : []; // 兼容无默认菜单的节点
        cb.apply(this, arguments);
        return r;
    };
};

app.registerExtension({
    name: "luy.select.dir",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === "FolderSelectNode") {
            addMenuHandler(nodeType, function (_, options) {
                options.unshift({
                    content: "打开文件夹",
                    callback: async () => { // 改为async函数
                        try {
                            // 1. 保存当前节点引用（保留原有逻辑）
                            ComfyApp.clipspace_return_node = this;

                            // 2. 调用浏览器目录选择API（核心新增逻辑）
                            // 必须在用户点击的callback中直接调用，符合手势要求
                            const directoryHandle = await window.showDirectoryPicker({
                                mode: "read", // 权限：read（只读）/ readwrite（读写）
                                startIn: "desktop" // 可选：默认打开桌面目录
                            });

                            // 3. （可选）处理选中的文件夹（比如把路径赋值给节点）
                            console.log("选中的文件夹：", directoryHandle.name);
                            // 示例：给节点的某个输入框赋值文件夹名称/句柄
                            if (this.widgets) {
                                const folderWidget = this.widgets.find(w => w.name === "dirpath");
                                if (folderWidget) {
                                    folderWidget.value = directoryHandle.name; // 或存储handle供后续使用
                                    folderWidget.callback?.(folderWidget.value); // 触发节点值更新
                                }
                            }

                        } catch (e) {
                            // 处理异常（用户取消选择/权限不足等）
                            if (e.name === "AbortError") {
                                console.log("用户取消了文件夹选择");
                            } else {
                                console.error("打开文件夹窗口失败:", e);
                            }
                        }
                    },
                });
            });
        }
    }
});