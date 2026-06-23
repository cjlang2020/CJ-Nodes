import { app } from "../../../../scripts/app.js";

const HANDLE = 8;
const COLORS = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e"];

// { label: 中文显示, value: 英文值 }
const PRESETS = {
    high_level_description: [
        { label: "电影感角色肖像，戏剧场景", value: "A cinematic portrait of a character in a dramatic scene" },
        { label: "宁静风景，柔和光线", value: "A serene landscape with vibrant colors and soft lighting" },
        { label: "抽象几何构图", value: "An abstract composition with geometric shapes and textures" },
        { label: "静物写实，自然元素", value: "A detailed still life arrangement with natural elements" },
        { label: "奇幻场景，魔幻氛围", value: "A fantasy scene with magical atmosphere and ethereal glow" },
        { label: "城市街景，黄金时刻", value: "A realistic urban street scene at golden hour" },
        { label: "极简设计，简洁线条", value: "A minimalist design with clean lines and subtle gradients" },
        { label: "动作场景，动态构图", value: "A dramatic action scene with dynamic composition" },
        { label: "水下梦幻场景", value: "A dreamy underwater scene with bioluminescent elements" },
        { label: "温馨室内，暖色灯光", value: "A cozy interior scene with warm ambient lighting" },
    ],
    background: [
        { label: "开阔田野，蓝天野花", value: "A vast open field with wildflowers under a blue sky" },
        { label: "茂密森林，阳光穿透", value: "A dense forest with sunlight filtering through the canopy" },
        { label: "未来都市，霓虹高楼", value: "A futuristic cityscape with neon lights and towering buildings" },
        { label: "安静房间，自然光线", value: "A quiet room with large windows and natural light" },
        { label: "晨雾山景", value: "A misty mountain landscape at dawn" },
        { label: "阳光海滩，温暖沙粒", value: "A sunlit beach with gentle waves and warm sand" },
        { label: "暗色小巷，戏剧阴影", value: "A dark moody alley with dramatic shadows" },
        { label: "花园繁花，蝴蝶飞舞", value: "A lush garden with blooming flowers and butterflies" },
        { label: "雪山星空", value: "A snowy mountain peak under a starlit sky" },
        { label: "专业影棚，柔光渐变", value: "A professional studio backdrop with soft gradients" },
        { label: "工业仓库，砖墙铁梁", value: "An industrial warehouse with exposed brick and metal beams" },
        { label: "天空浮岛，云层", value: "A floating island in a sky filled with clouds" },
    ],
    aesthetics: [
        { label: "电影感，胶片颗粒，浅景深", value: "cinematic, film grain, shallow depth of field" },
        { label: "鲜艳饱和，高对比", value: "vibrant, saturated colors, high contrast" },
        { label: "柔和色调，粉彩梦幻", value: "muted tones, pastel palette, soft and dreamy" },
        { label: "戏剧性，明暗对比，高动态", value: "dramatic, chiaroscuro, high dynamic range" },
        { label: "复古胶片感", value: "vintage, retro, analog film look" },
        { label: "现代简洁，精致光滑", value: "clean, modern, sleek and polished" },
        { label: "空灵脱俗，柔和光晕", value: "ethereal, otherworldly, soft glow" },
        { label: "大胆图形，强视觉冲击", value: "bold, graphic, strong visual impact" },
        { label: "自然有机，大地色系", value: "natural, organic, earthy tones" },
        { label: "奢华质感，丰富纹理", value: "luxurious, opulent, rich textures" },
        { label: "黑色电影，低饱和", value: "noir, moody, desaturated" },
        { label: "热带风情，暖色系", value: "tropical, vibrant, warm color palette" },
    ],
    lighting: [
        { label: "自然光，柔和均匀", value: "natural daylight, soft and even" },
        { label: "黄金时段，暖侧光", value: "golden hour, warm side lighting" },
        { label: "轮廓光，逆光", value: "dramatic rim lighting, backlight" },
        { label: "影棚三点布光", value: "studio lighting, three-point setup" },
        { label: "月光，冷蓝色调", value: "moonlight, cool blue tones" },
        { label: "霓虹灯光，彩色反射", value: "neon lighting, colorful reflections" },
        { label: "烛光，温暖亲密", value: "candlelight, warm intimate glow" },
        { label: "阴天，漫射柔光", value: "overcast, diffused soft light" },
        { label: "聚光灯，高对比", value: "spotlight, focused beam, high contrast" },
        { label: "体积光，光束穿透大气", value: "volumetric light, god rays through atmosphere" },
        { label: "生物发光，内在光晕", value: "bioluminescent, ethereal glow from within" },
        { label: "树叶间斑驳光影", value: "dappled light through leaves" },
    ],
    medium: [
        { label: "数字绘画，高细节", value: "digital painting, highly detailed" },
        { label: "油画，厚涂笔触", value: "oil painting, thick brushstrokes, impasto" },
        { label: "水彩，透明层叠", value: "watercolor, soft washes, transparent layers" },
        { label: "铅笔素描，交叉排线", value: "pencil sketch, fine linework, crosshatching" },
        { label: "3D渲染，光追写实", value: "3D render, photorealistic, ray tracing" },
        { label: "摄影，85mm镜头", value: "photograph, DSLR, 85mm lens" },
        { label: "概念艺术，数字哑光", value: "concept art, matte painting, cinematic" },
        { label: "动漫风格，赛璐珞着色", value: "anime style, cel shading, vibrant colors" },
        { label: "像素艺术，复古游戏", value: "pixel art, retro gaming aesthetic" },
        { label: "拼贴，混合媒介", value: "collage, mixed media, textured layers" },
        { label: "矢量插画，扁平设计", value: "vector illustration, flat design, clean lines" },
        { label: "炭笔素描，强对比", value: "charcoal drawing, dramatic contrast" },
    ],
    photo_style: [
        { label: "人像摄影，虚化背景", value: "portrait photography, bokeh background" },
        { label: "风光摄影，广角", value: "landscape photography, wide angle" },
        { label: "微距摄影，极致细节", value: "macro photography, extreme close-up detail" },
        { label: "街拍摄影，抓拍瞬间", value: "street photography, candid moments" },
        { label: "时尚摄影，影棚", value: "fashion photography, studio setup" },
        { label: "美食摄影，诱人呈现", value: "food photography, appetizing presentation" },
        { label: "建筑摄影，简洁线条", value: "architectural photography, clean lines" },
        { label: "野生动物，自然栖息", value: "wildlife photography, natural habitat" },
        { label: "天文摄影，长曝光星轨", value: "astrophotography, long exposure, star trails" },
        { label: "纪实风格，新闻摄影", value: "documentary style, photojournalistic" },
        { label: "艺术摄影，概念性", value: "fine art photography, conceptual" },
        { label: "产品摄影，干净背景", value: "product photography, clean background" },
    ],
    art_style: [
        { label: "印象派，可见笔触", value: "impressionist, visible brushstrokes, light and color" },
        { label: "超现实主义，梦幻", value: "surrealist, dreamlike, fantastical elements" },
        { label: "新艺术，流线有机", value: "art nouveau, flowing organic lines, decorative" },
        { label: "波普艺术，漫画风格", value: "pop art, bold colors, comic book style" },
        { label: "立体主义，几何碎片", value: "cubist, fragmented geometric forms" },
        { label: "巴洛克，戏剧光影", value: "baroque, dramatic lighting, rich details" },
        { label: "浮世绘，日式木版", value: "ukiyo-e, Japanese woodblock print style" },
        { label: "装饰艺术，几何华丽", value: "art deco, geometric patterns, glamorous" },
        { label: "表现主义，强烈情感", value: "expressionist, emotional intensity, bold colors" },
        { label: "极简主义，精简形式", value: "minimalist, reduced forms, essential elements" },
        { label: "迷幻艺术，万花筒", value: "psychedelic, vibrant patterns, kaleidoscopic" },
        { label: "哥特风，暗黑华丽", value: "gothic, dark atmosphere, ornate details" },
    ],
};

