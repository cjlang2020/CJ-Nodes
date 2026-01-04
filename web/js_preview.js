import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function updatePreview(node) {
    if (!node || !node.widgets) return;

    let previewUrl = null;

    if (node.comfyClass === "LoadImageBatch") {
        const widget = node.widgets.find(w => w.name === "batch");
        const uuid = widget ? widget.value : null;

        if (uuid && uuid !== "None") {
            previewUrl = api.apiURL(
                `/view?filename=__preview__grid.webp&subfolder=batch/${uuid}&type=input`
            );
        }
    }

    if (previewUrl) {
        const img = new Image();
        img.onload = () => {
            node.imgs = [img];
            app.graph.setDirtyCanvas(true, true);
        };
        img.onerror = () => {
            node.imgs = [];
            app.graph.setDirtyCanvas(true, true);
        };
        img.src = previewUrl;
    } else {
        node.imgs = [];
        app.graph.setDirtyCanvas(true, true);
    }
}

app.registerExtension({
    name: "Comfy.BatchPreviewWatcher",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LoadImageBatch") {
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;
                
                const widget = this.widgets.find(w => w.name === "batch");

                if (widget) {
                    const originalCallback = widget.callback;
                    widget.callback = function(value) {
                        if (originalCallback) originalCallback.apply(this, arguments);
                        updatePreview(node);
                    };
                }
                
                setTimeout(() => { updatePreview(node); }, 100);
                return r;
            };

            const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function() {
                const r = onConfigure ? onConfigure.apply(this, arguments) : undefined;
                setTimeout(() => { updatePreview(this); }, 100);
                return r;
            }
        }
    },
});