import { app } from "../../../../scripts/app.js";

const HANDLE = 8;
const COLORS = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e"];

// 中文（英文）格式的预置提示词
const PRESETS = {
    high_level_description: [
        "电影感角色肖像，戏剧场景（A cinematic portrait of a character in a dramatic scene）",
        "宁静风景，柔和光线（A serene landscape with vibrant colors and soft lighting）",
        "抽象几何构图（An abstract composition with geometric shapes and textures）",
        "静物写实，自然元素（A detailed still life arrangement with natural elements）",
        "奇幻场景，魔幻氛围（A fantasy scene with magical atmosphere and ethereal glow）",
        "城市街景，黄金时刻（A realistic urban street scene at golden hour）",
        "极简设计，简洁线条（A minimalist design with clean lines and subtle gradients）",
        "动作场景，动态构图（A dramatic action scene with dynamic composition）",
        "水下梦幻场景（A dreamy underwater scene with bioluminescent elements）",
        "温馨室内，暖色灯光（A cozy interior scene with warm ambient lighting）",
        "超现实梦境，扭曲现实（A surrealist dreamscape with melting clocks and impossible geometry）",
        "赛博朋克霓虹，雨夜街头（A cyberpunk scene with neon signs, rain-soaked streets and holograms）",
        "复古胶片生活，怀旧氛围（A vintage film-style lifestyle scene with warm nostalgic tones）",
        "恐怖暗黑氛围，迷雾笼罩（A dark horror atmosphere with eerie fog and shadowy figures）",
        "田园牧歌乡村，金色麦田（A pastoral countryside scene with golden wheat fields and rustic charm）",
        "太空科幻场景，星际探索（A sci-fi space scene with cosmic nebulae and futuristic spacecraft）",
        "俯瞰鸟瞰视角，壮阔全景（An aerial bird's eye view of a dramatic landscape）",
        "微观世界奇观，极致细节（A microscopic world wonder with extreme cellular and textural detail）",
        "后末日废墟，藤蔓覆盖（Post-apocalyptic ruins overgrown with vegetation and decay）",
        "蒸汽朋克机械，齿轮铜管（A steampunk mechanical contraption with brass gears and copper pipes）",
        "极光冰川奇景，梦幻光影（Aurora borealis dancing over glacial landscapes with ethereal light）",
        "东方古典意境，水墨留白（Classical Eastern ink painting atmosphere with elegant negative space）",
    ],
    background: [
        "开阔田野，蓝天野花（A vast open field with wildflowers under a blue sky）",
        "茂密森林，阳光穿透（A dense forest with sunlight filtering through the canopy）",
        "未来都市，霓虹高楼（A futuristic cityscape with neon lights and towering buildings）",
        "安静房间，自然光线（A quiet room with large windows and natural light）",
        "晨雾山景（A misty mountain landscape at dawn）",
        "阳光海滩，温暖沙粒（A sunlit beach with gentle waves and warm sand）",
        "暗色小巷，戏剧阴影（A dark moody alley with dramatic shadows）",
        "花园繁花，蝴蝶飞舞（A lush garden with blooming flowers and butterflies）",
        "雪山星空（A snowy mountain peak under a starlit sky）",
        "专业影棚，柔光渐变（A professional studio backdrop with soft gradients）",
        "工业仓库，砖墙铁梁（An industrial warehouse with exposed brick and metal beams）",
        "天空浮岛，云层（A floating island in a sky filled with clouds）",
        "沙漠沙丘，落日金辉（Desert sand dunes stretching to the horizon under a golden sunset）",
        "水下珊瑚礁，热带鱼群（An underwater coral reef teeming with colorful tropical fish）",
        "星云太空，璀璨星河（A deep space nebula with swirling cosmic dust and brilliant starlight）",
        "古代遗迹，藤蔓覆盖（Ancient stone ruins reclaimed by creeping vines and moss）",
        "雨夜街道，霓虹倒影（Rain-soaked city street with neon signs reflecting on wet pavement）",
        "夜市烟火，灯笼高挂（A bustling night market with paper lanterns and wisps of smoke）",
        "悬崖绝壁，海浪拍击（A dramatic cliff edge overlooking crashing ocean waves below）",
        "图书馆书墙，暖光氛围（A grand library with towering floor-to-ceiling bookshelves）",
        "废墟藤蔓，末日美学（Abandoned building interior with creeping vines and decay）",
        "地下水晶洞穴，虹彩光芒（An underground crystal cave with iridescent glowing formations）",
    ],
    aesthetics: [
        "电影感，胶片颗粒，浅景深（cinematic, film grain, shallow depth of field）",
        "鲜艳饱和，高对比（vibrant, saturated colors, high contrast）",
        "柔和色调，粉彩梦幻（muted tones, pastel palette, soft and dreamy）",
        "戏剧性，明暗对比，高动态（dramatic, chiaroscuro, high dynamic range）",
        "复古胶片感（vintage, retro, analog film look）",
        "现代简洁，精致光滑（clean, modern, sleek and polished）",
        "空灵脱俗，柔和光晕（ethereal, otherworldly, soft glow）",
        "大胆图形，强视觉冲击（bold, graphic, strong visual impact）",
        "自然有机，大地色系（natural, organic, earthy tones）",
        "奢华质感，丰富纹理（luxurious, opulent, rich textures）",
        "黑色电影，低饱和（noir, moody, desaturated）",
        "热带风情，暖色系（tropical, vibrant, warm color palette）",
        "蒸汽朋克，铜绿齿轮（steampunk, brass and copper tones, mechanical details）",
        "赛博朋克，霓虹雨夜（cyberpunk, neon glow, dark rainy streets, holographic elements）",
        "全息未来感，虹彩光泽（holographic, iridescent, futuristic sheen, prismatic colors）",
        "高调明亮，清新通透（high-key, bright, airy, overexposed feel, minimal shadows）",
        "低调暗黑，深邃阴影（low-key, deep shadows, moody darkness, dramatic contrast）",
        "双色调极简，双色配色（duotone, two-color palette, graphic simplicity）",
        "颗粒胶片质感，模拟温暖（grainy film texture, analog warmth, soft halation）",
        "哑光柔雾，雾面质感（matte finish, soft fog, desaturated, velvety surface）",
        "光泽玻璃质感，反射通透（glossy, reflective, glass-like surfaces, transparency）",
        "金属质感，铬面反光（metallic, chrome, reflective surfaces, industrial sheen）",
    ],
    lighting: [
        "自然光，柔和均匀（natural daylight, soft and even）",
        "黄金时段，暖侧光（golden hour, warm side lighting）",
        "轮廓光，逆光（dramatic rim lighting, backlight）",
        "影棚三点布光（studio lighting, three-point setup）",
        "月光，冷蓝色调（moonlight, cool blue tones）",
        "霓虹灯光，彩色反射（neon lighting, colorful reflections）",
        "烛光，温暖亲密（candlelight, warm intimate glow）",
        "阴天，漫射柔光（overcast, diffused soft light）",
        "聚光灯，高对比（spotlight, focused beam, high contrast）",
        "体积光，光束穿透大气（volumetric light, god rays through atmosphere）",
        "生物发光，内在光晕（bioluminescent, ethereal glow from within）",
        "树叶间斑驳光影（dappled light through leaves）",
        "伦勃朗光，面部三角光影（Rembrandt lighting, triangle of light on cheek, dramatic portrait）",
        "蝶形光，美容人像（butterfly lighting, glamour portrait, shadow under nose）",
        "分割光，半面明暗（split lighting, dramatic half-face illumination）",
        "实景光源， lamp窗光（practical lighting, visible lamps and windows in scene）",
        "火光映照，跳动暖橙（firelight, warm flickering orange glow, campfire ambiance）",
        "蓝色时刻，暮光深蓝（blue hour, twilight deep blue, city lights emerging）",
        "正午硬光，强烈阴影（harsh midday sun, strong defined shadows, high contrast）",
        "投影光影，图案投射（projected patterns, gobo lighting, decorative shadow play）",
        "底部打光，戏剧恐怖（uplighting, dramatic from below, horror movie feel）",
        "烟雾弥漫光，朦胧光束（hazy smoky light, diffused beams, atmospheric fog）",
    ],
    medium: [
        "数字绘画，高细节（digital painting, highly detailed）",
        "油画，厚涂笔触（oil painting, thick brushstrokes, impasto）",
        "水彩，透明层叠（watercolor, soft washes, transparent layers）",
        "铅笔素描，交叉排线（pencil sketch, fine linework, crosshatching）",
        "3D渲染，光追写实（3D render, photorealistic, ray tracing）",
        "摄影，85mm镜头（photograph, DSLR, 85mm lens）",
        "概念艺术，数字哑光（concept art, matte painting, cinematic）",
        "动漫风格，赛璐珞着色（anime style, cel shading, vibrant colors）",
        "像素艺术，复古游戏（pixel art, retro gaming aesthetic）",
        "拼贴，混合媒介（collage, mixed media, textured layers）",
        "矢量插画，扁平设计（vector illustration, flat design, clean lines）",
        "炭笔素描，强对比（charcoal drawing, dramatic contrast）",
        "丙烯画，大胆厚涂（acrylic painting, bold opaque layers, vivid colors）",
        "水墨画，东方笔韵（ink wash painting, sumi-e, Chinese brush strokes）",
        "色粉笔画，柔粉质感（pastel drawing, soft powdery texture, blended colors）",
        "黏土3D渲染，柔和次表面（clay render, soft subsurface scattering, miniature feel）",
        "马赛克拼贴，镶嵌碎片（mosaic, tile fragments, tessellated patterns）",
        "彩色玻璃，铅线透光（stained glass, lead lines, luminous translucent panels）",
        "木刻版画，粗犷刀痕（woodcut print, bold carved lines, high contrast）",
        "喷涂鸦，滴落飞溅（spray paint graffiti, drips and overspray, urban wall art）",
        "丝网印刷，扁平分层（screen print, flat color layers, risograph texture）",
        "刺绣织物，线迹纹理（embroidery, thread texture on fabric, stitched details）",
    ],
    photo_style: [
        "人像摄影，虚化背景（portrait photography, bokeh background）",
        "风光摄影，广角（landscape photography, wide angle）",
        "微距摄影，极致细节（macro photography, extreme close-up detail）",
        "街拍摄影，抓拍瞬间（street photography, candid moments）",
        "时尚摄影，影棚（fashion photography, studio setup）",
        "美食摄影，诱人呈现（food photography, appetizing presentation）",
        "建筑摄影，简洁线条（architectural photography, clean lines）",
        "野生动物，自然栖息（wildlife photography, natural habitat）",
        "天文摄影，长曝光星轨（astrophotography, long exposure, star trails）",
        "纪实风格，新闻摄影（documentary style, photojournalistic）",
        "艺术摄影，概念性（fine art photography, conceptual）",
        "产品摄影，干净背景（product photography, clean background）",
        "航拍鸟瞰，俯冲视角（aerial drone photography, top-down perspective）",
        "水下摄影，蓝绿色调（underwater photography, blue-green tones, caustics）",
        "红外摄影，超现实色彩（infrared photography, false color surreal, red foliage）",
        "长曝光，光轨丝滑（long exposure, light trails, silky water, motion blur）",
        "双重曝光，重叠剪影（double exposure, overlapping silhouettes, merged imagery）",
        "移轴摄影，微缩模型（tilt-shift photography, miniature effect, selective focus）",
        "黑白胶片，颗粒质感（black and white film, strong grain, timeless contrast）",
        "编辑杂志，叙事风格（editorial magazine photography, styled narrative）",
        "运动抓拍，冻结瞬间（sports action photography, frozen motion, dynamic）",
        "夜景城市，长曝光灯光（night cityscape, long exposure, vibrant city lights）",
    ],
    art_style: [
        "印象派，可见笔触（impressionist, visible brushstrokes, light and color）",
        "超现实主义，梦幻（surrealist, dreamlike, fantastical elements）",
        "新艺术，流线有机（art nouveau, flowing organic lines, decorative）",
        "波普艺术，漫画风格（pop art, bold colors, comic book style）",
        "立体主义，几何碎片（cubist, fragmented geometric forms）",
        "巴洛克，戏剧光影（baroque, dramatic lighting, rich details）",
        "浮世绘，日式木版（ukiyo-e, Japanese woodblock print style）",
        "装饰艺术，几何华丽（art deco, geometric patterns, glamorous）",
        "表现主义，强烈情感（expressionist, emotional intensity, bold colors）",
        "极简主义，精简形式（minimalist, reduced forms, essential elements）",
        "迷幻艺术，万花筒（psychedelic, vibrant patterns, kaleidoscopic）",
        "哥特风，暗黑华丽（gothic, dark atmosphere, ornate details）",
        "浪漫主义，壮丽风景（romanticism, emotional landscape, sublime nature）",
        "现实主义，细腻写实（realism, detailed everyday life, faithful representation）",
        "新古典主义，秩序庄严（neoclassicism, orderly composition, Greco-Roman ideals）",
        "洛可可，华丽柔美（rococo, ornate decoration, pastel colors, playful elegance）",
        "文艺复兴，透视光影（renaissance, chiaroscuro, linear perspective, classical balance）",
        "野兽派，狂野色彩（fauvism, wild expressive colors, non-naturalistic palette）",
        "构成主义，几何宣传（constructivism, geometric forms, bold propaganda style）",
        "风格派，三原色网格（De Stijl, primary colors, grid composition, Mondrian influence）",
        "超写实主义，照片级细节（hyperrealism, photo-like detail, extreme precision）",
        "蒸汽波，复古数字（vaporwave, retro digital aesthetic, pink and teal, glitch art）",
    ],
};

