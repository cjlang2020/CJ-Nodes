import { app } from "../../../../scripts/app.js";
import { api } from "../../../../scripts/api.js";

const API_BASE = "/CJ-Nodes/api/workflows";

const CSS = `
.wm-dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 10000;
  display: flex; align-items: center; justify-content: center;
}
.wm-dialog {
  width: 85vw; height: 90vh;
  background: #1e1e1e; color: #e0e0e0;
  border: 1px solid #444; border-radius: 6px;
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.wm-header {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: #2a2a2a;
  border-bottom: 1px solid #444; flex: 0 0 auto;
}
.wm-title { font-weight: 600; font-size: 14px; white-space: nowrap; }
.wm-breadcrumbs {
  display: flex; align-items: center; gap: 4px;
  flex: 1; overflow-x: auto; font-size: 13px;
  padding: 0 8px; white-space: nowrap;
}
.wm-breadcrumbs::-webkit-scrollbar { height: 3px; }
.wm-breadcrumbs::-webkit-scrollbar-thumb { background: #555; border-radius: 2px; }
.wm-breadcrumb-item {
  color: #8ab4f8; cursor: pointer; padding: 2px 4px;
  border-radius: 3px; flex-shrink: 0;
}
.wm-breadcrumb-item:hover { background: #333; }
.wm-breadcrumb-sep { color: #666; flex-shrink: 0; }
.wm-breadcrumb-current { color: #ccc; flex-shrink: 0; }
.wm-close-btn {
  background: transparent; border: none; color: #bbb;
  cursor: pointer; font-size: 20px; line-height: 1; padding: 0 6px;
}
.wm-close-btn:hover { color: #fff; }
.wm-body { flex: 1; overflow-y: auto; padding: 12px; }
.wm-body::-webkit-scrollbar { width: 6px; }
.wm-body::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
.wm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}
.wm-item {
  display: flex; flex-direction: column; align-items: center;
  background: #2a2a2a; border: 1px solid #444;
  border-radius: 6px; cursor: pointer; overflow: hidden;
  transition: all 0.15s; padding: 6px;
  position: relative;
}
.wm-item:hover { border-color: #8ab4f8; background: #333; }
.wm-item-folder { border-color: #3a4a5a; }
.wm-item-folder:hover { border-color: #6a9fd8; }
.wm-item-workflow { border-color: #3a5a4a; }
.wm-item-workflow:hover { border-color: #5ad8a0; }
.wm-item-icon {
  width: 100%; aspect-ratio: 2/1;
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; color: #888; border-radius: 4px;
  background: #222;
}
.wm-item-name {
  margin-top: 5px; font-size: 11px; color: #ccc;
  text-align: center; word-break: break-all;
  width: 100%; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.wm-empty {
  grid-column: 1 / -1; text-align: center; color: #888;
  padding: 40px 0; font-size: 14px;
}
.wm-loading {
  text-align: center; color: #888; padding: 40px 0; font-size: 14px;
}
.wm-toast {
  position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
  background: #333; color: #eee; padding: 8px 20px;
  border-radius: 6px; font-size: 13px; z-index: 10001;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  opacity: 0; transition: opacity 0.3s;
}
.wm-toast.show { opacity: 1; }
.wm-context-menu {
  position: fixed; z-index: 10002;
  background: #2a2a2a; border: 1px solid #555;
  border-radius: 6px; padding: 4px 0; min-width: 140px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}
.wm-context-item {
  padding: 7px 16px; font-size: 13px; color: #ddd;
  cursor: pointer; white-space: nowrap;
}
.wm-context-item:hover { background: #3a3a3a; color: #fff; }
.wm-context-sep {
  height: 1px; background: #444; margin: 4px 0;
}
.wm-modal-overlay {
  position: fixed; inset: 0; z-index: 10003;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
}
.wm-modal {
  background: #2a2a2a; border: 1px solid #555;
  border-radius: 8px; padding: 20px; min-width: 320px; max-width: 500px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.wm-modal h3 { font-size: 15px; margin: 0 0 12px; color: #eee; }
.wm-modal input {
  width: 100%; padding: 8px 10px; border: 1px solid #555;
  border-radius: 4px; background: #1e1e1e; color: #eee; font-size: 13px;
  box-sizing: border-box; margin-bottom: 12px;
}
.wm-modal input:focus { outline: none; border-color: #8ab4f8; }
.wm-modal-btns { display: flex; gap: 8px; justify-content: flex-end; }
.wm-modal-btn {
  padding: 6px 16px; border: 1px solid #555; border-radius: 4px;
  background: #3a3a3a; color: #eee; cursor: pointer; font-size: 13px;
}
.wm-modal-btn:hover { background: #4a4a4a; }
.wm-modal-btn-primary { background: #2563eb; border-color: #3b82f6; }
.wm-modal-btn-primary:hover { background: #1d4ed8; }
.wm-modal-btn-danger { background: #dc2626; border-color: #ef4444; }
.wm-modal-btn-danger:hover { background: #b91c1c; }
.wm-move-list {
  max-height: 300px; overflow-y: auto; margin-bottom: 12px;
  border: 1px solid #444; border-radius: 4px; background: #1e1e1e;
}
.wm-move-item {
  padding: 8px 12px; cursor: pointer; font-size: 13px; color: #ccc;
  border-bottom: 1px solid #333;
}
.wm-move-item:hover, .wm-move-item.selected { background: #333; color: #fff; }
.wm-move-item:last-child { border-bottom: none; }
.wm-move-new {
  display: flex; gap: 6px; margin-bottom: 12px;
}
.wm-move-new input { flex: 1; margin-bottom: 0; }
.wm-move-new button {
  padding: 6px 12px; border: 1px solid #555; border-radius: 4px;
  background: #2563eb; color: #eee; cursor: pointer; font-size: 12px; white-space: nowrap;
}
.wm-move-new button:hover { background: #1d4ed8; }
`;

