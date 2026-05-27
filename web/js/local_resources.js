import { app } from "../../../../scripts/app.js";

app.registerExtension({
  name: "CJ-Nodes.LocalResources",
  setup() {
    if (!document.getElementById('cj-menu-style')) {
      const s = document.createElement('style');
      s.id = 'cj-menu-style';
      s.textContent = '.cj-menu-btn { background: #dc2626 !important; color: #fff !important; } .cj-menu-btn-green { background: #16a34a !important; color: #fff !important; }';
      document.head.appendChild(s);
    }
    const { ComfyButton } = window.comfyAPI.button;
    app.menu?.settingsGroup.append(
      new ComfyButton({
        icon: "folder-open",
        tooltip: "打开output文件夹",
        content: "本地资源",
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