const SCENES = [
    { label:"电影感肖像", w:1024, h:1536, style:"photo",
      high_level_description:"电影感角色肖像，面部特写，眼神深邃，戏剧性表情（A cinematic close-up portrait with dramatic lighting and intense gaze）",
      background:"暗色模糊背景，光斑散景（Dark blurred background with bokeh light spots）",
      aesthetics:"电影感，胶片颗粒，浅景深，冷暖对比（cinematic, film grain, shallow depth of field, teal and orange）",
      lighting:"伦勃朗光，面部三角光影，暖侧光（Rembrandt lighting, triangle of light on cheek, warm side light）",
      medium:"摄影，85mm镜头，f1.4大光圈（photograph, 85mm lens, f1.4 aperture, full frame）",
      photo_style:"人像摄影，虚化背景，85mm定焦（portrait photography, bokeh background, 85mm prime lens）",
      art_style:"", style_color_palette:["#c87533","#1a3a4a","#e8d5b7","#2d2d2d","#f0e6d3"],
      regions:[{x:0.2,y:0.05,w:0.6,h:0.7,type:"obj",desc:"角色面部特写，眼神深邃，戏剧性表情",palette:[]},{x:0,y:0.75,w:1,h:0.25,type:"obj",desc:"暗色模糊背景，光斑散景",palette:[]}] },
    { label:"赛博朋克都市", w:1360, h:768, style:"photo",
      high_level_description:"赛博朋克都市夜景，霓虹灯闪烁，雨中街道，全息广告牌（A cyberpunk cityscape at night with neon lights, rain, and holographic billboards）",
      background:"未来都市街道，霓虹招牌密集，雨水反射光线（Futuristic urban street packed with neon signs, rain reflections）",
      aesthetics:"赛博朋克，霓虹紫蓝，高对比，潮湿反光（cyberpunk, neon purple and blue, high contrast, wet reflections）",
      lighting:"霓虹灯光，彩色反射，潮湿路面反光（neon lighting, colorful reflections, wet pavement glow）",
      medium:"3D渲染，光追写实，超高清细节（3D render, photorealistic, ray tracing, ultra detailed）",
      photo_style:"夜景城市，长曝光，霓虹灯光（night cityscape, long exposure, neon lights）",
      art_style:"", style_color_palette:["#ff00ff","#00ffff","#1a0a2e","#ff6b35","#0d1b2a"],
      regions:[{x:0,y:0,w:1,h:0.35,type:"obj",desc:"霓虹天空，全息广告牌闪烁",palette:[]},{x:0,y:0.3,w:1,h:0.4,type:"obj",desc:"密集高楼，霓虹招牌，雨水反射",palette:[]},{x:0,y:0.7,w:1,h:0.3,type:"obj",desc:"潮湿街道，霓虹灯光倒影，行人剪影",palette:[]}] },
    { label:"奇幻魔法森林", w:1024, h:1024, style:"art_style",
      high_level_description:"奇幻魔法森林，发光植物，精灵飞舞，神秘薄雾（A mystical enchanted forest with glowing flora, fairy lights, and magical mist）",
      background:"茂密古老森林，参天巨树，苔藓覆盖，薄雾弥漫（Ancient dense forest with towering trees, moss, and rolling mist）",
      aesthetics:"空灵脱俗，柔和光晕，梦幻色彩，丁达尔光线（ethereal, soft glow, dreamy colors, god rays through canopy）",
      lighting:"体积光，光束穿透树冠，生物发光点缀（volumetric light, god rays through canopy, bioluminescent accents）",
      medium:"数字绘画，高细节，哑光绘制（digital painting, highly detailed, matte painting style）",
      photo_style:"", art_style:"印象派，可见笔触，光影色彩（impressionist, visible brushstrokes, light and color）",
      style_color_palette:["#2ecc71","#9b59b6","#1abc9c","#f1c40f","#27ae60"],
      regions:[{x:0,y:0,w:0.35,h:1,type:"obj",desc:"左侧参天巨树，苔藓覆盖",palette:[]},{x:0.35,y:0,w:0.3,h:0.5,type:"obj",desc:"树冠间隙，丁达尔光束穿透",palette:[]},{x:0.65,y:0,w:0.35,h:1,type:"obj",desc:"右侧古老树木，藤蔓缠绕",palette:[]},{x:0.2,y:0.5,w:0.6,h:0.5,type:"obj",desc:"林间小径，发光植物，精灵飞舞",palette:[]}] },
    { label:"宁静湖畔风光", w:1360, h:768, style:"photo",
      high_level_description:"宁静湖畔清晨，湖面如镜，远山倒影，晨雾轻绕（A serene lakeside at dawn with mirror-like reflections, distant mountains, and gentle mist）",
      background:"开阔湖面，远处雪山，晨雾笼罩，宁静祥和（Expansive lake surface with distant snow-capped mountains and morning mist）",
      aesthetics:"柔和色调，清新通透，自然真实，空气感（soft tones, fresh and clear, natural realism, airy atmosphere）",
      lighting:"黄金时段，柔和晨光，湖面反射（golden hour, soft morning light, lake surface reflection）",
      medium:"风光摄影，广角镜头，偏振镜（landscape photography, wide angle lens, polarizer filter）",
      photo_style:"风光摄影，广角，长曝光（landscape photography, wide angle, long exposure）",
      art_style:"", style_color_palette:["#87ceeb","#2c3e50","#ecf0f1","#3498db","#1a5276"],
      regions:[{x:0,y:0,w:1,h:0.3,type:"obj",desc:"清晨天空，柔和渐变色彩",palette:[]},{x:0,y:0.25,w:1,h:0.2,type:"obj",desc:"远处雪山轮廓，晨雾缭绕",palette:[]},{x:0,y:0.45,w:1,h:0.35,type:"obj",desc:"平静湖面，山体倒影如镜",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"湖畔前景，野花岩石点缀",palette:[]}] },
    { label:"恐怖古堡", w:1024, h:1536, style:"art_style",
      high_level_description:"恐怖古堡内部，阴森走廊，摇曳烛光，蛛网密布（A haunted castle interior with eerie corridors, flickering candles, and cobwebs）",
      background:"古老城堡走廊，石墙斑驳，烛台排列，阴影深邃（Ancient castle corridor with weathered stone walls, candlestick rows, deep shadows）",
      aesthetics:"黑色电影，低饱和，强烈明暗对比，颗粒感（noir, desaturated, strong chiaroscuro, film grain）",
      lighting:"烛光，温暖但诡异，长投影，局部照明（candlelight, warm but eerie, long shadows, pools of light）",
      medium:"概念艺术，数字哑光，电影级构图（concept art, matte painting, cinematic composition）",
      photo_style:"", art_style:"哥特风，暗黑华丽，精致细节（gothic, dark atmosphere, ornate details）",
      style_color_palette:["#8b0000","#2c2c2c","#d4a574","#1a1a1a","#c0392b"],
      regions:[{x:0.1,y:0,w:0.8,h:0.15,type:"obj",desc:"穹顶石拱，蛛网密布",palette:[]},{x:0,y:0.15,w:0.3,h:0.7,type:"obj",desc:"左侧石墙，烛台排列，摇曳烛光",palette:[]},{x:0.7,y:0.15,w:0.3,h:0.7,type:"obj",desc:"右侧石墙，阴影深邃，诡异氛围",palette:[]},{x:0.15,y:0.3,w:0.7,h:0.5,type:"obj",desc:"走廊深处，黑暗延伸，神秘入口",palette:[]},{x:0,y:0.85,w:1,h:0.15,type:"obj",desc:"石板地面，积水反光",palette:[]}] },
    { label:"产品广告", w:1024, h:1024, style:"photo",
      high_level_description:"高端产品广告，精致布光，干净背景，质感突出（Premium product advertisement with refined lighting and clean background）",
      background:"渐变纯色背景，柔和过渡，专业影棚（Gradient solid background with smooth transition, professional studio）",
      aesthetics:"现代简洁，精致光滑，高光泽，干净利落（clean, modern, sleek and polished, high gloss）",
      lighting:"影棚三点布光，柔光箱，反光板补光（studio lighting, three-point setup, softbox, reflector fill）",
      medium:"产品摄影，微距镜头，焦点堆叠（product photography, macro lens, focus stacking）",
      photo_style:"产品摄影，干净背景，精致布光（product photography, clean background, refined lighting）",
      art_style:"", style_color_palette:["#ffffff","#f5f5f5","#e0e0e0","#333333","#c0c0c0"],
      regions:[{x:0.2,y:0.15,w:0.6,h:0.6,type:"obj",desc:"产品主体，精致细节，高光泽质感",palette:[]},{x:0,y:0,w:1,h:0.15,type:"obj",desc:"渐变背景上部，柔和过渡",palette:[]},{x:0,y:0.75,w:1,h:0.25,type:"obj",desc:"渐变背景下部，倒影投影",palette:[]}] },
    { label:"时尚大片", w:1024, h:1536, style:"photo",
      high_level_description:"时尚杂志大片，模特造型，前卫服装，艺术妆容（Fashion magazine editorial with model posing, avant-garde clothing, artistic makeup）",
      background:"纯色影棚背景，极简构图，色彩纯净（Solid color studio backdrop, minimalist composition, pure colors）",
      aesthetics:"高调明亮，时尚感，杂志级质感，锐利细节（high-key, fashion-forward, magazine quality, sharp details）",
      lighting:"柔光箱主光，轮廓光分离，蝴蝶光（softbox key light, rim light separation, butterfly lighting）",
      medium:"时尚摄影，中画幅，影棚拍摄（fashion photography, medium format, studio shot）",
      photo_style:"时尚摄影，影棚，高级感（fashion photography, studio setup, high-end feel）",
      art_style:"", style_color_palette:["#ff1493","#000000","#ffffff","#dc143c","#f0f0f0"],
      regions:[{x:0.15,y:0.05,w:0.7,h:0.85,type:"obj",desc:"模特全身，前卫服装造型，艺术妆容",palette:[]},{x:0,y:0,w:1,h:0.05,type:"obj",desc:"纯净背景上部",palette:[]},{x:0,y:0.9,w:1,h:0.1,type:"obj",desc:"纯净背景下部，地面投影",palette:[]}] },
    { label:"美食特写", w:1024, h:1024, style:"photo",
      high_level_description:"精致美食特写，摆盘讲究，食材新鲜，诱人食欲（Gourmet food closeup with elegant plating, fresh ingredients, appetizing presentation）",
      background:"木质桌面，亚麻餐布，餐具点缀（Wooden table surface, linen napkin, utensil accents）",
      aesthetics:"温暖色调，浅景深，食欲感，自然光质感（warm tones, shallow depth of field, appetizing, natural light feel）",
      lighting:"侧逆光，窗光漫射，高光食物表面（side backlight, window light diffusion, food surface highlights）",
      medium:"美食摄影，微距镜头，焦点堆叠（food photography, macro lens, focus stacking）",
      photo_style:"美食摄影，诱人呈现，浅景深（food photography, appetizing presentation, shallow DOF）",
      art_style:"", style_color_palette:["#d4a574","#8b4513","#f5deb3","#2e8b57","#cd853f"],
      regions:[{x:0.15,y:0.1,w:0.7,h:0.55,type:"obj",desc:"美食主体，精致摆盘，诱人色泽",palette:[]},{x:0,y:0.65,w:1,h:0.35,type:"obj",desc:"木质桌面，亚麻餐布，餐具",palette:[]},{x:0.7,y:0.05,w:0.3,h:0.3,type:"obj",desc:"窗光来源，柔和侧逆光",palette:[]}] },
    { label:"建筑空间", w:1360, h:768, style:"photo",
      high_level_description:"现代建筑空间，几何线条，光影交错，极简美学（Modern architectural space with geometric lines, light and shadow interplay, minimalist aesthetics）",
      background:"混凝土与玻璃结构，开放式空间，天窗采光（Concrete and glass structure, open space, skylight illumination）",
      aesthetics:"现代简洁，几何构成，光影对比，空间感（clean, geometric composition, light-shadow contrast, spatial depth）",
      lighting:"自然光，天窗漫射，几何投影（natural daylight, skylight diffusion, geometric shadow patterns）",
      medium:"建筑摄影，移轴镜头，透视校正（architectural photography, tilt-shift lens, perspective correction）",
      photo_style:"建筑摄影，简洁线条，对称构图（architectural photography, clean lines, symmetrical composition）",
      art_style:"", style_color_palette:["#808080","#f5f5f5","#2c3e50","#bdc3c7","#ecf0f1"],
      regions:[{x:0,y:0,w:1,h:0.2,type:"obj",desc:"天窗结构，自然光漫射进入",palette:[]},{x:0,y:0.2,w:0.35,h:0.6,type:"obj",desc:"左侧混凝土墙面，几何线条",palette:[]},{x:0.65,y:0.2,w:0.35,h:0.6,type:"obj",desc:"右侧玻璃幕墙，光影投射",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"地面光影图案，几何投影",palette:[]}] },
    { label:"动漫角色", w:768, h:1024, style:"art_style",
      high_level_description:"日系动漫角色，大眼睛，动态姿势，鲜艳色彩（Japanese anime character with large eyes, dynamic pose, vibrant colors）",
      background:"渐变色背景，光效粒子，氛围渲染（Gradient background with light particles, atmospheric rendering）",
      aesthetics:"鲜艳饱和，赛璐珞着色，清晰线条，日式美学（vibrant, cel shading, clean linework, Japanese aesthetics）",
      lighting:"均匀柔光，面部补光，发丝高光（even soft light, face fill light, hair highlights）",
      medium:"动漫风格，赛璐珞着色，数字绘画（anime style, cel shading, digital painting）",
      photo_style:"", art_style:"动漫风格，赛璐珞着色，日式美学（anime style, cel shading, Japanese aesthetic）",
      style_color_palette:["#ff6b9d","#c44dff","#4dc9f6","#ffe066","#ff4757"],
      regions:[{x:0.1,y:0.05,w:0.8,h:0.7,type:"obj",desc:"动漫角色主体，大眼睛，动态姿势",palette:[]},{x:0,y:0,w:1,h:0.05,type:"obj",desc:"渐变背景上部",palette:[]},{x:0,y:0.75,w:1,h:0.25,type:"obj",desc:"光效粒子，氛围渲染，渐变背景",palette:[]}] },
    { label:"蒸汽朋克世界", w:1360, h:768, style:"art_style",
      high_level_description:"蒸汽朋克世界，齿轮机械，飞艇天空，维多利亚建筑（A steampunk world with brass gears, airships in sky, Victorian architecture）",
      background:"蒸汽工厂内部，铜管管道，齿轮咬合，蒸汽弥漫（Steam factory interior with copper pipes, interlocking gears, steam clouds）",
      aesthetics:"蒸汽朋克，铜绿齿轮，暖棕色调，复古机械（steampunk, brass and copper tones, warm brown palette, retro mechanical）",
      lighting:"火光映照，蒸汽漫射，金属高光（firelight glow, steam diffusion, metallic highlights）",
      medium:"概念艺术，数字哑光，丰富细节（concept art, matte painting, rich details）",
      photo_style:"", art_style:"新艺术，流线有机，装饰细节（art nouveau, flowing organic lines, decorative details）",
      style_color_palette:["#b87333","#cd853f","#8b4513","#daa520","#704214"],
      regions:[{x:0,y:0,w:1,h:0.3,type:"obj",desc:"蒸汽天空，飞艇漂浮，烟囱冒烟",palette:[]},{x:0,y:0.25,w:0.4,h:0.5,type:"obj",desc:"左侧齿轮机械装置，铜管管道",palette:[]},{x:0.6,y:0.25,w:0.4,h:0.5,type:"obj",desc:"右侧维多利亚建筑，蒸汽管道",palette:[]},{x:0,y:0.75,w:1,h:0.25,type:"obj",desc:"地面蒸汽弥漫，金属反射",palette:[]}] },
    { label:"末日废墟", w:1360, h:768, style:"photo",
      high_level_description:"后末日城市废墟，建筑坍塌，藤蔓覆盖，荒芜寂静（Post-apocalyptic city ruins with collapsed buildings, overgrown vines, desolate silence）",
      background:"废弃城市街道，残破建筑，植被入侵，灰尘弥漫（Abandoned city street, crumbling structures, vegetation reclaiming, dust in air）",
      aesthetics:"低饱和，灰绿色调，衰败美感，末日氛围（desaturated, grey-green tones, decay beauty, apocalyptic atmosphere）",
      lighting:"阴天漫射光，均匀灰调，无强烈阴影（overcast diffused light, uniform grey tone, no harsh shadows）",
      medium:"摄影，35mm镜头，纪实风格（photograph, 35mm lens, documentary style）",
      photo_style:"纪实风格，新闻摄影，raw真实感（documentary style, photojournalistic, raw realism）",
      art_style:"", style_color_palette:["#556b2f","#696969","#8fbc8f","#2f4f4f","#a9a9a9"],
      regions:[{x:0,y:0,w:0.4,h:0.6,type:"obj",desc:"左侧坍塌建筑残骸，钢筋外露",palette:[]},{x:0.6,y:0,w:0.4,h:0.5,type:"obj",desc:"右侧倾斜建筑，藤蔓覆盖",palette:[]},{x:0.3,y:0.1,w:0.4,h:0.3,type:"obj",desc:"灰暗天空，灰尘弥漫",palette:[]},{x:0,y:0.6,w:1,h:0.4,type:"obj",desc:"废弃街道，植被入侵，碎石瓦砾",palette:[]}] },
    { label:"深海奇遇", w:1024, h:1536, style:"art_style",
      high_level_description:"深海奇幻世界，发光水母，珊瑚礁群，神秘光束（A fantastical deep sea world with glowing jellyfish, coral reefs, mysterious light beams）",
      background:"深海环境，珊瑚礁群，海藻摇曳，气泡上升（Deep sea environment with coral reefs, swaying kelp, rising bubbles）",
      aesthetics:"空灵脱俗，生物发光，蓝绿色调，梦幻水下（ethereal, bioluminescent, blue-green tones, dreamy underwater）",
      lighting:"体积光，水面光束穿透，生物发光点缀（volumetric light, surface light beams, bioluminescent accents）",
      medium:"数字绘画，高细节，光效渲染（digital painting, highly detailed, light effects rendering）",
      photo_style:"水下摄影，蓝绿色调，焦散光（underwater photography, blue-green tones, caustics）",
      art_style:"", style_color_palette:["#006994","#40e0d0","#00ced1","#20b2aa","#008b8b"],
      regions:[{x:0,y:0,w:1,h:0.2,type:"obj",desc:"水面光线穿透，体积光束",palette:[]},{x:0.2,y:0.2,w:0.6,h:0.35,type:"obj",desc:"发光水母群，生物发光",palette:[]},{x:0,y:0.55,w:1,h:0.25,type:"obj",desc:"珊瑚礁群，海藻摇曳",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"深海底部，气泡上升，神秘光点",palette:[]}] },
    { label:"太空科幻", w:1360, h:768, style:"photo",
      high_level_description:"太空科幻场景，星际飞船，星云背景，宇宙深邃（A space sci-fi scene with interstellar spacecraft, nebula backdrop, cosmic depth）",
      background:"深空星云，璀璨星河，远处星系，宇宙尘埃（Deep space nebula, brilliant starfield, distant galaxies, cosmic dust）",
      aesthetics:"高对比，冷色调，光晕效果，未来科技感（high contrast, cool tones, lens flare, futuristic tech feel）",
      lighting:"恒星直射，星云漫射，飞船灯光（direct starlight, nebula ambient glow, spacecraft lights）",
      medium:"3D渲染，光追写实，超高清（3D render, photorealistic, ray tracing, ultra HD）",
      photo_style:"天文摄影，长曝光，深空天体（astrophotography, long exposure, deep sky objects）",
      art_style:"", style_color_palette:["#0a0a2e","#4a0080","#00bfff","#191970","#e0ffff"],
      regions:[{x:0,y:0,w:1,h:0.5,type:"obj",desc:"深空星云，璀璨星河，宇宙尘埃",palette:[]},{x:0.25,y:0.3,w:0.5,h:0.3,type:"obj",desc:"星际飞船主体，科技细节",palette:[]},{x:0,y:0.5,w:1,h:0.5,type:"obj",desc:"远处星系，行星轮廓，光晕效果",palette:[]}] },
    { label:"复古怀旧", w:1024, h:1024, style:"photo",
      high_level_description:"复古怀旧场景，老式汽车，暖黄街灯，年代感街道（Vintage nostalgic scene with classic car, warm street lamps, period street）",
      background:"老城区街道，欧式建筑，暖黄灯光，黄昏时分（Old town street, European buildings, warm yellow lights, dusk）",
      aesthetics:"复古胶片感，暖色调，颗粒质感，柔焦效果（vintage film look, warm tones, grain texture, soft focus）",
      lighting:"黄金时段，暖侧光，长投影，路灯点缀（golden hour, warm side light, long shadows, street lamp accents）",
      medium:"摄影，50mm胶片机，Kodak Portra 400（photograph, 50mm film camera, Kodak Portra 400）",
      photo_style:"黑白胶片，颗粒质感，经典构图（black and white film, grain texture, classic composition）",
      art_style:"", style_color_palette:["#d4a574","#c19a6b","#8b7355","#daa520","#f5deb3"],
      regions:[{x:0,y:0,w:0.4,h:0.6,type:"obj",desc:"左侧欧式建筑，暖黄灯光",palette:[]},{x:0.6,y:0,w:0.4,h:0.6,type:"obj",desc:"右侧建筑立面，窗台花盆",palette:[]},{x:0.3,y:0.2,w:0.4,h:0.4,type:"obj",desc:"老式汽车，复古造型",palette:[]},{x:0,y:0.6,w:1,h:0.4,type:"obj",desc:"石板街道，暖黄街灯投影",palette:[]}] },
    { label:"极简抽象", w:1024, h:1024, style:"art_style",
      high_level_description:"极简抽象设计，几何形状，留白空间，纯净色彩（Minimalist abstract design with geometric shapes, negative space, pure colors）",
      background:"纯白背景，大面积留白，呼吸感（Pure white background, large negative space, breathing room）",
      aesthetics:"极简主义，精简形式，少即是多，纯净利落（minimalist, reduced forms, less is more, pure and clean）",
      lighting:"均匀漫射光，无阴影，平面感（even diffused light, no shadows, flat feel）",
      medium:"矢量插画，扁平设计，精确几何（vector illustration, flat design, precise geometry）",
      photo_style:"", art_style:"极简主义，精简形式，留白美学（minimalist, reduced forms, negative space aesthetics）",
      style_color_palette:["#ffffff","#000000","#e74c3c","#f5f5f5","#333333"],
      regions:[{x:0.15,y:0.15,w:0.35,h:0.35,type:"obj",desc:"圆形几何形状，纯净色块",palette:[]},{x:0.55,y:0.45,w:0.3,h:0.4,type:"obj",desc:"矩形几何形状，对比色彩",palette:[]}] },
    { label:"微距自然", w:1024, h:1024, style:"photo",
      high_level_description:"微距自然世界，露珠晶莹，花瓣纹理，昆虫细节（Macro nature world with crystal dewdrops, petal textures, insect details）",
      background:"模糊绿色植被，柔和散景，自然虚化（Blurred green foliage, soft bokeh, natural defocus）",
      aesthetics:"鲜艳自然，极致细节，浅景深，露珠折射（vibrant natural, extreme detail, shallow DOF, dewdrop refraction）",
      lighting:"逆光，轮廓光，露珠高光，柔和散射（backlight, rim light, dewdrop highlights, soft diffusion）",
      medium:"微距摄影，100mm微距镜头，焦点堆叠（macro photography, 100mm macro lens, focus stacking）",
      photo_style:"微距摄影，极致细节，浅景深（macro photography, extreme close-up detail, shallow DOF）",
      art_style:"", style_color_palette:["#2ecc71","#27ae60","#f1c40f","#e74c3c","#1abc9c"],
      regions:[{x:0.1,y:0.1,w:0.8,h:0.6,type:"obj",desc:"花瓣主体，露珠晶莹，极致纹理细节",palette:[]},{x:0,y:0,w:1,h:0.1,type:"obj",desc:"逆光来源，轮廓光高光",palette:[]},{x:0,y:0.7,w:1,h:0.3,type:"obj",desc:"模糊绿色散景，柔和虚化",palette:[]}] },
    { label:"街头纪实", w:1360, h:768, style:"photo",
      high_level_description:"街头纪实摄影，行人匆匆，城市节奏，真实瞬间（Street documentary photography, bustling pedestrians, city rhythm, authentic moments）",
      background:"繁忙城市街道，建筑林立，车辆穿梭，生活气息（Busy urban street with buildings, vehicles, life energy）",
      aesthetics:"纪实风格，自然色彩，抓拍感，raw真实（documentary style, natural colors, candid feel, raw realism）",
      lighting:"自然光，阴天漫射，真实环境光（natural light, overcast diffusion, authentic ambient light）",
      medium:"摄影，35mm镜头，徕卡M系列（photograph, 35mm lens, Leica M series）",
      photo_style:"街拍摄影，抓拍瞬间，35mm广角（street photography, candid moments, 35mm wide angle）",
      art_style:"", style_color_palette:["#2c3e50","#7f8c8d","#95a5a6","#bdc3c7","#34495e"],
      regions:[{x:0,y:0,w:1,h:0.3,type:"obj",desc:"城市建筑天际线，招牌广告",palette:[]},{x:0.2,y:0.25,w:0.6,h:0.4,type:"obj",desc:"行人匆匆，抓拍瞬间，城市节奏",palette:[]},{x:0,y:0.65,w:1,h:0.35,type:"obj",desc:"街道地面，车辆穿梭，生活气息",palette:[]}] },
    { label:"油画古典肖像", w:1024, h:1536, style:"art_style",
      high_level_description:"古典油画肖像，华丽服饰，深色背景，大师笔触（Classical oil painting portrait with elaborate clothing, dark background, masterful brushwork）",
      background:"深色渐变背景，帷幔质感，低调奢华（Dark gradient background, drapery texture, understated luxury）",
      aesthetics:"巴洛克，戏剧光影，丰富细节，厚涂质感（baroque, dramatic lighting, rich details, impasto texture）",
      lighting:"伦勃朗光，侧光照明，面部立体感（Rembrandt lighting, side illumination, facial dimensionality）",
      medium:"油画，厚涂笔触，古典技法（oil painting, thick brushstrokes, classical technique）",
      photo_style:"", art_style:"巴洛克，戏剧光影，古典肖像（baroque, dramatic lighting, classical portrait）",
      style_color_palette:["#8b4513","#daa520","#2c1810","#f5deb3","#cd853f"],
      regions:[{x:0.15,y:0.05,w:0.7,h:0.6,type:"obj",desc:"人物肖像，华丽服饰，面部表情",palette:[]},{x:0,y:0,w:0.25,h:0.8,type:"obj",desc:"左侧帷幔，深色褶皱质感",palette:[]},{x:0.75,y:0,w:0.25,h:0.8,type:"obj",desc:"右侧帷幔，低调奢华背景",palette:[]},{x:0,y:0.65,w:1,h:0.35,type:"obj",desc:"深色渐变背景下部，手部细节",palette:[]}] },
    { label:"黄金时段风景", w:1360, h:768, style:"photo",
      high_level_description:"黄金时段壮丽风景，阳光洒落，山脉剪影，天空渐变（Magnificent golden hour landscape with sunlight rays, mountain silhouettes, sky gradient）",
      background:"连绵山脉，天空渐变橙红紫，云层层次（Rolling mountains, sky gradient of orange-red-purple, layered clouds）",
      aesthetics:"鲜艳饱和，高对比，金色暖调，壮丽感（vibrant, high contrast, golden warm tones, majestic feel）",
      lighting:"黄金时段，低角度暖光，长投影，轮廓光（golden hour, low-angle warm light, long shadows, rim lighting）",
      medium:"风光摄影，广角镜头，渐变滤镜（landscape photography, wide angle lens, graduated filter）",
      photo_style:"风光摄影，广角，黄金时段（landscape photography, wide angle, golden hour）",
      art_style:"", style_color_palette:["#ff8c00","#ff6347","#ffd700","#4a0080","#191970"],
      regions:[{x:0,y:0,w:1,h:0.35,type:"obj",desc:"天空渐变橙红紫，云层层次丰富",palette:[]},{x:0.3,y:0.15,w:0.4,h:0.2,type:"obj",desc:"太阳位置，金色光芒散射",palette:[]},{x:0,y:0.3,w:1,h:0.3,type:"obj",desc:"连绵山脉剪影，层次分明",palette:[]},{x:0,y:0.6,w:1,h:0.4,type:"obj",desc:"前景草甸，暖光洒落，长投影",palette:[]}] },
    { label:"微缩模型场景", w:1360, h:768, style:"photo",
      high_level_description:"移轴微缩模型效果，城市街道如玩具，选择性聚焦，超浅景深（A tilt-shift miniature scene making real city look like tiny toys with selective focus and ultra shallow DOF）",
      background:"城市街区俯瞰，建筑如模型，迷你车辆行人（Urban block aerial view with buildings like miniature models, tiny cars and pedestrians）",
      aesthetics:"鲜艳饱和，高对比，清晰锐利，趣味移轴效果（vibrant, saturated, high contrast, sharp, fun tilt-shift effect）",
      lighting:"日光直射，明亮均匀，色彩通透（direct sunlight, bright and even, clear colors）",
      medium:"移轴摄影，微缩效果，超浅景深（tilt-shift photography, miniature effect, ultra shallow depth of field）",
      photo_style:"移轴摄影，微缩模型效果，选择性聚焦（tilt-shift photography, miniature effect, selective focus）",
      art_style:"", style_color_palette:["#87ceeb","#98fb98","#ffb6c1","#dda0dd","#f0e68c"],
      regions:[{x:0,y:0,w:1,h:0.3,type:"obj",desc:"天空晴朗，云朵轻柔",palette:[]},{x:0,y:0.25,w:1,h:0.5,type:"obj",desc:"城市街区如玩具模型，移轴模糊带上下",palette:[]},{x:0,y:0.75,w:1,h:0.25,type:"obj",desc:"前景模糊虚化，强制浅景深感",palette:[]}] },
    { label:"古装全身人像", w:768, h:1024, style:"photo",
      high_level_description:"古装人物全身立像，汉服华美飘逸，姿态优雅，古典东方韵味（Full-body portrait in ancient Chinese Hanfu, elegant flowing robes, classical oriental grace）",
      background:"古风庭院，红墙绿瓦，梅花枝掩映，晨雾轻笼（Ancient courtyard with red walls and green tiles, plum blossoms, morning mist）",
      aesthetics:"东方古典意境，柔和色调，水墨留白，雅致温润（classical Eastern atmosphere, soft tones, ink-wash negative space, refined elegance）",
      lighting:"自然柔光，漫射天光，面部均匀柔和（natural soft light, diffused skylight, even gentle face lighting）",
      medium:"摄影，85mm镜头，中画幅数字（photograph, 85mm lens, medium format digital）",
      photo_style:"人像摄影，全身立像，古典风格（portrait photography, full body portrait, classical style）",
      art_style:"", style_color_palette:["#c0392b","#f5deb3","#8b4513","#2c3e50","#d4a574"],
      regions:[{x:0.1,y:0,w:0.8,h:0.15,type:"obj",desc:"古风屋檐，梅花枝桠",palette:[]},{x:0.1,y:0.1,w:0.8,h:0.7,type:"obj",desc:"人物全身，汉服华美飘逸，优雅站姿",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"庭院地面，青石砖瓦，落叶点缀",palette:[]}] },
    { label:"现代全身人像", w:768, h:1024, style:"photo",
      high_level_description:"现代时尚全身人像，潮流穿搭，自信姿态，都市生活氛围（Modern full-body fashion portrait with trendy outfit, confident pose, urban lifestyle vibe）",
      background:"城市街道或简洁影棚，干净利落，现代感（Urban street or clean studio backdrop, crisp and modern feel）",
      aesthetics:"现代简洁，高对比，锐利清晰，时尚杂志感（clean modern, high contrast, sharp clarity, fashion editorial feel）",
      lighting:"侧光加补光，轮廓分明，面部立体（side light with fill, defined contours, facial dimensionality）",
      medium:"时尚摄影，50mm镜头，f1.8大光圈（fashion photography, 50mm lens, f1.8 aperture）",
      photo_style:"时尚摄影，全身造型，街拍风格（fashion photography, full body styling, street style）",
      art_style:"", style_color_palette:["#2c3e50","#e74c3c","#ecf0f1","#f39c12","#34495e"],
      regions:[{x:0,y:0,w:1,h:0.15,type:"obj",desc:"城市天空或简洁背景上部",palette:[]},{x:0.1,y:0.1,w:0.8,h:0.7,type:"obj",desc:"人物全身，时尚穿搭，自信姿态",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"地面或街道，倒影投影",palette:[]}] },
    { label:"俯瞰视角大场景", w:1360, h:768, style:"photo",
      high_level_description:"高空俯瞰壮阔全景，大地脉络清晰，山河壮丽，气势磅礴（A breathtaking aerial panoramic view with earth's veins visible, magnificent mountains and rivers）",
      background:"连绵山脉河流，大地纹理，云层投影，色彩丰富（Rolling mountains and rivers, earth textures, cloud shadows, rich colors）",
      aesthetics:"壮丽辽阔，高对比，细节丰富，色彩饱和（majestic and vast, high contrast, rich details, saturated colors）",
      lighting:"黄金时段航拍光，低角度暖光，地形光影分明（golden hour aerial light, low-angle warm light, distinct terrain shadows）",
      medium:"航拍摄影，无人机，广角镜头（aerial drone photography, wide angle lens）",
      photo_style:"航拍鸟瞰，俯冲视角，风光全景（aerial drone photography, top-down perspective, panoramic landscape）",
      art_style:"", style_color_palette:["#2ecc71","#3498db","#f39c12","#8e44ad","#1abc9c"],
      regions:[{x:0,y:0,w:1,h:0.5,type:"obj",desc:"远处地平线，山脉层次，云层投影",palette:[]},{x:0,y:0.4,w:1,h:0.4,type:"obj",desc:"蜿蜒河流穿行峡谷，大地纹理",palette:[]},{x:0,y:0.75,w:1,h:0.25,type:"obj",desc:"前景山谷森林，纵深细节",palette:[]}] },
    { label:"厚涂游戏原画", w:1360, h:768, style:"art_style",
      high_level_description:"厚涂游戏概念原画，角色与场景交融，笔触粗犷有力，史诗感（Impasto game concept art with character and scene fusion, bold brushstrokes, epic feel）",
      background:"幻想世界战场或神秘遗迹，大气透视，恢弘壮阔（Fantasy battlefield or ancient ruins, atmospheric perspective, grandeur）",
      aesthetics:"厚涂质感，强笔触，高饱和，电影级构图（impasto texture, strong brushwork, high saturation, cinematic composition）",
      lighting:"戏剧体积光，丁达尔效应，光尘飞舞（dramatic volumetric light, god rays, floating dust particles）",
      medium:"数字绘画，厚涂技法，高细节，厚叠笔触（digital painting, impasto technique, highly detailed, thick layered strokes）",
      photo_style:"", art_style:"厚涂技法，游戏原画风格，史诗构图（impasto technique, game concept art style, epic composition）",
      style_color_palette:["#8b0000","#daa520","#2c1810","#4a0080","#ff8c00"],
      regions:[{x:0,y:0,w:1,h:0.3,type:"obj",desc:"天空火烧云，丁达尔光束穿透",palette:[]},{x:0.2,y:0.2,w:0.6,h:0.6,type:"obj",desc:"中心角色或主体，厚涂笔触质感",palette:[]},{x:0,y:0.7,w:1,h:0.3,type:"obj",desc:"前景地面，刮刀纹理，粗犷笔触",palette:[]}] },
    { label:"3D超写实修仙", w:1024, h:1024, style:"photo",
      high_level_description:"3D超写实超现实主义修仙场景，仙人飞升，天地异象，玄妙光芒（3D hyperrealistic surreal cultivation scene with immortals ascending, celestial phenomena, mystical light）",
      background:"云海仙山，悬浮山峰，金光万丈，灵气氤氲（Cloud sea with immortal mountains, floating peaks, golden rays, spiritual energy mist）",
      aesthetics:"超写实，超现实主义，空灵玄幻，高动态范围（hyperrealistic, surrealist, ethereal mystical, high dynamic range）",
      lighting:"体积光，金光穿云，神圣光辉，丁达尔弥漫（volumetric light, golden rays through clouds, divine glow, atmospheric god rays）",
      medium:"3D渲染，光追超写实，虚幻引擎，极致细节（3D render, photorealistic ray tracing, Unreal Engine, extreme detail）",
      photo_style:"", art_style:"超写实主义，超现实主义，幻想修真（hyperrealism, surrealism, fantasy cultivation）",
      style_color_palette:["#ffd700","#ffffff","#1a0a2e","#00bfff","#ff4500"],
      regions:[{x:0,y:0,w:1,h:0.35,type:"obj",desc:"天空金光万丈，云海翻涌，天地异象",palette:[]},{x:0.2,y:0.2,w:0.6,h:0.5,type:"obj",desc:"悬浮仙山，仙人飞升身影，灵气缠绕",palette:[]},{x:0,y:0.65,w:1,h:0.35,type:"obj",desc:"云海底部，山水倒映，玄妙光影",palette:[]}] },
    ];