let currentNode = null;

function injectStyles() {
    if (document.getElementById("cj-pb-style")) return;
    const s = document.createElement("style");
    s.id = "cj-pb-style";
    s.textContent = `
        .cj-pb{display:flex;flex-direction:column;gap:4px;padding:4px;font:12px sans-serif;color:#ccc;overflow-y:auto}
        .cj-pb-r{display:flex;align-items:center;gap:6px}
        .cj-pb-l{width:80px;flex:0 0 auto;color:#aaa;font-size:11px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-pb-i{flex:1;min-width:0;background:#1a1a1a;border:1px solid #444;border-radius:4px;color:#ddd;font:12px monospace;padding:3px 6px;outline:none}
        .cj-pb-i:focus{border-color:#46b4e6}
        .cj-pb-i.cj-pb-ml{min-height:36px;resize:vertical;font-family:monospace;line-height:1.4}
        .cj-pb-dw{position:relative;flex:0 0 auto}
        .cj-pb-db{width:20px;height:20px;background:#333;border:1px solid #555;border-radius:4px;color:#bbb;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:9px}
        .cj-pb-db:hover{border-color:#46b4e6;color:#fff}
        .cj-pb-dd{position:absolute;top:100%;right:0;z-index:10000;min-width:240px;max-width:360px;max-height:240px;overflow-y:auto;background:#262626;border:1px solid #555;border-radius:6px;box-shadow:0 6px 20px rgba(0,0,0,.55);padding:4px;display:none}
        .cj-pb-dd.open{display:block}
        .cj-pb-di{padding:3px 6px;border-radius:4px;cursor:pointer;font:11px sans-serif;color:#bbb;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
        .cj-pb-di:hover{background:#333;color:#fff}
        .cj-pb-btn{background:#333;border:1px solid #555;border-radius:4px;color:#bbb;font:11px sans-serif;cursor:pointer;padding:2px 6px;line-height:16px;white-space:nowrap}
        .cj-pb-btn:hover{border-color:#46b4e6;color:#fff}
        .cj-pb-btn.act{border-color:#46b4e6;color:#46b4e6;background:#2a3a42}
        .cj-pb-num{width:60px;flex:0 0 auto;background:#1a1a1a;border:1px solid #444;border-radius:4px;color:#ddd;font:12px monospace;padding:2px 4px;outline:none;text-align:center}
        .cj-pb-num:focus{border-color:#46b4e6}
        .cj-pb-cv{flex:1 1 auto;min-height:80px;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative;background:#111}
        .cj-pb-canvas{cursor:crosshair;display:block;flex:0 0 auto;background:#1a1a1a;border-radius:4px;outline:none;touch-action:none;min-width:100px;min-height:80px}
        .cj-pb-sw{width:16px;height:16px;border:1px solid #666;border-radius:3px;cursor:pointer;flex:0 0 auto}
        .cj-pb-pv{background:#1d1d1d;border:1px solid #333;border-radius:4px;padding:4px 6px;font:10px monospace;color:#aaa;white-space:pre-wrap;max-height:80px;overflow-y:auto;line-height:1.3}
    `;
    document.head.appendChild(s);
}

