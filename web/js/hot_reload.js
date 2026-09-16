import { app } from "../../../../scripts/app.js";
import "./cj_menu_style.js";

app.registerExtension({
  name: "CJ-Nodes.HotReload",
  setup() {
    const { ComfyButton } = window.comfyAPI.button;
    app.menu?.settingsGroup.append(
      new ComfyButton({
        icon: "refresh",
        tooltip: "重新加载 CJ-Nodes 的节点代码（修改 service 下的 Python 代码后点击，再刷新页面即可生效，无需重启 ComfyUI）",
        content: "重载插件",
        classList: "comfyui-button cj-menu-btn",
        action: async () => {
          try {
            const res = await fetch("/CJ-Nodes/api/reload-nodes", { method: "POST" });
            const data = await res.json();
            if (data.ok) {
              alert(`CJ-Nodes 重载完成：${data.count} 个节点类。\n如新增/修改了节点定义，请刷新页面（F5）加载新定义。`);
            } else {
              alert("CJ-Nodes 重载失败：" + data.error);
            }
          } catch (e) {
            alert("CJ-Nodes 重载请求失败：" + e.message);
          }
        }
      })
    );
  }
});