let currentNode = null;

function injectStyles() {
    if (document.getElementById("cj-pb-style")) return;
    const s = document.createElement("style");
    s.id = "cj-pb-style";
    s.textContent = `
        .cj-pb{display:flex;flex-direction:column;gap:4px;padding:4px;font:12px sans-serif;color:#ccc;overflow-y:auto}
        .cj-pb-r{display:flex;align-items:center;gap:6px}
        .cj-pb-l{width:55px;flex:0 0 auto;color:#aaa;font-size:11px;text-align:left;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
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
        .cj-pb-cv{flex:1 1 auto;min-height:80px;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;position:relative;background:#111}
        .cj-pb-canvas{cursor:crosshair;display:block;flex:0 0 auto;background:#CCCCCC;border-radius:4px;outline:none;touch-action:none;min-width:100px;min-height:80px}
        .cj-pb-sw{width:16px;height:16px;border:1px solid #666;border-radius:3px;cursor:pointer;flex:0 0 auto}
        .cj-pb-pv{background:#1d1d1d;border:1px solid #333;border-radius:4px;padding:4px 6px;font:10px monospace;color:#aaa;white-space:pre-wrap;max-height:80px;overflow-y:auto;line-height:1.3}
        .cj-pb-panel{width:100%;box-sizing:border-box;background:#1d1d1d;border:1px solid #444;border-radius:4px;padding:6px 8px;font:11px sans-serif;color:#bbb;min-height:32px;max-height:100px;overflow-y:auto}
    `;
    document.head.appendChild(s);
    document.addEventListener("click", () => {
        document.querySelectorAll(".cj-pb-dd.open").forEach(x => x.classList.remove("open"));
    });
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
            item.textContent = p; item.title = p;
            item.addEventListener("click", (e) => { e.stopPropagation(); onSel(p); d.classList.remove("open"); });
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
function syncTokens(node) {} // placeholder for token counting
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
    function mouseNClamped(e) { const r = canvas.getBoundingClientRect(); return { x: Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)), y: Math.max(0,Math.min(1,(e.clientY-r.top)/r.height)) }; }
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
        ctx.fillStyle="#CCCCCC"; ctx.fillRect(0,0,W,H);
        // grid
        ctx.strokeStyle="rgba(0,0,0,0.1)"; ctx.lineWidth=1;
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
            // desc text clipped - 居中显示
            if(b.desc||b.text){
                ctx.save(); ctx.beginPath(); ctx.rect(x1,y1,w,h); ctx.clip();
                ctx.font="10px monospace"; ctx.fillStyle=readableText(col);
                let body=b.type==="text"&&b.text?`"${b.text}" ${b.desc||""}`:b.desc||"";
                const lines=wrapText(ctx,body,w-8);
                const lineHeight=12;
                const totalH=lines.length*lineHeight;
                let ty=y1+(h-totalH)/2+lineHeight;
                ctx.textAlign="center";
                for(const ln of lines){if(ty>y2-2)break;ctx.fillText(ln,x1+w/2,ty);ty+=lineHeight;}
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
            const nb={x:Math.max(0,Math.min(1,mN.x)),y:Math.max(0,Math.min(1,mN.y)),w:0,h:0,type:"obj",text:"",desc:"",palette:[]};
            s.regions.push(nb); s.activeRegion=s.regions.length-1;
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
        s.regions[s.activeRegion]=normBox(applyDrag(dragMode,boxStart,dx,dy));
        draw(); syncPreview(node); syncTokens(node);
    }
    function onUp(){
        drawing=false;
        document.removeEventListener("pointermove",onMove);
        document.removeEventListener("pointerup",onUp);
        const b=s.regions[s.activeRegion];
        if(b&&(b.w<0.005||b.h<0.005)&&dragMode==="draw"){s.regions.splice(s.activeRegion,1);s.activeRegion=Math.min(s.activeRegion,s.regions.length-1);}
        dragMode=null;boxStart=null;dragStart=null;
        draw(); sync();
        renderRegionPanel(node);
    }

    canvas.addEventListener("keydown",(e)=>{
        if(e.key==="Delete"||e.key==="Backspace"){
            if(s.activeRegion>=0&&s.activeRegion<s.regions.length){
                e.preventDefault();e.stopPropagation();
                s.regions.splice(s.activeRegion,1);
                s.activeRegion=Math.min(s.activeRegion,s.regions.length-1);
                draw();sync();
                renderRegionPanel(node);
            }
        }
    });

    node._cvFit=fitCanvas;
    node._cvDraw=draw;
    cvWrap.appendChild(canvas);
    return cvWrap;
}