function mkRow(label, tooltip) {
    const r = document.createElement("div"); r.className = "cj-pb-r";
    const l = document.createElement("span"); l.className = "cj-pb-l"; l.textContent = label;
    if (tooltip) l.title = tooltip;
    r.appendChild(l); return r;
}
function mkInp(value, ml, ph) {
    const e = document.createElement(ml ? "textarea" : "input");
    e.className = "cj-pb-i" + (ml ? " cj-pb-ml" : "");
    e.value = value || ""; if (ph) e.placeholder = ph; if (!ml) e.type = "text";
    return e;
}
function mkDropdown(presets, onSel) {
    const w = document.createElement("div"); w.className = "cj-pb-dw";
    const b = document.createElement("button"); b.className = "cj-pb-db"; b.textContent = "\u25BC"; b.title = "选择预置";
    const d = document.createElement("div"); d.className = "cj-pb-dd";
    function build() {
        d.innerHTML = "";
        for (const p of presets) {
            const item = document.createElement("div"); item.className = "cj-pb-di";
            const display = p.label || p;
            const val = p.value || p;
            item.textContent = display; item.title = val;
            item.addEventListener("click", (e) => { e.stopPropagation(); onSel(val); d.classList.remove("open"); });
            d.appendChild(item);
        }
    }
    build();
    b.addEventListener("click", (e) => { e.stopPropagation(); const was = d.classList.contains("open"); document.querySelectorAll(".cj-pb-dd.open").forEach(x => x.classList.remove("open")); if (!was) { build(); d.classList.add("open"); } });
    w.appendChild(b); w.appendChild(d); return w;
}
function mkParamField(label, tooltip, ml, presets, getter, setter) {
    const r = mkRow(label, tooltip);
    const i = mkInp(getter(), ml, "");
    i.addEventListener("input", () => { setter(i.value); sync(); });
    r.appendChild(i);
    if (presets?.length) r.appendChild(mkDropdown(presets, (v) => { i.value = v; setter(v); sync(); }));
    return { row: r, input: i };
}

