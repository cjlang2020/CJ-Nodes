import { app } from "../../../../scripts/app.js";
import "./cj_menu_style.js";

app.registerExtension({
  name: "CJ-Nodes.LocalResources",
  setup() {
    const { ComfyButton } = window.comfyAPI.button;
    app.menu?.settingsGroup.append(
      new ComfyButton({
        icon: "folder-open",
        tooltip: "打开output文件夹",
        content: "Output图片",
        classList: "comfyui-button cj-menu-btn-green",
        action: async () => {
          await fetch("/CJ-Nodes/api/open-directory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "local-resources" })
          });
        }
      })
    );
  }
});