function renderRegionPanel(node) {
    const s = node._pb;
    const panel = node._pbPanel;
    if (!panel) return;
    panel.innerHTML = "";
    const b = s.regions[s.activeRegion];
    if (!b) {
        const hint = document.createElement("div");
        hint.style.color = "#888";
        hint.textContent = s.regions.length ? "点击区域进行编辑" : "暂无区域";
        panel.appendChild(hint);
        return;
    }
    const col = COLORS[s.activeRegion % COLORS.length] || "#bbb";
    // Header
    const hdr = document.createElement("div");
    hdr.style.cssText = "display:flex;align-items:center;gap:6px;margin-bottom:4px;";
    const tag = document.createElement("span");
    tag.style.cssText = `font-weight:bold;color:${col};`;
    tag.textContent = "区域 " + (s.activeRegion + 1);
    hdr.appendChild(tag);
    // Type toggle
    const typeGrp = document.createElement("div");
    typeGrp.style.cssText = "display:flex;gap:4px;";
    const typeLabels = { "obj": "物体", "text": "文字" };
    for (const t of ["obj", "text"]) {
        const btn = document.createElement("button");
        btn.className = "cj-pb-btn" + (b.type === t ? " act" : "");
        btn.textContent = typeLabels[t] || t;
        btn.addEventListener("click", () => { b.type = t; renderRegionPanel(node); sync(); });
        typeGrp.appendChild(btn);
    }
    hdr.appendChild(typeGrp);
    // Delete button
    const delBtn = document.createElement("button");
    delBtn.className = "cj-pb-btn";
    delBtn.textContent = "删除";
    delBtn.style.cssText = "margin-left:auto;";
    delBtn.addEventListener("click", () => {
        s.regions.splice(s.activeRegion, 1);
        s.activeRegion = Math.min(s.activeRegion, s.regions.length - 1);
        renderRegionPanel(node);
        node._cvDraw?.();
        sync();
    });
    hdr.appendChild(delBtn);
    panel.appendChild(hdr);
    // Text (only for text type)
    if (b.type === "text") {
        const textRow = document.createElement("div"); textRow.className = "cj-pb-r";
        const textLbl = document.createElement("span"); textLbl.className = "cj-pb-l"; textLbl.textContent = "文本:";
        const textInp = document.createElement("input");
        textInp.className = "cj-pb-i";
        textInp.value = b.text || "";
        textInp.placeholder = "要渲染的文本";
        textInp.addEventListener("input", () => { b.text = textInp.value; node._cvDraw?.(); sync(); });
        textRow.append(textLbl, textInp);
        panel.appendChild(textRow);
    }
    // Description
    const descRow = document.createElement("div"); descRow.className = "cj-pb-r";
    const descLbl = document.createElement("span"); descLbl.className = "cj-pb-l"; descLbl.textContent = "描述:";
    const descInp = document.createElement("input");
    descInp.className = "cj-pb-i";
    descInp.value = b.desc || "";
    descInp.placeholder = "区域描述";
    descInp.addEventListener("input", () => { b.desc = descInp.value; node._cvDraw?.(); sync(); });
    descRow.append(descLbl, descInp);
    panel.appendChild(descRow);
}

