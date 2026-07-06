import { app } from "../../../../scripts/app.js";

const HANDLE = 8;
const COLORS = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e"];

let currentNode = null;

function injectStyles() {
    if (document.getElementById("cj-er-style")) return;
    const s = document.createElement("style");
    s.id = "cj-er-style";
    s.textContent = `
        .cj-er{display:flex;flex-direction:column;gap:6px;padding:4px;font:12px sans-serif;color:#ccc;overflow-y:auto}
        .cj-er-r{display:flex;align-items:center;gap:6px}
        .cj-er-l{width:60px;flex:0 0 auto;color:#aaa;font-size:11px;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-er-i{flex:1;min-width:0;background:#1a1a1a;border:1px solid #444;border-radius:4px;color:#ddd;font:12px monospace;padding:3px 6px;outline:none}
        .cj-er-i:focus{border-color:#46b4e6}
        .cj-er-ta{flex:1;min-width:0;background:#1a1a1a;border:1px solid #444;border-radius:4px;color:#ddd;font:12px monospace;padding:3px 6px;outline:none;resize:vertical;min-height:44px;font-family:monospace;line-height:1.4}
        .cj-er-ta:focus{border-color:#46b4e6}
        .cj-er-btn{background:#333;border:1px solid #555;border-radius:4px;color:#bbb;font:11px sans-serif;cursor:pointer;padding:2px 8px;line-height:18px;white-space:nowrap}
        .cj-er-btn:hover{border-color:#46b4e6;color:#fff}
        .cj-er-cv{flex:1 1 auto;min-height:200px;display:flex;flex-direction:column;align-items:center;overflow:hidden;position:relative;background:#111;border:1px solid #444;border-radius:4px;padding:6px}
        .cj-er-upload-row{display:flex;align-items:center;gap:8px;margin-bottom:4px;width:100%}
        .cj-er-canvas{cursor:crosshair;display:block;flex:0 0 auto;border-radius:4px;outline:none;touch-action:none;min-width:100px;min-height:100px}
        .cj-er-panel{width:100%;box-sizing:border-box;background:#1d1d1d;border:1px solid #444;border-radius:4px;padding:6px 8px;font:11px sans-serif;color:#bbb;min-height:32px;max-height:90px;overflow-y:auto}
    `;
    document.head.appendChild(s);
}

function mkRow(label) {
    const r = document.createElement("div"); r.className = "cj-er-r";
    if (label) { const l = document.createElement("span"); l.className = "cj-er-l"; l.textContent = label; r.appendChild(l); }
    return r;
}

function clamp01(v) { return Math.max(0, Math.min(1, v)); }
function normBox(b) {
    let {x,y,w,h} = b;
    if (w<0){x+=w;w=-w;} if (h<0){y+=h;h=-h;}
    x=clamp01(x); y=clamp01(y); w=Math.min(w,1-x); h=Math.min(h,1-y);
    return {...b,x,y,w:Math.max(0,w),h:Math.max(0,h)};
}
function rectHitN(mx,my,x1,y1,x2,y2,rx,ry) {
    const h=(cx,cy)=>Math.abs(mx-cx)<rx&&Math.abs(my-cy)<ry;
    if(h(x1,y1))return"tl"; if(h(x2,y1))return"tr"; if(h(x1,y2))return"bl"; if(h(x2,y2))return"br";
    if(mx>=x1&&mx<=x2&&Math.abs(my-y1)<ry)return"t"; if(mx>=x1&&mx<=x2&&Math.abs(my-y2)<ry)return"b";
    if(my>=y1&&my<=y2&&Math.abs(mx-x1)<rx)return"l"; if(my>=y1&&my<=y2&&Math.abs(mx-x2)<rx)return"r";
    if(mx>=x1&&mx<=x2&&my>=y1&&my<=y2)return"move";
    return null;
}
function applyDrag(mode,start,dx,dy) {
    const {x,y,w,h}=start;
    if(mode==="move")return{...start,x:clamp01(Math.min(x+dx,1-w)),y:clamp01(Math.min(y+dy,1-h))};
    if(mode==="draw"){const ax=clamp01(x),ay=clamp01(y),cx=clamp01(x+dx),cy=clamp01(y+dy);return{...start,x:Math.min(ax,cx),y:Math.min(ay,cy),w:Math.abs(cx-ax),h:Math.abs(cy-ay)};}
    const s=mode;let l=x,t=y,r=x+w,b=y+h;
    if(s.includes("l"))l=clamp01(l+dx); if(s.includes("r"))r=clamp01(r+dx);
    if(s.includes("t"))t=clamp01(t+dy); if(s.includes("b"))b=clamp01(b+dy);
    if(r<l)[l,r]=[r,l]; if(b<t)[t,b]=[b,t];
    return{...start,x:l,y:t,w:r-l,h:b-t};
}