function sync() {
    const node = currentNode; if (!node) return;
    syncPreview(node); saveState(node);
    if (app?.graph) app.graph.setDirtyCanvas(true, true);
}
function saveState(node) {
    const w = node.widgets?.find((w) => w.name === "prompt_data");
    if (w) w.value = JSON.stringify(node._pb);
}
function syncPreview(node) {
    if (!node._pbPV) return;
    const s = node._pb;
    const lines = [];
    if (s.high_level_description) lines.push(`描述: ${s.high_level_description}`);
    if (s.aesthetics) lines.push(`美学: ${s.aesthetics}`);
    if (s.lighting) lines.push(`光影: ${s.lighting}`);
    if (s.medium) lines.push(`媒介: ${s.medium}`);
    if (s.photo_style) lines.push(`摄影: ${s.photo_style}`);
    if (s.background) lines.push(`背景: ${s.background}`);
    if (s.regions.length) {
        lines.push(`区域: ${s.regions.length}`);
        for (let i = 0; i < s.regions.length; i++) {
            const rg = s.regions[i];
            let t = `  [${String(i+1).padStart(2,"0")}] ${rg.type}`;
            const bbox = rg.bbox;
            if (bbox) t += ` [${bbox[0]},${bbox[1]},${bbox[2]},${bbox[3]}]`;
            if (rg.desc) t += ` - ${rg.desc.slice(0,40)}`;
            lines.push(t);
        }
    }
    node._pbPV.textContent = lines.join("\n");
}

// ── Canvas Region Editor ──
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