function buildUI(node) {
    const s=node._pb;
    const wrap=document.createElement("div");wrap.className="cj-pb";

    // size
    const dimR=mkRow("尺寸:","画布尺寸");
    const wInp=document.createElement("input");wInp.className="cj-pb-num";wInp.type="number";wInp.min="64";wInp.max="16384";wInp.step="16";wInp.value=s.width;
    wInp.addEventListener("input",()=>{s.width=parseInt(wInp.value)||1024;node._cvFit?.();sync();});
    // Swap button
    const swapBtn=document.createElement("button");swapBtn.className="cj-pb-btn";swapBtn.textContent="\u21C4";swapBtn.title="交换宽高";
    swapBtn.addEventListener("click",()=>{const tmp=s.width;s.width=s.height;s.height=tmp;wInp.value=s.width;hInp.value=s.height;node._cvFit?.();sync();});
    const hInp=document.createElement("input");hInp.className="cj-pb-num";hInp.type="number";hInp.min="64";hInp.max="16384";hInp.step="16";hInp.value=s.height;
    hInp.addEventListener("input",()=>{s.height=parseInt(hInp.value)||1024;node._cvFit?.();sync();});
    // Preset sizes dropdown
    const presetSizes=[
        {label:"1:1 (1024×1024)",w:1024,h:1024},
        {label:"4:3 (1152×896)",w:1152,h:896},
        {label:"3:2 (1216×832)",w:1216,h:832},
        {label:"16:9 (1360×768)",w:1360,h:768},
        {label:"21:9 (1504×640)",w:1504,h:640},
        {label:"16:9 (1920×1080)",w:1920,h:1080},
        {label:"1:1 (2048×2048)",w:2048,h:2048},
        {label:"16:9 (2560×1600)",w:2560,h:1600},
        {label:"16:9 (4096×2300)",w:4096,h:2300}
    ];
    const sizeDropdown=document.createElement("div");sizeDropdown.className="cj-pb-dw";
    const sizeBtn=document.createElement("button");sizeBtn.className="cj-pb-db";sizeBtn.textContent="\u25BC";sizeBtn.title="预设尺寸";
    const sizeList=document.createElement("div");sizeList.className="cj-pb-dd";
    function buildSizeList(){
        sizeList.innerHTML="";
        for(const p of presetSizes){
            const item=document.createElement("div");item.className="cj-pb-di";
            item.textContent=p.label;
            item.addEventListener("click",(e)=>{e.stopPropagation();s.width=p.w;s.height=p.h;wInp.value=p.w;hInp.value=p.h;node._cvFit?.();sync();sizeList.classList.remove("open");});
            sizeList.appendChild(item);
        }
    }
    buildSizeList();
    sizeBtn.addEventListener("click",(e)=>{e.stopPropagation();const was=sizeList.classList.contains("open");document.querySelectorAll(".cj-pb-dd.open").forEach(x=>x.classList.remove("open"));if(!was){buildSizeList();sizeList.classList.add("open");}});
    sizeDropdown.append(sizeBtn,sizeList);
    dimR.append(wInp,swapBtn,hInp,sizeDropdown);wrap.appendChild(dimR);
    node._pbWInp=wInp; node._pbHInp=hInp;

    // scene preset
    const scR=mkRow("场景:","一键填充预设场景");
    const scDropdown=document.createElement("div");scDropdown.className="cj-pb-dw";scDropdown.style.cssText="display:inline-flex;align-items:center;gap:4px;";
    const scBtn=document.createElement("button");scBtn.className="cj-pb-db";scBtn.textContent="\u25BC";scBtn.title="预设场景";
    const scInp=document.createElement("input");scInp.className="cj-pb-i";scInp.value="none";scInp.readOnly=true;scInp.style.cssText="width:120px;flex:0 0 120px;cursor:pointer;background:#1a1a1a;";
    const scList=document.createElement("div");scList.className="cj-pb-dd";
    function positionScList(){
        const r=scInp.getBoundingClientRect();
        scList.style.position="fixed";
        scList.style.top=r.bottom+"px";
        scList.style.left=r.left+"px";
        scList.style.right="auto";
    }
    function buildScList(){
        scList.innerHTML="";
        for(const sc of SCENES){
            const item=document.createElement("div");item.className="cj-pb-di";
            item.textContent=sc.label;
            item.addEventListener("click",(e)=>{
                e.stopPropagation();
                Object.assign(s,{width:sc.width||sc.w,height:sc.height||sc.h,high_level_description:sc.high_level_description,background:sc.background,aesthetics:sc.aesthetics,lighting:sc.lighting,medium:sc.medium,photo_style:sc.photo_style||"",art_style:sc.art_style||"",style:sc.style||"none",style_color_palette:[...(sc.style_color_palette||[])],regions:(sc.regions||[]).map(r=>({...r,palette:[...(r.palette||[])]})),activeRegion:-1});
                wInp.value=s.width; hInp.value=s.height;
                for(const k of Object.keys(fEls)){fEls[k].input.value=s[k]||"";}
                photoI.value=s.photo_style; artI.value=s.art_style;
                updStyle(s.style);
                stGrp.querySelectorAll(".cj-pb-btn").forEach(b=>{b.classList.toggle("act",b.textContent===s.style);});
                buildScpSwatches();
                scInp.value=sc.label;
                node._cvFit?.(); node._cvDraw?.(); sync();
                renderRegionPanel(node);
                closeScList();
            });
            scList.appendChild(item);
        }
    }
    function closeScList(){scList.classList.remove("open");scList.remove();}
    buildScList();
    function toggleScList(e){
        e.stopPropagation();
        const was=scList.classList.contains("open");
        document.querySelectorAll(".cj-pb-dd.open").forEach(x=>{x.classList.remove("open");x.remove();});
        if(!was){buildScList();positionScList();document.body.appendChild(scList);scList.classList.add("open");}
    }
    scBtn.addEventListener("click",toggleScList);
    scInp.addEventListener("click",toggleScList);
    scDropdown.append(scInp,scBtn); scR.appendChild(scDropdown); wrap.appendChild(scR);

    // style
    const stR=mkRow("风格:","");
    const stGrp=document.createElement("div");stGrp.style.cssText="display:flex;gap:4px;flex:1;";
    const photoR=mkRow("摄影:","");const artR=mkRow("艺术风格:","");
    const photoI=mkInp(s.photo_style||"",false,"");photoI.addEventListener("input",()=>{s.photo_style=photoI.value;sync();});
    photoR.appendChild(photoI);photoR.appendChild(mkDropdown(PRESETS.photo_style,v=>{photoI.value=v;s.photo_style=v;sync();}));
    const artI=mkInp(s.art_style||"",false,"");artI.addEventListener("input",()=>{s.art_style=artI.value;sync();});
    artR.appendChild(artI);artR.appendChild(mkDropdown(PRESETS.art_style,v=>{artI.value=v;s.art_style=v;sync();}));
    function updStyle(t){
        s.style=t;
        photoR.style.display=t==="photo"?"flex":"none";
        artR.style.display=t==="art_style"?"flex":"none";
        if(t!=="photo"){s.photo_style="";photoI.value="";}
        if(t!=="art_style"){s.art_style="";artI.value="";}
        sync();
    }
    for(const t of["none","photo","art_style"]){const b=document.createElement("button");b.className="cj-pb-btn"+(s.style===t?" act":"");b.textContent=t;b.addEventListener("click",()=>{stGrp.querySelectorAll(".cj-pb-btn").forEach(x=>x.classList.remove("act"));b.classList.add("act");updStyle(t);sync();});stGrp.appendChild(b);}
    stR.appendChild(stGrp);wrap.appendChild(stR);wrap.appendChild(photoR);wrap.appendChild(artR);

    // param fields
    const fields=[
        {l:"描述:",t:"整体画面概述",ml:false,p:PRESETS.high_level_description,k:"high_level_description"},
        {l:"背景:",t:"场景背景描述",ml:false,p:PRESETS.background,k:"background"},
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

    // region edit panel (standalone row)
    const regionPanel = document.createElement("div"); regionPanel.className = "cj-pb-panel";
    node._pbPanel = regionPanel;
    wrap.appendChild(regionPanel);

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
    renderRegionPanel(node);
}

function chainCallback(obj,prop,cb){const old=obj[prop];obj[prop]=function(...args){const r=old?.apply(this,args);cb.apply(this,args);return r;};}

app.registerExtension({
    name:"CJNodes.PromptBuilder",
    async beforeRegisterNodeDef(nodeType,nodeData){
        if(nodeData.name!=="PromptBuilderNode")return;
        injectStyles();
        chainCallback(nodeType.prototype,"onNodeCreated",function(){
            const node=this;currentNode=node;
            node._pb={width:1360,height:768,high_level_description:"",background:"",style:"none",aesthetics:"",lighting:"",medium:"",photo_style:"",art_style:"",style_color_palette:[],regions:[],activeRegion:-1};
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
