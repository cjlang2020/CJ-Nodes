import { app } from "../../../../scripts/app.js";
import { api } from "../../../../scripts/api.js";

const API_BASE = "/CJ-Nodes/api/local-resources";
const NODE_TYPES = {
  image: "LoadImage",
  audio: "LoadAudio",
  video: "VHS_LoadVideo",
};

const CSS = `
.lr-dialog-overlay {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 10000;
  display: flex; align-items: center; justify-content: center;
}
.lr-dialog {
  width: 85vw; height: 90vh;
  background: #1e1e1e; color: #e0e0e0;
  border: 1px solid #444; border-radius: 6px;
  display: flex; flex-direction: column; overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.lr-header {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; background: #2a2a2a;
  border-bottom: 1px solid #444; flex: 0 0 auto;
}
.lr-title { font-weight: 600; font-size: 14px; white-space: nowrap; }
.lr-breadcrumbs {
  display: flex; align-items: center; gap: 4px;
  flex: 1; overflow-x: auto; font-size: 13px;
  padding: 0 8px; white-space: nowrap;
}
.lr-breadcrumbs::-webkit-scrollbar { height: 3px; }
.lr-breadcrumbs::-webkit-scrollbar-thumb { background: #555; border-radius: 2px; }
.lr-breadcrumb-item {
  color: #8ab4f8; cursor: pointer; padding: 2px 4px;
  border-radius: 3px; flex-shrink: 0;
}
.lr-breadcrumb-item:hover { background: #333; }
.lr-breadcrumb-sep { color: #666; flex-shrink: 0; }
.lr-breadcrumb-current { color: #ccc; flex-shrink: 0; }
.lr-close-btn {
  background: transparent; border: none; color: #bbb;
  cursor: pointer; font-size: 20px; line-height: 1; padding: 0 6px;
}
.lr-close-btn:hover { color: #fff; }
.lr-body { flex: 1; overflow-y: auto; padding: 12px; }
.lr-body::-webkit-scrollbar { width: 6px; }
.lr-body::-webkit-scrollbar-thumb { background: #555; border-radius: 3px; }
.lr-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
}
.lr-item {
  display: flex; flex-direction: column; align-items: center;
  background: #2a2a2a; border: 1px solid #444;
  border-radius: 6px; cursor: pointer; overflow: hidden;
  transition: all 0.15s; padding: 6px;
  position: relative;
}
.lr-item:hover { border-color: #8ab4f8; background: #333; }
.lr-item-folder { border-color: #3a4a5a; }
.lr-item-folder:hover { border-color: #6a9fd8; }
.lr-item-filetype {
  position: absolute; top: 4px; right: 4px;
  background: rgba(0,0,0,0.6); color: #aaa;
  font-size: 9px; padding: 1px 5px; border-radius: 3px;
}
.lr-item-img {
  width: 100%; aspect-ratio: 1;
  object-fit: cover; border-radius: 4px;
  background: #1a1a1a;
}
.lr-item-icon {
  width: 100%; aspect-ratio: 1;
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; color: #888; border-radius: 4px;
  background: #222;
}
.lr-item-name {
  margin-top: 5px; font-size: 11px; color: #ccc;
  text-align: center; word-break: break-all;
  width: 100%; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.lr-empty {
  grid-column: 1 / -1; text-align: center; color: #888;
  padding: 40px 0; font-size: 14px;
}
.lr-loading {
  text-align: center; color: #888; padding: 40px 0; font-size: 14px;
}
.lr-toast {
  position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
  background: #333; color: #eee; padding: 8px 20px;
  border-radius: 6px; font-size: 13px; z-index: 10001;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  opacity: 0; transition: opacity 0.3s;
}
.lr-toast.show { opacity: 1; }
.lr-context-menu {
  position: fixed; z-index: 10002;
  background: #2a2a2a; border: 1px solid #555;
  border-radius: 6px; padding: 4px 0; min-width: 140px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}
.lr-context-item {
  padding: 7px 16px; font-size: 13px; color: #ddd;
  cursor: pointer; white-space: nowrap;
}
.lr-context-item:hover { background: #3a3a3a; color: #fff; }
.lr-context-sep {
  height: 1px; background: #444; margin: 4px 0;
}
.lr-modal-overlay {
  position: fixed; inset: 0; z-index: 10003;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
}
.lr-modal {
  background: #2a2a2a; border: 1px solid #555;
  border-radius: 8px; padding: 20px; min-width: 320px; max-width: 500px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.lr-modal h3 { font-size: 15px; margin: 0 0 12px; color: #eee; }
.lr-modal input {
  width: 100%; padding: 8px 10px; border: 1px solid #555;
  border-radius: 4px; background: #1e1e1e; color: #eee; font-size: 13px;
  box-sizing: border-box; margin-bottom: 12px;
}
.lr-modal input:focus { outline: none; border-color: #8ab4f8; }
.lr-modal-btns { display: flex; gap: 8px; justify-content: flex-end; }
.lr-modal-btn {
  padding: 6px 16px; border: 1px solid #555; border-radius: 4px;
  background: #3a3a3a; color: #eee; cursor: pointer; font-size: 13px;
}
.lr-modal-btn:hover { background: #4a4a4a; }
.lr-modal-btn-primary { background: #2563eb; border-color: #3b82f6; }
.lr-modal-btn-primary:hover { background: #1d4ed8; }
.lr-modal-btn-danger { background: #dc2626; border-color: #ef4444; }
.lr-modal-btn-danger:hover { background: #b91c1c; }
.lr-move-list {
  max-height: 300px; overflow-y: auto; margin-bottom: 12px;
  border: 1px solid #444; border-radius: 4px; background: #1e1e1e;
}
.lr-move-item {
  padding: 8px 12px; cursor: pointer; font-size: 13px; color: #ccc;
  border-bottom: 1px solid #333;
}
.lr-move-item:hover, .lr-move-item.selected { background: #333; color: #fff; }
.lr-move-item:last-child { border-bottom: none; }
.lr-move-new {
  display: flex; gap: 6px; margin-bottom: 12px;
}
.lr-move-new input { flex: 1; margin-bottom: 0; }
.lr-move-new button {
  padding: 6px 12px; border: 1px solid #555; border-radius: 4px;
  background: #2563eb; color: #eee; cursor: pointer; font-size: 12px; white-space: nowrap;
}
.lr-move-new button:hover { background: #1d4ed8; }
.lr-filterbar {
  display: flex; align-items: center; gap: 14px;
  padding: 6px 14px; background: #222; border-bottom: 1px solid #444;
  flex: 0 0 auto; font-size: 13px;
}
.lr-filterbar label {
  display: flex; align-items: center; gap: 5px;
  cursor: pointer; color: #bbb; user-select: none;
}
.lr-filterbar input[type="checkbox"] { accent-color: #3b82f6; cursor: pointer; }
.lr-filter-label { font-size: 12px; color: #888; white-space: nowrap; }
`;

