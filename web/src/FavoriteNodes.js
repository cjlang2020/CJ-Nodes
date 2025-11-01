import { app } from "../../../scripts/app.js";
import { ComfyDialog, $el } from "../../../scripts/ui.js";
import { ComfyApp } from "../../../scripts/app.js";

class FavoriteNodes {
    constructor() {
        this.panel = null;
        this.isDragging = false;
        this.offset = { x: 0, y: 0 };
        this.initPanel();
    }

    // 初始化面板
    initPanel() {
        // 创建面板元素
        this.panel = document.createElement('div');
        this.panel.className = 'comfyui-floating-panel';
        this.panel.style.cssText = `
            position: fixed;
            top: 50px;
            right: 50px;
            width: 300px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 1000;
            overflow: hidden;
        `;

        // 添加标题栏
        const titleBar = document.createElement('div');
        titleBar.className = 'panel-title-bar';
        titleBar.style.cssText = `
            padding: 8px 12px;
            background: #3a3a3a;
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;
        titleBar.textContent = '常用节点';

        // 添加关闭按钮
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '×';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: #ccc;
            cursor: pointer;
            font-size: 16px;
            padding: 0 5px;
        `;
        closeBtn.addEventListener('click', () => this.hide());
        titleBar.appendChild(closeBtn);

        // 添加面板内容
        const content = document.createElement('div');
        content.className = 'panel-content';
        content.style.cssText = `
            padding: 12px;
            color: #fff;
        `;
        content.innerHTML = `
            <p>这是一个悬浮面板示例,目前没啥用</p>
            <button id="panel-action">面板按钮</button>
        `;

        // 组装面板
        this.panel.appendChild(titleBar);
        this.panel.appendChild(content);

        // 添加到文档
        document.body.appendChild(this.panel);

        // 初始化事件监听
        this.initEvents(titleBar);
    }

    // 初始化事件
    initEvents(titleBar) {
        // 拖拽功能
        titleBar.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            const rect = this.panel.getBoundingClientRect();
            this.offset.x = e.clientX - rect.left;
            this.offset.y = e.clientY - rect.top;
            this.panel.style.transition = 'none';
        });

        document.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const x = e.clientX - this.offset.x;
                const y = e.clientY - this.offset.y;
                this.panel.style.left = `${x}px`;
                this.panel.style.top = `${y}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.panel.style.transition = 'left 0.1s, top 0.1s';
        });

        // 面板按钮事件
        this.panel.querySelector('#panel-action').addEventListener('click', () => {
            alert('面板按钮被点击');
        });
    }

    // 显示面板
    show() {
        this.panel.style.display = 'block';
    }

    // 隐藏面板
    hide() {
        this.panel.style.display = 'none';
    }

    // 切换面板显示状态
    toggle() {
        if (this.panel.style.display === 'none') {
            this.show();
        } else {
            this.hide();
        }
    }
};

export default new FavoriteNodes();