function buildCanvas(node) {
    const s = node._er;
    const cvWrap = document.createElement("div"); cvWrap.className = "cj-er-cv";
    const canvas = document.createElement("canvas"); canvas.className = "cj-er-canvas"; canvas.tabIndex = 0;
    const ctx = canvas.getContext("2d");
    node._cvEl = canvas; node._cvCtx = ctx;

    let drawing = false, dragMode = null, dragStart = null, boxStart = null;
    let imgEl = null, imgW = 0, imgH = 0;
    node._erImgEl = null;

    function logW() { return canvas.offsetWidth || 1; }
    function logH() { return canvas.offsetHeight || 1; }
    function mouseN(e) { const r = canvas.getBoundingClientRect(); return { x: (e.clientX-r.left)/r.width, y: (e.clientY-r.top)/r.height }; }
    function mouseNClamped(e) { const r = canvas.getBoundingClientRect(); return { x: Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)), y: Math.max(0,Math.min(1,(e.clientY-r.top)/r.height)) }; }
    function toPx(b) { const W=logW(),H=logH(); return {x1:b.x*W,y1:b.y*H,x2:(b.x+b.w)*W,y2:(b.y+b.h)*H}; }

    function boxesAt(mN) {
        const baseRx=HANDLE/logW(),baseRy=HANDLE/logH();
        const res=[];
        for(let i=0;i<s.edit_items.length;i++){
            const b=s.edit_items[i];
            const rx=Math.min(baseRx,b.w/3||baseRx),ry=Math.min(baseRy,b.h/3||baseRy);
            const mode=rectHitN(mN.x,mN.y,b.x,b.y,b.x+b.w,b.y+b.h,rx,ry);
            if(mode)res.push({index:i,mode});
        }
        const ai=res.findIndex(c=>c.index===s.activeIndex);
        if(ai>0)res.unshift(res.splice(ai,1)[0]);
        return res;
    }

    function draw() {
        const W=logW()||100,H=logH()||100,d=window.devicePixelRatio||1;
        const bw=Math.round(W*d),bh=Math.round(H*d);
        if(canvas.width!==bw||canvas.height!==bh){canvas.width=bw;canvas.height=bh;}
        ctx.setTransform(d,0,0,d,0,0);
        ctx.clearRect(0,0,W,H);

        if (imgEl) {
            const scale = Math.min(W/imgW, H/imgH);
            const iw = imgW * scale, ih = imgH * scale;
            const ix = (W - iw) / 2, iy = (H - ih) / 2;
            ctx.drawImage(imgEl, ix, iy, iw, ih);
            node._imgInfo = { ix, iy, iw, ih, scale, imgW, imgH };
        } else {
            ctx.fillStyle="#CCCCCC"; ctx.fillRect(0,0,W,H);
            ctx.fillStyle="#999"; ctx.font="14px sans-serif"; ctx.textAlign="center";
            ctx.fillText("请上传一张图片", W/2, H/2-10);
            ctx.fillStyle="#777"; ctx.font="12px sans-serif";
            ctx.fillText("点击上方「上传图片」按钮", W/2, H/2+12);
            node._imgInfo = null;
        }

        for(let i=0;i<s.edit_items.length;i++){
            const b=s.edit_items[i],active=i===s.activeIndex;
            const{x1,y1,x2,y2}=toPx(b);
            const w=x2-x1,h=y2-y1;
            if(w<1||h<1)continue;
            const col=COLORS[i%COLORS.length];
            ctx.fillStyle=col+"33"; ctx.fillRect(x1,y1,w,h);
            ctx.strokeStyle=col; ctx.lineWidth=active?2:1.5;
            ctx.strokeRect(x1+0.5,y1+0.5,w-1,h-1);
            if(active){ctx.strokeStyle="#ff8c00";ctx.lineWidth=2;ctx.strokeRect(x1+1,y1+1,w-2,h-2);}
            const tag=String(i+1);
            ctx.font="bold 11px monospace"; const tw=ctx.measureText(tag).width+8;
            ctx.fillStyle=col; ctx.fillRect(x1,y1,tw,15);
            ctx.fillStyle="#fff"; ctx.fillText(tag,x1+4,y1+12);
            // edit_text display on region
            if (b.edit_text) {
                ctx.save(); ctx.beginPath(); ctx.rect(x1, y1, w, h); ctx.clip();
                ctx.font = "10px monospace";
                const textCol = active ? "#fff" : col;
                ctx.fillStyle = textCol;
                const lines = wrapText(ctx, b.edit_text, w-8);
                const lineH = 12;
                const totalH = lines.length * lineH;
                let ty = y1 + (h - totalH) / 2 + lineH;
                ctx.textAlign = "center";
                for (const ln of lines) { if (ty > y2-2) break; ctx.fillText(ln, x1+w/2, ty); ty += lineH; }
                ctx.restore();
            }
            if(active){
                const hs=5;
                for(const[px,py]of[[x1,y1],[x2,y1],[x1,y2],[x2,y2],[x1+w/2,y1],[x1+w/2,y2],[x1,y1+h/2],[x2,y1+h/2]]){
                    ctx.fillStyle="#ff8c00"; ctx.fillRect(px-hs,py-hs,hs*2,hs*2);
                }
            }
        }
    }
    function wrapText(c, text, maxW) {
        const lines = [];
        for (const para of text.split("\n")) {
            let line = "";
            for (const word of para.split(/\s+/)) {
                if (!word) continue;
                const test = line ? line + " " + word : word;
                if (line && c.measureText(test).width > maxW) { lines.push(line); line = word; }
                else line = test;
            }
            lines.push(line);
        }
        return lines;
    }

    function fitCanvas() {
        if(cvWrap.offsetParent===null)return;
        const availW=cvWrap.clientWidth-12,availH=cvWrap.clientHeight-12;
        if(availW<4||availH<4)return;
        const aspect = 4/3;
        let cw=availW,ch=cw/aspect;
        if(ch>availH){ch=availH;cw=ch*aspect;}
        canvas.style.width=Math.round(cw)+"px";
        canvas.style.height=Math.round(ch)+"px";
        draw();
    }

    try{
        node._erVisObs=new IntersectionObserver((entries)=>{
            if(entries.some(en=>en.isIntersecting))fitCanvas();
        });
        node._erVisObs.observe(cvWrap);
    }catch(e){}
    try{
        node._erResizeObs=new ResizeObserver(()=>fitCanvas());
        node._erResizeObs.observe(cvWrap);
    }catch(e){}

    function loadImageFromDataUrl(dataUrl) {
        const img = new Image();
        img.onload = () => {
            imgEl = img;
            imgW = img.naturalWidth;
            imgH = img.naturalHeight;
            s.image_width = imgW;
            s.image_height = imgH;
            fitCanvas();
            saveState(node);
        };
        img.src = dataUrl;
    }
    node._erLoadImage = loadImageFromDataUrl;
    // Restore image if exists in state
    if (s.image_data) loadImageFromDataUrl(s.image_data);

    canvas.addEventListener("pointerdown",(e)=>{
        if(e.button!==0||!imgEl)return;
        canvas.focus();
        const mN=mouseN(e);
        const hits=rectHitN(mN.x,mN.y,0,0,1,1,0,0)?boxesAt(mN):[];
        if(hits.length>0){
            const hit=hits[0];
            s.activeIndex=hit.index; dragMode=hit.mode;
            boxStart={...s.edit_items[hit.index]}; dragStart=mN;
        } else {
            const nb={x:Math.max(0,Math.min(1,mN.x)),y:Math.max(0,Math.min(1,mN.y)),w:0,h:0,edit_text:""};
            s.edit_items.push(nb); s.activeIndex=s.edit_items.length-1;
            dragMode="draw"; boxStart={...nb}; dragStart=mN;
        }
        drawing=true;
        document.addEventListener("pointermove",onMove);
        document.addEventListener("pointerup",onUp);
        e.preventDefault();
    });

    function onMove(e){
        if(!drawing)return;
        const mN=mouseNClamped(e);
        const dx=mN.x-dragStart.x,dy=mN.y-dragStart.y;
        s.edit_items[s.activeIndex]=normBox(applyDrag(dragMode,boxStart,dx,dy));
        draw();
    }
    function onUp(){
        drawing=false;
        document.removeEventListener("pointermove",onMove);
        document.removeEventListener("pointerup",onUp);
        const b=s.edit_items[s.activeIndex];
        if(b&&(b.w<0.008||b.h<0.008)&&dragMode==="draw"){s.edit_items.splice(s.activeIndex,1);s.activeIndex=Math.min(s.activeIndex,s.edit_items.length-1);}
        dragMode=null;boxStart=null;dragStart=null;
        draw();
        saveState(node);
        renderPanel(node);
    }

    canvas.addEventListener("keydown",(e)=>{
        if((e.key==="Delete"||e.key==="Backspace")&&!e.target.closest("input,textarea")){
            if(s.activeIndex>=0&&s.activeIndex<s.edit_items.length){
                e.preventDefault();e.stopPropagation();
                s.edit_items.splice(s.activeIndex,1);
                s.activeIndex=Math.min(s.activeIndex,s.edit_items.length-1);
                draw();saveState(node);
                renderPanel(node);
            }
        }
    });

    node._cvFit=fitCanvas;
    node._cvDraw=draw;

    cvWrap.appendChild(canvas);
    return cvWrap;
}