class LocalResourcesDialog {
  constructor() {
    this.overlay = null;
    this.dialog = null;
    this.body = null;
    this.breadcrumbs = null;
    this._filterBar = null;
    this.styleInjected = false;
    this.currentPath = "";
    this.currentData = null;
    this._ctxMenu = null;
    this._modalOverlay = null;
    this._filter = { image: true, audio: true, video: true };
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
    this.overlay.className = "lr-dialog-overlay";
    this.overlay.addEventListener("click", (e) => { if (e.target === this.overlay) this.close(); });

    this.dialog = document.createElement("div");
    this.dialog.className = "lr-dialog";

    const header = document.createElement("div");
    header.className = "lr-header";
    const title = document.createElement("span");
    title.className = "lr-title";
    title.textContent = "本地资源";
    this.breadcrumbs = document.createElement("div");
    this.breadcrumbs.className = "lr-breadcrumbs";
    const closeBtn = document.createElement("button");
    closeBtn.className = "lr-close-btn";
    closeBtn.textContent = "✕";
    closeBtn.addEventListener("click", () => this.close());
    header.appendChild(title);
    header.appendChild(this.breadcrumbs);
    header.appendChild(closeBtn);
    this.dialog.appendChild(header);

    this._filterBar = document.createElement("div");
    this._filterBar.className = "lr-filterbar";
    const filterLabel = document.createElement("span");
    filterLabel.className = "lr-filter-label";
    filterLabel.textContent = "过滤:";
    this._filterBar.appendChild(filterLabel);
    for (const [key, label] of [["image", "图片"], ["audio", "音频"], ["video", "视频"]]) {
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = true;
      cb.dataset.type = key;
      const lbl = document.createElement("label");
      lbl.appendChild(cb);
      lbl.appendChild(document.createTextNode(label));
      lbl.addEventListener("change", () => {
        this._filter[key] = cb.checked;
        this._renderFilteredGrid();
      });
      this._filterBar.appendChild(lbl);
    }
    this.dialog.appendChild(this._filterBar);

    this.body = document.createElement("div");
    this.body.className = "lr-body";
    this.dialog.appendChild(this.body);

    this.overlay.appendChild(this.dialog);
    document.body.appendChild(this.overlay);
  }