function buildCanvasEditor(node) {
    const s = node._pb;
    const cvWrap = document.createElement("div"); cvWrap.className = "cj-pb-cv";
    const canvas = document.createElement("canvas"); canvas.className = "cj-pb-canvas"; canvas.tabIndex = 0;
    const ctx = canvas.getContext("2d");
    node._cvEl = canvas; node._cvCtx = ctx;

    let drawing = false, dragMode = null, dragStart = null, boxStart = null;

    function logW() { return canvas.offsetWidth || 1; }
    function logH() { return canvas.offsetHeight || 1; }
    function mouseN(e) { const r = canvas.getBoundingClientRect(); return { x: (e.clientX-r.left)/r.width, y: (e.clientY-r.top)/r.height }; }
    function toPx(b) { const W=logW(),H=logH(); return {x1:b.x*W,y1:b.y*H,x2:(b.x+b.w)*W,y2:(b.y+b.h)*H}; }

    function boxesAt(mN) {
        const baseRx=HANDLE/logW(),baseRy=HANDLE/logH();
        const res=[];
        for(let i=0;i<s.regions.length;i++){
            const b=s.regions[i];
            const rx=Math.min(baseRx,b.w/3),ry=Math.min(baseRy,b.h/3);
            const mode=rectHitN(mN.x,mN.y,b.x,b.y,b.x+b.w,b.y+b.h,rx,ry);
            if(mode)res.push({index:i,mode});
        }
        const ai=res.findIndex(c=>c.index===s.activeRegion);
        if(ai>0)res.unshift(res.splice(ai,1)[0]);
        return res;
    }

    function draw() {
        const W=logW()||100,H=logH()||80,d=window.devicePixelRatio||1;
        const bw=Math.round(W*d),bh=Math.round(H*d);
        if(canvas.width!==bw||canvas.height!==bh){canvas.width=bw;canvas.height=bh;}
        ctx.setTransform(d,0,0,d,0,0);
        ctx.clearRect(0,0,W,H);
        ctx.fillStyle="#1a1a1a"; ctx.fillRect(0,0,W,H);
        // grid
        ctx.strokeStyle="rgba(255,255,255,0.06)"; ctx.lineWidth=1;
        for(let i=1;i<4;i++){const fx=i/4;ctx.beginPath();ctx.moveTo(fx*W,0);ctx.lineTo(fx*W,H);ctx.stroke();ctx.beginPath();ctx.moveTo(0,fx*H);ctx.lineTo(W,fx*H);ctx.stroke();}
        // regions
        for(let i=0;i<s.regions.length;i++){
            const b=s.regions[i],active=i===s.activeRegion;
            const{x1,y1,x2,y2}=toPx(b);
            const w=x2-x1,h=y2-y1;
            const col=COLORS[i%COLORS.length];
            ctx.fillStyle=col+"22"; ctx.fillRect(x1,y1,w,h);
            ctx.strokeStyle=col; ctx.lineWidth=active?2:1;
            ctx.strokeRect(x1+0.5,y1+0.5,w-1,h-1);
            if(active){ctx.strokeStyle="#ff8c00";ctx.lineWidth=2;ctx.strokeRect(x1+1,y1+1,w-2,h-2);}
            // tag
            const tag=String(i+1).padStart(2,"0");
            ctx.font="bold 10px monospace"; const tw=ctx.measureText(tag).width+6;
            ctx.fillStyle=col; ctx.fillRect(x1,y1,tw,13);
            ctx.fillStyle=active?"#000":textOn(col); ctx.fillText(tag,x1+3,y1+10);
            // desc text clipped
            if(b.desc||b.text){
                ctx.save(); ctx.beginPath(); ctx.rect(x1,y1,w,h); ctx.clip();
                ctx.font="10px monospace"; ctx.fillStyle=readableText(col);
                let body=b.type==="text"&&b.text?`"${b.text}" ${b.desc||""}`:b.desc||"";
                const lines=wrapText(ctx,body,w-8);
                let ty=y1+14; for(const ln of lines){if(ty>y2-2)break;ctx.fillText(ln,x1+4,ty);ty+=12;}
                ctx.restore();
            }
            // handles when active
            if(active){
                const hs=5;
                for(const[px,py]of[[x1,y1],[x2,y1],[x1,y2],[x2,y2],[x1+w/2,y1],[x1+w/2,y2],[x1,y1+h/2],[x2,y1+h/2]]){
                    ctx.fillStyle="#ff8c00"; ctx.fillRect(px-hs,py-hs,hs*2,hs*2);
                }
            }
        }
    }
    function textOn(hex){const c=hexRgb(hex);return!c?"#000":luminance(c)>140?"#000":"#fff";}
    function readableText(hex){const c=hexRgb(hex);if(!c)return"#d4d4d4";let{r,g,b}=c;const l=luminance(c);if(l<130){const t=(130-l)/(255-l);r=Math.round(r+(255-r)*t);g=Math.round(g+(255-g)*t);b=Math.round(b+(255-b)*t);}return`rgb(${r},${g},${b})`;}
    function hexRgb(h){h=h.replace("#","");if(h.length<6)return null;return{r:parseInt(h.slice(0,2),16),g:parseInt(h.slice(2,4),16),b:parseInt(h.slice(4,6),16)};}
    function luminance({r,g,b}){return 0.299*r+0.587*g+0.114*b;}
    function wrapText(c,text,maxW){const lines=[];for(const para of text.split("\n")){let line="";for(const word of para.split(/\s+/)){if(!word)continue;const test=line?line+" "+word:word;if(line&&c.measureText(test).width>maxW){lines.push(line);line=word;}else line=test;}lines.push(line);}return lines;}

    function fitCanvas() {
        if(cvWrap.offsetParent===null)return;
        const availW=cvWrap.clientWidth,availH=cvWrap.clientHeight;
        if(availW<4||availH<4)return;
        const aspect=s.width/s.height;
        let cw=availW,ch=cw/aspect;
        if(ch>availH){ch=availH;cw=ch*aspect;}
        canvas.style.width=Math.round(cw)+"px";
        canvas.style.height=Math.round(ch)+"px";
        draw();
    }

    // Observer to re-fit when visible again
    try{
        node._pbVisObs=new IntersectionObserver((entries)=>{
            if(entries.some(en=>en.isIntersecting))fitCanvas();
        });
        node._pbVisObs.observe(cvWrap);
    }catch(e){}
    // Observer to re-fit on resize
    try{
        node._pbResizeObs=new ResizeObserver(()=>fitCanvas());
        node._pbResizeObs.observe(cvWrap);
    }catch(e){}

    canvas.addEventListener("pointerdown",(e)=>{
        if(e.button!==0)return;
        canvas.focus();
        const mN=mouseN(e);
        const hits=rectHitN(mN.x,mN.y,0,0,1,1,0,0)?boxesAt(mN):[];
        if(hits.length>0){
            const hit=hits[0];
            s.activeRegion=hit.index; dragMode=hit.mode;
            boxStart={...s.regions[hit.index]}; dragStart=mN;
        } else {
            const nb={x:mN.x,y:mN.y,w:0,h:0,type:"obj",text:"",desc:"",palette:[]};
            s.regions.push(nb); s.activeRegion=s.regions.length-1;
            dragMode="draw"; boxStart={...nb}; dragStart=mN;
        }
        drawing=true;
        canvas.addEventListener("pointermove",onMove);
        canvas.addEventListener("pointerup",onUp);
        e.preventDefault();
    });

    function onMove(e){
        if(!drawing)return;
        const mN=mouseN(e);
        const dx=mN.x-dragStart.x,dy=mN.y-dragStart.y;
        s.regions[s.activeRegion]=normBox(applyDrag(dragMode,boxStart,dx,dy));
        draw(); syncPreview(node); syncTokens(node);
    }
    function onUp(){
        drawing=false;
        canvas.removeEventListener("pointermove",onMove);
        canvas.removeEventListener("pointerup",onUp);
        const b=s.regions[s.activeRegion];
        if(b&&(b.w<0.005||b.h<0.005)&&dragMode==="draw"){s.regions.splice(s.activeRegion,1);s.activeRegion=Math.min(s.activeRegion,s.regions.length-1);}
        dragMode=null;boxStart=null;dragStart=null;
        draw(); sync();
    }

    canvas.addEventListener("keydown",(e)=>{
        if(e.key==="Delete"||e.key==="Backspace"){
            if(s.activeRegion>=0&&s.activeRegion<s.regions.length){
                e.preventDefault();e.stopPropagation();
                s.regions.splice(s.activeRegion,1);
                s.activeRegion=Math.min(s.activeRegion,s.regions.length-1);
                draw();sync();
            }
        }
    });

    node._cvFit=fitCanvas;
    node._cvDraw=draw;
    cvWrap.appendChild(canvas);
    return cvWrap;
}