function renderPanel(node) {
    const s = node._er;
    const panel = node._erPanel;
    if (!panel) return;
    panel.innerHTML = "";
    const b = s.edit_items[s.activeIndex];
    if (!b) {
        const hint = document.createElement("div");
        hint.style.color = "#888";
        hint.textContent = s.edit_items.length ? "点击区域进行编辑" : s.image_data ? "在画布上拖动创建编辑区域" : "请先上传图片";
        panel.appendChild(hint);
        return;
    }
    const col = COLORS[s.activeIndex % COLORS.length] || "#bbb";
    const hdr = document.createElement("div");
    hdr.style.cssText = "display:flex;align-items:center;gap:6px;margin-bottom:3px;";
    const tag = document.createElement("span");
    tag.style.cssText = `font-weight:bold;color:${col};`;
    tag.textContent = "\u7F16\u8F91\u533A\u57DF " + (s.activeIndex + 1);
    hdr.appendChild(tag);
    const delBtn = document.createElement("button");
    delBtn.className = "cj-er-btn";
    delBtn.textContent = "\u5220\u9664";
    delBtn.style.cssText = "margin-left:auto;padding:0 6px;line-height:16px;font-size:10px";
    delBtn.addEventListener("click", () => {
        s.edit_items.splice(s.activeIndex, 1);
        s.activeIndex = Math.min(s.activeIndex, s.edit_items.length - 1);
        renderPanel(node);
        node._cvDraw?.();
        saveState(node);
    });
    hdr.appendChild(delBtn);
    panel.appendChild(hdr);

    const editRow = document.createElement("div"); editRow.className = "cj-er-r";
    const editTa = document.createElement("textarea");
    editTa.className = "cj-er-ta";
    editTa.style.cssText = "min-height:36px;resize:none";
    editTa.rows = 2;
    editTa.value = b.edit_text || "";
    editTa.placeholder = "\u4F8B\u5982\uFF1A\u4FEE\u6539\u4E3A\u56FE3\u7684\u4EBA\u7269";
    editTa.addEventListener("input", () => { b.edit_text = editTa.value; node._cvDraw?.(); saveState(node); });
    editRow.appendChild(editTa);
    panel.appendChild(editRow);
}

