import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "Comfy.BatchZipper",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "SaveImageAsZip"||nodeData.name === "SaveTextAsZip") {
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                const r = onExecuted ? onExecuted.apply(this, arguments) : undefined;
                
                if (message && message.zip_filename) {
                    const zipName = message.zip_filename[0];
                    const subfolder = message.subfolder ? message.subfolder[0] : "";
                    const type = message.type ? message.type[0] : "output";
                    const node = this;

                    const existingWidgetIndex = node.widgets.findIndex(w => w.name === "Download Last Zip");
                    if (existingWidgetIndex !== -1) {
                        node.widgets.splice(existingWidgetIndex, 1);
                    }

                    const downloadWidget = node.addWidget("button", "Download Last Zip", "Click to Download", () => {
                        const params = new URLSearchParams({
                            filename: zipName,
                            subfolder: subfolder,
                            type: type
                        });
                        const url = api.apiURL("/view?" + params.toString());
                        window.open(url, "_blank");
                    });
                    
                    downloadWidget.label = `Download: ${zipName}`;
                    node.setDirtyCanvas(true, true);
                }
                return r;
            };
        }
    },
});