function buildUI(node) {
    const s=node._pb;
    const wrap=document.createElement("div");wrap.className="cj-pb";

    // size
    const dimR=mkRow("尺寸:","画布尺寸");
    const wInp=document.createElement("input");wInp.className="cj-pb-num";wInp.type="number";wInp.min="64";wInp.max="16384";wInp.step="16";wInp.value=s.width;
    wInp.addEventListener("input",()=>{s.width=parseInt(wInp.value)||1024;node._cvFit?.();sync();});
    const xL=document.createElement("span");xL.textContent="\u00D7";xL.style.color="#666";
    const hInp=document.createElement("input");hInp.className="cj-pb-num";hInp.type="number";hInp.min="64";hInp.max="16384";hInp.step="16";hInp.value=s.height;
    hInp.addEventListener("input",()=>{s.height=parseInt(hInp.value)||1024;node._cvFit?.();sync();});
    dimR.append(wInp,xL,hInp);wrap.appendChild(dimR);

    // style
    const stR=mkRow("风格:","");
    const stGrp=document.createElement("div");stGrp.style.cssText="display:flex;gap:4px;flex:1;";
    const photoR=mkRow("摄影:","");const artR=mkRow("艺术风格:","");
    const photoI=mkInp(s.photo_style||"",false,"");photoI.addEventListener("input",()=>{s.photo_style=photoI.value;sync();});
    photoR.appendChild(photoI);photoR.appendChild(mkDropdown(PRESETS.photo_style,v=>{photoI.value=v;s.photo_style=v;sync();}));
    const artI=mkInp(s.art_style||"",false,"");artI.addEventListener("input",()=>{s.art_style=artI.value;sync();});
    artR.appendChild(artI);artR.appendChild(mkDropdown(PRESETS.art_style,v=>{artI.value=v;s.art_style=v;sync();}));
    function updStyle(t){s.style=t;photoR.style.display=t==="photo"?"flex":"none";artR.style.display=t==="art_style"?"flex":"none";}
    for(const t of["none","photo","art_style"]){const b=document.createElement("button");b.className="cj-pb-btn"+(s.style===t?" act":"");b.textContent=t;b.addEventListener("click",()=>{stGrp.querySelectorAll(".cj-pb-btn").forEach(x=>x.classList.remove("act"));b.classList.add("act");updStyle(t);sync();});stGrp.appendChild(b);}
    stR.appendChild(stGrp);wrap.appendChild(stR);wrap.appendChild(photoR);wrap.appendChild(artR);

    // param fields
    const fields=[
        {l:"描述:",t:"整体画面概述",ml:true,p:PRESETS.high_level_description,k:"high_level_description"},
        {l:"背景:",t:"场景背景描述",ml:true,p:PRESETS.background,k:"background"},
        {l:"美学:",t:"美学风格",ml:false,p:PRESETS.aesthetics,k:"aesthetics"},
        {l:"光影:",t:"光照",ml:false,p:PRESETS.lighting,k:"lighting"},
        {l:"媒介:",t:"媒介",ml:false,p:PRESETS.medium,k:"medium"},
    ];
    const fEls={};
    for(const f of fields){
        const r=mkParamField(f.l,f.t,f.ml,f.p,()=>s[f.k]||"",v=>{s[f.k]=v;});
        fEls[f.k]=r;wrap.appendChild(r.row);
    }

    // style color palette
    const scpR=mkRow("色板:","风格色板（最多5色）");
    const scpSwatches=document.createElement("div");scpSwatches.style.cssText="display:flex;gap:3px;flex:1;flex-wrap:wrap;";
    function buildScpSwatches(){
        scpSwatches.innerHTML="";
        (s.style_color_palette||[]).forEach((c,i)=>{
            const sw=document.createElement("div");sw.className="cj-pb-sw";sw.style.cssText=`background:${c};cursor:pointer;width:18px;height:18px;border-radius:3px;`;
            sw.title=`${c} — 点击移除`;
            sw.addEventListener("click",()=>{s.style_color_palette.splice(i,1);buildScpSwatches();sync();});
            scpSwatches.appendChild(sw);
        });
        if((s.style_color_palette||[]).length<5){
            const addB=document.createElement("div");addB.className="cj-pb-sw";addB.style.cssText="background:#333;cursor:pointer;width:18px;height:18px;border-radius:3px;display:flex;align-items:center;justify-content:center;color:#888;font-size:12px;";addB.textContent="+";addB.title="添加颜色";
            const ci=document.createElement("input");ci.type="color";ci.value="#ffffff";ci.style.cssText="position:absolute;opacity:0;width:0;height:0;pointer-events:none;";
            addB.appendChild(ci);
            addB.style.position="relative";
            addB.addEventListener("click",()=>ci.click());
            ci.addEventListener("input",()=>{if(!s.style_color_palette)s.style_color_palette=[];s.style_color_palette.push(ci.value);buildScpSwatches();sync();});
            scpSwatches.appendChild(addB);
        }
    }
    buildScpSwatches();
    scpR.appendChild(scpSwatches);wrap.appendChild(scpR);

    // canvas only (no splitter/bottom panel)
    const cvWrap=buildCanvasEditor(node);
    wrap.appendChild(cvWrap);

    node._fEls=fEls;
    node._pbPhotoI=photoI;node._pbArtI=artI;node._pbUpdStyle=updStyle;
    node._pbBuildScpSwatches=buildScpSwatches;

    node.addDOMWidget("pb_panel","Prompt Builder",wrap,{
        getValue:()=>JSON.stringify(node._pb),
        setValue:v=>{try{Object.assign(node._pb,JSON.parse(v));rebuildAll(node);}catch(e){}}
    });

    rebuildAll(node);
    requestAnimationFrame(()=>node._cvFit?.());
}