function saveState(node) {
    const s = node._er;
    let imgW = 1, imgH = 1;
    if (node._imgInfo) { imgW = node._imgInfo.imgW; imgH = node._imgInfo.imgH; }
    const cw = node._cvEl?.offsetWidth || 1;
    const ch = node._cvEl?.offsetHeight || 1;
    const normW = node.widgets?.find(w => w.name === "normalize");
    const normalize = normW ? normW.value : true;
    const items = s.edit_items.map(item => {
        let bbox_px = [0, 0, 0, 0];
        if (node._imgInfo && node._imgInfo.scale > 0) {
            const { ix, iy, scale } = node._imgInfo;
            const px1 = Math.max(0, (item.x * cw - ix) / scale);
            const py1 = Math.max(0, (item.y * ch - iy) / scale);
            const px2 = Math.min(imgW, ((item.x + item.w) * cw - ix) / scale);
            const py2 = Math.min(imgH, ((item.y + item.h) * ch - iy) / scale);
            if (normalize) {
                bbox_px = [
                    Math.round(px1 / imgW * 1000),
                    Math.round(py1 / imgH * 1000),
                    Math.round(px2 / imgW * 1000),
                    Math.round(py2 / imgH * 1000)
                ];
            } else {
                bbox_px = [Math.round(px1), Math.round(py1), Math.round(px2), Math.round(py2)];
            }
        }
        return { edit_text: item.edit_text || "", bbox_px };
    });
    const data = { prompt_text: s.prompt_text, image_data: s.image_data, image_width: imgW, image_height: imgH, edit_items: items, normalize };
    const w = node.widgets?.find(w => w.name === "frontend_data");
    if (w) w.value = JSON.stringify(data);
}

