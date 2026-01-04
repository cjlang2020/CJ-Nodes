import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

async function uploadZip(node, file) {
    if (!file || !file.name.toLowerCase().endsWith(".zip")) {
        return;
    }

    const btn = node.widgets.find(w => w.type === "button");
    const originalLabel = btn ? btn.name : "Upload Zip";
    if (btn) btn.name = "Uploading...";
    app.graph.setDirtyCanvas(true, true);

    try {
        const body = new FormData();
        body.append("image", file);
        body.append("subfolder", "zip"); 
        body.append("overwrite", "true"); 
        body.append("type", "input");

        console.log(`[ZipLoader] Uploading ${file.name} to input/zip...`);
        
        const response = await api.fetchApi("/upload/image", {
            method: "POST",
            body,
        });

        if (response.status !== 200) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();
        const serverFileName = data.name;
        const widget = node.widgets.find(w => w.name === "filename");
        if (widget) {
            if (widget.options.values.length === 1 && widget.options.values[0] === "None") {
                widget.options.values = [];
            }
            if (!widget.options.values.includes(serverFileName)) {
                widget.options.values.unshift(serverFileName);
            }
            
            widget.value = serverFileName;
            if (widget.callback) widget.callback(serverFileName);
        }
        console.log(`[ZipLoader] Upload success: ${serverFileName}`);

    } catch (error) {
        console.error("[ZipLoader] Error:", error);
    } finally {
        if (btn) btn.name = originalLabel;
        app.graph.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "Comfy.ZipLoaderNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LoadZipBatch") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;

                this.addWidget("button", "Upload Zip File", "Click to Upload", () => {
                    const input = document.createElement("input");
                    input.type = "file";
                    input.accept = ".zip";
                    input.style.display = "none";
                    input.onchange = async () => {
                        if (input.files.length > 0) {
                            await uploadZip(node, input.files[0]);
                        }
                        input.remove();
                    };
                    document.body.appendChild(input);
                    input.click();
                });

                node.onDragOver = function (e) {
                    if (e.dataTransfer && e.dataTransfer.items) {
                        const hasFile = Array.from(e.dataTransfer.items).some(item => item.kind === 'file');
                        if (hasFile) {
                            return true;
                        }
                    }
                    return false;
                };

                node.onDragDrop = function (e) {
                    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                        const file = e.dataTransfer.files[0];
                        if (file.name.toLowerCase().endsWith(".zip")) {
                            uploadZip(node, file);
                            return true;
                        }
                    }
                    return false;
                };

                node.onPaste = function(e) {
                    if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
                        const file = e.clipboardData.files[0];
                        if (file.name.toLowerCase().endsWith(".zip")) {
                            uploadZip(node, file);
                            return true;
                        }
                    }
                };
                
                return r;
            };
        }
    },
});