function rebuildAll(node) {
    const s=node._pb,f=node._fEls;if(!f)return;
    for(const k of Object.keys(f)){f[k].input.value=s[k]||"";}
    node._pbUpdStyle(s.style||"none");
    if(node._pbPhotoI)node._pbPhotoI.value=s.photo_style||"";
    if(node._pbArtI)node._pbArtI.value=s.art_style||"";
    node._pbBuildScpSwatches?.();
    node._cvDraw?.();
    syncPreview(node);
}

function chainCallback(obj,prop,cb){const old=obj[prop];obj[prop]=function(...args){const r=old?.apply(this,args);cb.apply(this,args);return r;};}

app.registerExtension({
    name:"CJNodes.PromptBuilder",
    async beforeRegisterNodeDef(nodeType,nodeData){
        if(nodeData.name!=="PromptBuilderNode")return;
        injectStyles();
        chainCallback(nodeType.prototype,"onNodeCreated",function(){
            const node=this;currentNode=node;
            node._pb={width:1024,height:1024,high_level_description:"",background:"",style:"none",aesthetics:"",lighting:"",medium:"",photo_style:"",art_style:"",style_color_palette:[],regions:[],activeRegion:-1};
            const pdW=node.widgets?.find(w=>w.name==="prompt_data");
            if(pdW){pdW.hidden=true;pdW.computeSize=()=>[0,-4];if(pdW.value){try{const d=JSON.parse(pdW.value);Object.assign(node._pb,d);if(!node._pb.regions)node._pb.regions=[];if(node._pb.activeRegion==null)node._pb.activeRegion=-1;}catch(e){}}}
            buildUI(node);
            node.setSize([Math.max(440,node.size[0]),Math.max(500,node.size[1])]);
            // Cleanup observers when node is removed
            chainCallback(node,"onRemoved",()=>{
                if(node._pbVisObs){node._pbVisObs.disconnect();node._pbVisObs=null;}
                if(node._pbResizeObs){node._pbResizeObs.disconnect();node._pbResizeObs=null;}
            });
        });
    }
});

console.log("CJ-Nodes PromptBuilder with canvas regions loaded");