  async loadDirectory(relPath) {
    if (!this.body) return;
    this.body.innerHTML = '<div class="lr-loading">加载中...</div>';
    try {
      const resp = await fetch(`${API_BASE}/list?path=${encodeURIComponent(relPath)}`);
      if (!resp.ok) { this.body.innerHTML = '<div class="lr-empty">加载失败</div>'; return; }
      this.currentData = await resp.json();
      this.currentPath = this.currentData.currentPath || "";
      this.renderBreadcrumbs(this.currentData.currentPath || "");
      this.renderGrid(this.currentData);
    } catch (e) {
      this.body.innerHTML = '<div class="lr-empty">加载失败: ' + e.message + '</div>';
    }
  }

  renderBreadcrumbs(currentPath) {
    this.breadcrumbs.innerHTML = "";
    const rootItem = document.createElement("span");
    rootItem.className = "lr-breadcrumb-item";
    rootItem.textContent = "output";
    rootItem.addEventListener("click", () => this.loadDirectory(""));
    this.breadcrumbs.appendChild(rootItem);
    if (!currentPath) return;
    const parts = currentPath.split("/");
    let accumulated = "";
    for (const part of parts) {
      if (!part) continue;
      accumulated += (accumulated ? "/" : "") + part;
      const sep = document.createElement("span");
      sep.className = "lr-breadcrumb-sep";
      sep.textContent = "›";
      this.breadcrumbs.appendChild(sep);
      if (part === parts[parts.length - 1]) {
        const current = document.createElement("span");
        current.className = "lr-breadcrumb-current";
        current.textContent = part;
        this.breadcrumbs.appendChild(current);
      } else {
        const item = document.createElement("span");
        item.className = "lr-breadcrumb-item";
        item.textContent = part;
        item.addEventListener("click", () => this.loadDirectory(accumulated));
        this.breadcrumbs.appendChild(item);
      }
    }
  }

  renderGrid(data) {
    this.body.innerHTML = "";
    const grid = document.createElement("div");
    grid.className = "lr-grid";

    if (data.parentPath != null) {
      const upItem = this._createItem({ name: "..", isDirectory: true, fileType: null }, true);
      upItem.addEventListener("click", () => this.loadDirectory(data.parentPath));
      grid.appendChild(upItem);
    }

    if (!data.entries || data.entries.length === 0) {
      grid.innerHTML = '<div class="lr-empty">此文件夹为空</div>';
      this.body.appendChild(grid);
      return;
    }

    let entries = data.entries;
    const hasFilter = Object.values(this._filter).some(v => !v);
    if (hasFilter) {
      entries = entries.filter(e => !e.fileType || this._filter[e.fileType]);
    }

    if (entries.length === 0) {
      grid.innerHTML = '<div class="lr-empty">无匹配项</div>';
      this.body.appendChild(grid);
      return;
    }

    for (const entry of entries) {
      const item = this._createItem(entry, false);
      const targetPath = data.currentPath ? data.currentPath + "/" + entry.name : entry.name;

      item.addEventListener("click", (e) => {
        this._closeCtxMenu();
        if (entry.isDirectory) this.loadDirectory(targetPath);
      });
      if (entry.fileType && !entry.isDirectory) {
        item.addEventListener("dblclick", () => this.addToWorkflow(entry, targetPath));
      }
      item.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        this._showContextMenu(e.clientX, e.clientY, entry, targetPath);
      });