class WorkflowManagerDialog {
  constructor() {
    this.overlay = null;
    this.dialog = null;
    this.body = null;
    this.breadcrumbs = null;
    this.styleInjected = false;
    this.currentPath = "";
    this.currentData = null;
    this._ctxMenu = null;
    this._modalOverlay = null;
  }

  open() {
    this.injectStyles();
    this.buildUI();
    this.loadDirectory("");
  }

  close() {
    this._closeCtxMenu();
    this._closeModal();
    if (this.overlay) {
      this.overlay.remove();
      this.overlay = null;
      this.dialog = null;
      this.body = null;
      this.breadcrumbs = null;
      this.currentData = null;
    }
  }

  injectStyles() {
    if (this.styleInjected) return;
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
    this.styleInjected = true;
  }

  buildUI() {
    if (this.overlay) return;
    this.overlay = document.createElement("div");
    this.overlay.className = "wm-dialog-overlay";
    this.overlay.addEventListener("click", (e) => { if (e.target === this.overlay) this.close(); });

    this.dialog = document.createElement("div");
    this.dialog.className = "wm-dialog";

    const header = document.createElement("div");
    header.className = "wm-header";
    const title = document.createElement("span");
    title.className = "wm-title";
    title.textContent = "流程管理";
    this.breadcrumbs = document.createElement("div");
    this.breadcrumbs.className = "wm-breadcrumbs";
    const closeBtn = document.createElement("button");
    closeBtn.className = "wm-close-btn";
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", () => this.close());
    header.appendChild(title);
    header.appendChild(this.breadcrumbs);
    header.appendChild(closeBtn);
    this.dialog.appendChild(header);

    this.body = document.createElement("div");
    this.body.className = "wm-body";
    this.dialog.appendChild(this.body);

    this.overlay.appendChild(this.dialog);
    document.body.appendChild(this.overlay);
  }