function buildUI(node) {
    const s = node._er;
    const wrap = document.createElement("div"); wrap.className = "cj-er";

    const promptRow = mkRow("\u5168\u5C40\u63D0\u793A:");
    const promptTa = document.createElement("textarea");
    promptTa.className = "cj-er-ta";
    promptTa.placeholder = "\u4F8B\u5982\uFF1A\u6574\u4F53\u8272\u8C03\u548C\u56FE3\u76F8\u4F3C";
    promptTa.value = s.prompt_text || "";
    promptTa.addEventListener("input", () => { s.prompt_text = promptTa.value; saveState(node); });
    promptRow.appendChild(promptTa);
    wrap.appendChild(promptRow);

    // Upload row (outside canvas container, stays fixed)
    const uploadRow = document.createElement("div"); uploadRow.className = "cj-er-upload-row";
    const uploadBtn = document.createElement("button"); uploadBtn.className = "cj-er-btn";
    uploadBtn.textContent = "\uD83D\uDCC1 \u4E0A\u4F20\u56FE\u7247";
    const imgInfoSpan = document.createElement("span");
    imgInfoSpan.style.cssText = "color:#888;font-size:11px;";
    imgInfoSpan.textContent = s.image_data ? `\u5DF2\u52A0\u8F7D\u56FE\u7247 (${s.image_width||'?'}\u00D7${s.image_height||'?'})` : "\u672A\u9009\u62E9\u56FE\u7247";
    const fileInput = document.createElement("input"); fileInput.type = "file"; fileInput.accept = "image/*";
    fileInput.style.cssText = "display:none";
    uploadBtn.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            s.image_data = ev.target.result;
            s.edit_items = [];
            s.activeIndex = -1;
            if (node._erLoadImage) node._erLoadImage(s.image_data);
            imgInfoSpan.textContent = `${file.name} (${s.image_width||'?'}\u00D7${s.image_height||'?'})`;
            renderPanel(node);
        };
        reader.readAsDataURL(file);
    });
    uploadRow.append(uploadBtn, imgInfoSpan, fileInput);
    wrap.appendChild(uploadRow);
    node._erUploadInfo = imgInfoSpan;

    const panel = document.createElement("div"); panel.className = "cj-er-panel";
    node._erPanel = panel;
    wrap.appendChild(panel);

    const cvWrap = buildCanvas(node);
    wrap.appendChild(cvWrap);

    node.addDOMWidget("er_panel", "Edit Region", wrap, {
        getValue: () => JSON.stringify(node._er),
        setValue: v => { try { const d = JSON.parse(v); Object.assign(node._er, d); rebuildAll(node); } catch(e) {} }
    });

    rebuildAll(node);
    requestAnimationFrame(() => node._cvFit?.());
}

function rebuildAll(node) {
    const s = node._er;
    if (s.image_data && node._erLoadImage) {
        node._erLoadImage(s.image_data);
        if (node._erUploadInfo) node._erUploadInfo.textContent = `\u5DF2\u52A0\u8F7D\u56FE\u7247 (${s.image_width||'?'}\u00D7${s.image_height||'?'})`;
    }
    node._cvDraw?.();
    renderPanel(node);
}

function chainCallback(obj, prop, cb) {
    const old = obj[prop];
    obj[prop] = function(...args) { const r = old?.apply(this, args); cb.apply(this, args); return r; };
}

app.registerExtension({
    name: "CJNodes.EditRegion",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "EditRegionNode") return;
        injectStyles();
        chainCallback(nodeType.prototype, "onNodeCreated", function() {
            const node = this; currentNode = node;
            node._er = { prompt_text: "", image_data: "", image_width: 0, image_height: 0, edit_items: [], activeIndex: -1 };
            const pdW = node.widgets?.find(w => w.name === "frontend_data");
            if (pdW) {
                pdW.hidden = true;
                pdW.computeSize = () => [0, -4];
                if (pdW.value) {
                    try { const d = JSON.parse(pdW.value); Object.assign(node._er, d); if (!node._er.edit_items) node._er.edit_items = []; } catch(e) {}
                }
            }
            buildUI(node);

            const normW = node.widgets?.find(w => w.name === "normalize");
            if (normW) {
                const origCb = normW.callback;
                normW.callback = function(v) {
                    if (origCb) origCb(v);
                    saveState(node);
                };
            }

            node.setSize([Math.max(440, node.size[0]), Math.max(600, node.size[1])]);
            chainCallback(node, "onRemoved", () => {
                if (node._erVisObs) { node._erVisObs.disconnect(); node._erVisObs = null; }
                if (node._erResizeObs) { node._erResizeObs.disconnect(); node._erResizeObs = null; }
            });
        });
    }
});

console.log("CJ-Nodes EditRegionNode loaded");