      grid.appendChild(item);
    }
    this.body.appendChild(grid);
  }

  _renderFilteredGrid() {
    if (this.currentData) this.renderGrid(this.currentData);
  }

  _createItem(entry, isUp) {
    const item = document.createElement("div");
    item.className = "lr-item" + (entry.isDirectory ? " lr-item-folder" : "");
    if (isUp) {
      const icon = document.createElement("div");
      icon.className = "lr-item-icon"; icon.textContent = "⬆"; item.appendChild(icon);
    } else if (entry.isDirectory) {
      const icon = document.createElement("div");
      icon.className = "lr-item-icon"; icon.textContent = "📁"; item.appendChild(icon);
    } else if (entry.fileType === "image") {
      const img = document.createElement("img");
      img.className = "lr-item-img"; img.src = entry.thumbUrl; img.loading = "lazy"; item.appendChild(img);
    } else {
      const icon = document.createElement("div");
      icon.className = "lr-item-icon";
      icon.textContent = { audio: "🎵", video: "🎬" }[entry.fileType] || "📄";
      item.appendChild(icon);
    }
    if (entry.fileType && !entry.isDirectory) {
      const badge = document.createElement("span");
      badge.className = "lr-item-filetype"; badge.textContent = entry.fileType; item.appendChild(badge);
    }
    const name = document.createElement("div");
    name.className = "lr-item-name"; name.textContent = entry.name; item.appendChild(name);
    return item;
  }

  _showContextMenu(clientX, clientY, entry, targetPath) {
    this._closeCtxMenu();
    const menu = document.createElement("div");
    menu.className = "lr-context-menu";
    menu.style.left = clientX + "px";
    menu.style.top = clientY + "px";

    const addItem = (label, fn) => {
      const div = document.createElement("div");
      div.className = "lr-context-item";
      div.textContent = label;
      div.addEventListener("click", () => { this._closeCtxMenu(); fn(); });
      menu.appendChild(div);
    };

    addItem("✏️ 重命名", () => this._rename(entry, targetPath));
    addItem("📂 移动", () => this._move(entry, targetPath));
    const sep = document.createElement("div");
    sep.className = "lr-context-sep";
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
    overlay.className = "lr-modal-overlay";
    overlay.innerHTML = html;
    overlay.addEventListener("click", (e) => { if (e.target === overlay) this._closeModal(); });
    document.body.appendChild(overlay);
    this._modalOverlay = overlay;
    return overlay;
  }

  async _rename(entry, targetPath) {
    const overlay = this._showModal(`
      <div class="lr-modal">
        <h3>重命名</h3>
        <input type="text" id="lrRenameInput" value="${entry.name}" autofocus>
        <div class="lr-modal-btns">
          <button class="lr-modal-btn" id="lrRenameCancel">取消</button>
          <button class="lr-modal-btn lr-modal-btn-primary" id="lrRenameConfirm">确认</button>
        </div>
      </div>
    `);
    const input = overlay.querySelector("#lrRenameInput");
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
    overlay.querySelector("#lrRenameConfirm").addEventListener("click", doRename);
    overlay.querySelector("#lrRenameCancel").addEventListener("click", () => this._closeModal());
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") doRename(); if (e.key === "Escape") this._closeModal(); });
  }

  async _move(entry, targetPath) {
    const overlay = this._showModal(`
      <div class="lr-modal">
        <h3>移动到</h3>
        <div class="lr-move-new">
          <input type="text" id="lrMoveNewDir" placeholder="新建文件夹名称...">
          <button id="lrMoveCreateDir">新建</button>
        </div>
        <div class="lr-move-list" id="lrMoveList">加载中...</div>
        <div class="lr-modal-btns">
          <button class="lr-modal-btn" id="lrMoveCancel">取消</button>
          <button class="lr-modal-btn lr-modal-btn-primary" id="lrMoveConfirm">移动到此</button>
        </div>
      </div>
    `);

    let selectedDir = "";
    const listEl = overlay.querySelector("#lrMoveList");

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
          item.className = "lr-move-item";
          item.textContent = "📁 " + dir.name;
          const fullPath = this.currentPath ? this.currentPath + "/" + dir.name : dir.name;
          item.addEventListener("click", () => {
            listEl.querySelectorAll(".lr-move-item").forEach(el => el.classList.remove("selected"));
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

    overlay.querySelector("#lrMoveCreateDir").addEventListener("click", async () => {
      const name = overlay.querySelector("#lrMoveNewDir").value.trim();
      if (!name) { this._showToast("请输入文件夹名称"); return; }
      selectedDir = this.currentPath ? this.currentPath + "/" + name : name;
      doMove();
    });
    overlay.querySelector("#lrMoveConfirm").addEventListener("click", doMove);
    overlay.querySelector("#lrMoveCancel").addEventListener("click", () => this._closeModal());

    loadDirs();
  }

  async _delete(entry, targetPath) {
    const overlay = this._showModal(`
      <div class="lr-modal">
        <h3>确认删除</h3>
        <p style="color:#ccc;font-size:13px;margin-bottom:16px;">确定要删除 "<strong>${entry.name}</strong>" 吗？${entry.isDirectory ? '<br>文件夹内的所有内容将被删除。' : ''}</p>
        <div class="lr-modal-btns">
          <button class="lr-modal-btn" id="lrDeleteCancel">取消</button>
          <button class="lr-modal-btn lr-modal-btn-danger" id="lrDeleteConfirm">删除</button>
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
    overlay.querySelector("#lrDeleteConfirm").addEventListener("click", doDelete);
    overlay.querySelector("#lrDeleteCancel").addEventListener("click", () => this._closeModal());
  }

  async addToWorkflow(entry, targetPath) {
    const nodeType = NODE_TYPES[entry.fileType];
    if (!nodeType) return;
    this.close();
    try {
      const resp = await fetch(`${API_BASE}/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: targetPath }),
      });
      if (!resp.ok) { this._showToast(`导入失败: ${resp.status}`); return; }
      const { filename } = await resp.json();
      if (!LiteGraph.registered_node_types[nodeType]) {
        this._showToast(`节点类型 "${nodeType}" 未安装`);
        return;
      }
      const canvas = app.canvas;
      const centerX = (-canvas.ds.offset[0] + canvas.width / 2) / canvas.ds.scale;
      const centerY = (-canvas.ds.offset[1] + canvas.height / 2) / canvas.ds.scale;
      const node = LiteGraph.createNode(nodeType);
      if (!node) { this._showToast("创建节点失败"); return; }
      node.configure({
        type: nodeType,
        pos: [centerX - 135, centerY - 157],
        widgets_values: [`${filename} [output]`],
      });
      app.graph.add(node);
      app.graph.setDirtyCanvas(true, true);
      this._showToast(`已添加: ${entry.name}`);
    } catch (e) {
      this._showToast("添加失败: " + e.message);
    }
  }

  _showToast(msg) {
    let toast = document.querySelector(".lr-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "lr-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => toast.classList.remove("show"), 2500);
  }
}

const dialog = new LocalResourcesDialog();

app.registerExtension({
  name: "CJ-Nodes.LocalResources",
  setup() {
    const { ComfyButton } = window.comfyAPI.button;
    app.menu?.settingsGroup.append(
      new ComfyButton({
        icon: "folder-open",
        tooltip: "浏览output文件夹",
        content: "本地资源",
        action: () => dialog.open()
      })
    );
  }
});