  async loadDirectory(relPath) {
    if (!this.body) return;
    this.body.innerHTML = '<div class="wm-loading">加载中...</div>';
    try {
      const resp = await fetch(`${API_BASE}/list?path=${encodeURIComponent(relPath)}`);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        this.body.innerHTML = '<div class="wm-empty">加载失败' + (err.error ? ': ' + err.error : ' (' + resp.status + ')') + '</div>';
        return;
      }
      this.currentData = await resp.json();
      this.currentPath = this.currentData.currentPath || "";
      this.renderBreadcrumbs(this.currentData.currentPath || "");
      this.renderGrid(this.currentData);
    } catch (e) {
      this.body.innerHTML = '<div class="wm-empty">加载失败: ' + e.message + '</div>';
    }
  }

  renderBreadcrumbs(currentPath) {
    this.breadcrumbs.innerHTML = "";
    const rootItem = document.createElement("span");
    rootItem.className = "wm-breadcrumb-item";
    rootItem.textContent = "workflows";
    rootItem.addEventListener("click", () => this.loadDirectory(""));
    this.breadcrumbs.appendChild(rootItem);
    if (!currentPath) return;
    const parts = currentPath.split("/");
    let accumulated = "";
    for (const part of parts) {
      if (!part) continue;
      accumulated += (accumulated ? "/" : "") + part;
      const sep = document.createElement("span");
      sep.className = "wm-breadcrumb-sep";
      sep.textContent = "›";
      this.breadcrumbs.appendChild(sep);
      if (part === parts[parts.length - 1]) {
        const current = document.createElement("span");
        current.className = "wm-breadcrumb-current";
        current.textContent = part;
        this.breadcrumbs.appendChild(current);
      } else {
        const item = document.createElement("span");
        item.className = "wm-breadcrumb-item";
        item.textContent = part;
        item.addEventListener("click", () => this.loadDirectory(accumulated));
        this.breadcrumbs.appendChild(item);
      }
    }
  }

  renderGrid(data) {
    this.body.innerHTML = "";
    const grid = document.createElement("div");
    grid.className = "wm-grid";

    if (data.parentPath != null) {
      const upItem = this._createItem({ name: "..", isDirectory: true }, true);
      upItem.addEventListener("click", () => this.loadDirectory(data.parentPath));
      grid.appendChild(upItem);
    }

    if (!data.entries || data.entries.length === 0) {
      grid.innerHTML = '<div class="wm-empty">此文件夹为空</div>';
      this.body.appendChild(grid);
      return;
    }

    for (const entry of data.entries) {
      const item = this._createItem(entry, false);
      const targetPath = data.currentPath ? data.currentPath + "/" + entry.name : entry.name;

      item.addEventListener("click", (e) => {
        this._closeCtxMenu();
        if (entry.isDirectory) this.loadDirectory(targetPath);
      });
      if (entry.isWorkflow && !entry.isDirectory) {
        item.addEventListener("dblclick", () => this.openWorkflow(entry, targetPath));
      }
      item.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        this._showContextMenu(e.clientX, e.clientY, entry, targetPath);
      });

      grid.appendChild(item);
    }
    this.body.appendChild(grid);
  }

  _createItem(entry, isUp) {
    const item = document.createElement("div");
    item.className = "wm-item" + (entry.isDirectory ? " wm-item-folder" : entry.isWorkflow ? " wm-item-workflow" : "");
    const icon = document.createElement("div");
    icon.className = "wm-item-icon";
    if (isUp) {
      icon.textContent = "⬆";
    } else if (entry.isDirectory) {
      icon.textContent = "📁";
    } else if (entry.isWorkflow) {
      icon.textContent = "⚡";
    } else {
      icon.textContent = "📄";
    }
    item.appendChild(icon);
    const name = document.createElement("div");
    name.className = "wm-item-name";
    name.textContent = entry.name;
    item.appendChild(name);
    return item;
  }

  _showContextMenu(clientX, clientY, entry, targetPath) {
    this._closeCtxMenu();
    const menu = document.createElement("div");
    menu.className = "wm-context-menu";
    menu.style.left = clientX + "px";
    menu.style.top = clientY + "px";

    const addItem = (label, fn) => {
      const div = document.createElement("div");
      div.className = "wm-context-item";
      div.textContent = label;
      div.addEventListener("click", () => { this._closeCtxMenu(); fn(); });
      menu.appendChild(div);
    };

    addItem("✏️ 重命名", () => this._rename(entry, targetPath));
    addItem("📂 移动", () => this._move(entry, targetPath));
    const sep = document.createElement("div");
    sep.className = "wm-context-sep";
    menu.appendChild(sep);
    addItem("🗑️ 删除", () => this._delete(entry, targetPath));

    document.body.appendChild(menu);
    this._ctxMenu = menu;

    setTimeout(() => {
      document.addEventListener("click", this._ctxCloseHandler = () => this._closeCtxMenu(), { once: true });
    }, 0);
  }

  _closeCtxMenu() {
    if (this._ctxMenu) { this._ctxMenu.remove(); this._ctxMenu = null; }
    if (this._ctxCloseHandler) { document.removeEventListener("click", this._ctxCloseHandler); this._ctxCloseHandler = null; }
  }

  _closeModal() {
    if (this._modalOverlay) { this._modalOverlay.remove(); this._modalOverlay = null; }
  }

  _showModal(html) {
    this._closeModal();
    const overlay = document.createElement("div");
    overlay.className = "wm-modal-overlay";
    overlay.innerHTML = html;
    overlay.addEventListener("click", (e) => { if (e.target === overlay) this._closeModal(); });
    document.body.appendChild(overlay);
    this._modalOverlay = overlay;
    return overlay;
  }

  async _rename(entry, targetPath) {
    const overlay = this._showModal(`
      <div class="wm-modal">
        <h3>重命名</h3>
        <input type="text" id="wmRenameInput" value="${entry.name}" autofocus>
        <div class="wm-modal-btns">
          <button class="wm-modal-btn" id="wmRenameCancel">取消</button>
          <button class="wm-modal-btn wm-modal-btn-primary" id="wmRenameConfirm">确认</button>
        </div>
      </div>
    `);
    const input = overlay.querySelector("#wmRenameInput");
    input.focus();
    input.select();
    const doRename = async () => {
      const newName = input.value.trim();
      if (!newName) return;
      try {
        const resp = await fetch(`${API_BASE}/rename`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: targetPath, newName }),
        });
        if (!resp.ok) {
          const err = await resp.json();
          this._showToast(err.error || "重命名失败");
          return;
        }
        this._showToast("重命名成功");
        this._closeModal();
        this.loadDirectory(this.currentPath);
      } catch (e) {
        this._showToast("重命名失败: " + e.message);
      }
    };
    overlay.querySelector("#wmRenameConfirm").addEventListener("click", doRename);
    overlay.querySelector("#wmRenameCancel").addEventListener("click", () => this._closeModal());
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") doRename(); if (e.key === "Escape") this._closeModal(); });
  }

  async _move(entry, targetPath) {
    const overlay = this._showModal(`
      <div class="wm-modal">
        <h3>移动到</h3>
        <div class="wm-move-new">
          <input type="text" id="wmMoveNewDir" placeholder="新建文件夹名称...">
          <button id="wmMoveCreateDir">新建</button>
        </div>
        <div class="wm-move-list" id="wmMoveList">加载中...</div>
        <div class="wm-modal-btns">
          <button class="wm-modal-btn" id="wmMoveCancel">取消</button>
          <button class="wm-modal-btn wm-modal-btn-primary" id="wmMoveConfirm">移动到此</button>
        </div>
      </div>
    `);

    let selectedDir = "";
    const listEl = overlay.querySelector("#wmMoveList");

    const loadDirs = async () => {
      listEl.textContent = "加载中...";
      try {
        const resp = await fetch(`${API_BASE}/list?path=${encodeURIComponent(this.currentPath)}`);
        if (!resp.ok) { listEl.textContent = "加载失败"; return; }
        const data = await resp.json();
        listEl.innerHTML = "";
        const dirs = data.entries.filter(e => e.isDirectory);
        if (dirs.length === 0) {
          listEl.innerHTML = '<div style="padding:12px;color:#666;text-align:center;">暂无子文件夹</div>';
          return;
        }
        for (const dir of dirs) {
          const item = document.createElement("div");
          item.className = "wm-move-item";
          item.textContent = "📁 " + dir.name;
          const fullPath = this.currentPath ? this.currentPath + "/" + dir.name : dir.name;
          item.addEventListener("click", () => {
            listEl.querySelectorAll(".wm-move-item").forEach(el => el.classList.remove("selected"));
            item.classList.add("selected");
            selectedDir = fullPath;
          });
          item.addEventListener("dblclick", () => {
            selectedDir = fullPath;
            doMove();
          });
          listEl.appendChild(item);
        }
      } catch (e) {
        listEl.textContent = "加载失败";
      }
    };

    const doMove = async () => {
      if (!selectedDir) { this._showToast("请选择一个目标文件夹"); return; }
      try {
        const resp = await fetch(`${API_BASE}/move`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: targetPath, destDir: selectedDir }),
        });
        if (!resp.ok) {
          const err = await resp.json();
          this._showToast(err.error || "移动失败");
          return;
        }
        this._showToast("移动成功");
        this._closeModal();
        this.loadDirectory(this.currentPath);
      } catch (e) {
        this._showToast("移动失败: " + e.message);
      }
    };

    overlay.querySelector("#wmMoveCreateDir").addEventListener("click", async () => {
      const name = overlay.querySelector("#wmMoveNewDir").value.trim();
      if (!name) { this._showToast("请输入文件夹名称"); return; }
      selectedDir = this.currentPath ? this.currentPath + "/" + name : name;
      doMove();
    });
    overlay.querySelector("#wmMoveConfirm").addEventListener("click", doMove);
    overlay.querySelector("#wmMoveCancel").addEventListener("click", () => this._closeModal());

    loadDirs();
  }

  async _delete(entry, targetPath) {
    const overlay = this._showModal(`
      <div class="wm-modal">
        <h3>确认删除</h3>
        <p style="color:#ccc;font-size:13px;margin-bottom:16px;">确定要删除 "<strong>${entry.name}</strong>" 吗？${entry.isDirectory ? '<br>文件夹内的所有内容将被删除。' : ''}</p>
        <div class="wm-modal-btns">
          <button class="wm-modal-btn" id="wmDeleteCancel">取消</button>
          <button class="wm-modal-btn wm-modal-btn-danger" id="wmDeleteConfirm">删除</button>
        </div>
      </div>
    `);
    const doDelete = async () => {
      try {
        const resp = await fetch(`${API_BASE}/delete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: targetPath }),
        });
        if (!resp.ok) {
          const err = await resp.json();
          this._showToast(err.error || "删除失败");
          return;
        }
        this._showToast("删除成功");
        this._closeModal();
        this.loadDirectory(this.currentPath);
      } catch (e) {
        this._showToast("删除失败: " + e.message);
      }
    };
    overlay.querySelector("#wmDeleteConfirm").addEventListener("click", doDelete);
    overlay.querySelector("#wmDeleteCancel").addEventListener("click", () => this._closeModal());
  }

  async openWorkflow(entry, targetPath) {
    this.close();
    try {
      const resp = await api.getUserData('workflows/' + targetPath);
      if (!resp.ok) { this._showToast("打开失败"); return; }
      const data = await resp.json();
      if (typeof app.loadGraphData === "function") {
        app.loadGraphData(data);
      } else {
        app.graph.clear();
        app.graph.deserialize(data);
        app.graph.setDirtyCanvas(true, true);
      }
      app._cjWorkflowPath = 'workflows/' + targetPath;
      this._showIndicator(entry.name || targetPath);
      this._showToast('已打开: ' + (entry.name || targetPath));
    } catch (e) {
      this._showToast("打开失败: " + e.message);
    }
  }

  _showIndicator(name) {
    let el = document.getElementById('cj-wm-indicator');
    if (!el) {
      el = document.createElement('div');
      el.id = 'cj-wm-indicator';
      el.style.cssText = 'position:fixed;bottom:4px;left:50%;transform:translateX(-50%);background:#1a5a2a;color:#cfc;padding:2px 14px;font-size:11px;border-radius:4px;z-index:9998;pointer-events:none;white-space:nowrap;font-family:sans-serif;border:1px solid #2a8a4a;';
      document.body.appendChild(el);
    }
    el.textContent = name;
    el.style.display = '';
  }

  _hideIndicator() {
    const el = document.getElementById('cj-wm-indicator');
    if (el) el.style.display = 'none';
  }

  _showToast(msg) {
    let toast = document.querySelector(".wm-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "wm-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => toast.classList.remove("show"), 2500);
  }
}

const wmDialog = new WorkflowManagerDialog();

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
        tooltip: "浏览workflows文件夹",
        content: "流程管理",
        classList: "comfyui-button cj-menu-btn",
        action: () => wmDialog.open()
      })
    );

    document.addEventListener('keydown', async (e) => {
      if (!app._cjWorkflowPath) return;
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        if (e.target.closest('input, textarea')) return;
        e.preventDefault();
        e.stopImmediatePropagation();
        const ok = await saveWorkflowToPath(app._cjWorkflowPath);
        wmDialog._showToast(ok ? '已保存到原文件' : '保存失败');
      }
    }, true);
  }
});
