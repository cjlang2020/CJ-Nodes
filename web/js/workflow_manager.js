import { app } from "../../../../scripts/app.js";
import { api } from "../../../../scripts/api.js";

function showToast(msg) {
  let toast = document.querySelector(".cj-toast-save");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "cj-toast-save";
    toast.style.cssText = 'position:fixed;bottom:30px;left:50%;transform:translateX(-50%);background:#333;color:#eee;padding:8px 20px;border-radius:6px;font-size:13px;z-index:10001;box-shadow:0 4px 12px rgba(0,0,0,0.4);opacity:0;transition:opacity 0.3s;';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.style.opacity = '0', 2500);
}

async function saveWorkflowToPath(path) {
  try {
    const graphData = app.graph.serialize();
    const resp = await api.storeUserData(path, graphData);
    return resp.status === 200;
  } catch (e) {
    console.error('Failed to save workflow:', e);
    return false;
  }
}

app.registerExtension({
  name: "CJ-Nodes.WorkflowManager",
  setup() {
    const { ComfyButton } = window.comfyAPI.button;
    app.menu?.settingsGroup.append(
      new ComfyButton({
        icon: "folder-open",
        tooltip: "打开workflows文件夹",
        content: "流程管理",
        classList: "comfyui-button cj-menu-btn",
        action: async () => {
          await fetch("/CJ-Nodes/api/open-directory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ type: "workflows" })
          });
        }
      })
    );

    document.addEventListener('keydown', async (e) => {
      if (!app._cjWorkflowPath) return;
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        if (e.target.closest('input, textarea')) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        const ok = await saveWorkflowToPath(app._cjWorkflowPath);
        showToast(ok ? '已保存到原文件' : '保存失败');
      }
    }, true);
  }
});
