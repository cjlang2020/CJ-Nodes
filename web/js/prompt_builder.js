import { app } from "../../../../scripts/app.js";

const HANDLE = 8;
const COLORS = ["#e74c3c","#3498db","#2ecc71","#f39c12","#9b59b6","#1abc9c","#e67e22","#34495e"];

// ──────────────────────────────────────────────
//  PRESETS — values are in English per spec (scene/elements/desc must be English)
//  Chinese labels are only used in SCENES.label for UI navigation
// ──────────────────────────────────────────────
const PRESETS = {
    high_level_description: [
        "A cinematic portrait of a character in a dramatic scene",
        "A serene landscape with soft lighting and a tranquil atmosphere",
        "An abstract composition with geometric shapes and layered textures",
        "A detailed still life arrangement with natural elements and rich textures",
        "A fantasy scene with magical atmosphere and an ethereal glow",
        "A realistic urban street scene at golden hour with warm sunlight",
        "A minimalist design with clean lines, subtle gradients, and ample negative space",
        "A dramatic action scene with dynamic composition and high energy",
        "A dreamy underwater scene with bioluminescent organisms and caustic light",
        "A cozy interior scene with soft ambient lighting and comfortable furnishings",
        "A surrealist dreamscape with melting clocks, impossible geometry, and floating forms",
        "A cyberpunk scene with neon signs, rain-soaked streets, and holographic advertisements",
        "A vintage film-style lifestyle scene with nostalgic period details",
        "A dark horror atmosphere with eerie fog, shadowy figures, and a foreboding mood",
        "A pastoral countryside scene with golden wheat fields, rustic charm, and open skies",
        "A sci-fi space scene with cosmic nebulae, distant stars, and futuristic spacecraft",
        "An aerial bird's eye view of a dramatic landscape with sweeping topography",
        "A microscopic world with extreme cellular detail and intricate patterns",
        "Post-apocalyptic ruins overgrown with creeping vines, moss, and encroaching vegetation",
        "A steampunk mechanical contraption with brass gears, copper pipes, and Victorian details",
        "Aurora borealis dancing over glacial ice formations with ethereal green and purple light",
        "Classical Eastern ink wash painting atmosphere with misty mountains and elegant negative space",
    ],
    background: [
        "A vast open field with wildflowers under a clear blue sky with soft clouds",
        "A dense forest interior with broad tree trunks, sunlight filtering through the canopy, and a carpet of fallen leaves",
        "A futuristic cityscape with sleek skyscrapers, neon accents, and elevated transit lines",
        "A quiet room with large windows, white walls, and soft natural light entering from the side",
        "A misty mountain landscape at dawn with layers of fog between the peaks",
        "A sunlit beach with gentle waves lapping at golden sand and a soft horizon line",
        "A dark moody alley with brick walls, a single overhead lamp, and deep shadow pools",
        "A lush garden with dense blooming flowers of mixed colors and hovering butterflies",
        "A snowy mountain peak under a starlit sky with a crescent moon and deep blue firmament",
        "A professional studio backdrop with seamless paper, soft gradient lighting, and clean surroundings",
        "An industrial warehouse with exposed brick walls, metal beams, and concrete flooring",
        "A floating island suspended in a sky filled with soft cumulus clouds at sunset",
        "Desert sand dunes stretching to the horizon under a sky transitioning from gold to deep purple",
        "An underwater coral reef with branching corals, kelp fronds, and rays of light from the surface",
        "A deep space nebula field with swirling cosmic dust, scattered stars, and distant galaxies",
        "Ancient stone ruins with weathered pillars, cracked paving, and moss creeping over every surface",
        "A rain-soaked city street at night with wet pavement reflecting vivid neon signs overhead",
        "A bustling night market with rows of stalls, hanging paper lanterns, and smoke from food grills",
        "A dramatic cliff edge of layered sedimentary rock overlooking churning ocean waves below",
        "A grand library interior with towering floor-to-ceiling bookshelves, a vaulted ceiling, and warm reading lamps",
        "An abandoned building interior with peeling wallpaper, shattered windows, and vines pushing through cracks",
        "An underground crystal cave with faceted mineral formations catching and refracting ambient light",
    ],
    aesthetics: [
        "cinematic, dramatic contrast, moody atmosphere, teal and orange",
        "vibrant, saturated colors, high contrast, energetic",
        "muted tones, pastel palette, soft and dreamy, delicate",
        "dramatic, chiaroscuro, high dynamic range, sculptural light",
        "vintage, retro, faded colors, analog character",
        "clean, modern, sleek and polished, refined",
        "ethereal, otherworldly, translucent, gossamer quality",
        "bold, graphic, high-impact, strong silhouettes",
        "natural, organic, earthy tones, grounded",
        "luxurious, opulent, rich textures, ornate",
        "noir, moody, desaturated, shadow-heavy",
        "tropical, vivid botanical hues, saturated greens and corals",
        "steampunk, brass and copper tones, mechanical intricacy",
        "cyberpunk, neon accents, dark urban, reflective surfaces",
        "holographic, iridescent, shifting prismatic highlights, futuristic sheen",
        "high-key, bright, airy, overexposed quality, minimal shadows",
        "low-key, deep shadows, moody darkness, dramatic contrast",
        "duotone, two-color palette, graphic simplicity, flat color fields",
        "grainy film texture, analog halation, soft emulsion character",
        "matte finish, soft veiling, desaturated, velvety surface quality",
        "glossy, reflective, glass-like transparency, specular highlights",
        "metallic, chrome, polished reflective surfaces, industrial precision",
    ],
    lighting: [
        "natural daylight, soft and even, open sky fill",
        "golden hour, low-angle side light, long soft shadows",
        "dramatic rim lighting, backlight, edge illumination",
        "studio lighting, three-point setup, softbox key, fill and rim",
        "moonlight, cool blue tones, silver ambient glow",
        "neon lighting, multicolored reflections, saturated color casts",
        "candlelight, flickering intimate pool of light, amber glow",
        "overcast, diffused soft light, no hard shadows, even wrapping",
        "spotlight, focused beam, high contrast, pool of light on subject",
        "volumetric light, god rays, light piercing through atmospheric particles",
        "bioluminescent, self-illuminated, soft glow from within",
        "dappled light through leaves, shifting speckled pattern on surfaces",
        "Rembrandt lighting, triangle of light on the cheek, dramatic portrait",
        "butterfly lighting, glamour portrait, soft shadow under the nose",
        "split lighting, half the face illuminated, the other in shadow",
        "practical lighting, visible lamps, windows, and fixtures casting scene light",
        "firelight, flickering orange glow, dancing highlight shift, campfire ambiance",
        "blue hour, twilight deep blue sky, emerging city lights in the distance",
        "harsh midday sun, strong defined shadows, high contrast, bright highlights",
        "projected patterns, gobo lighting, structural shadow shapes on surfaces",
        "uplighting, dramatic illumination from below, hollow cheek shadows",
        "hazy smoky light, diffused beam through fog, soft atmospheric glow",
    ],
    medium: [
        "digital painting",
        "oil painting",
        "watercolor",
        "pencil sketch",
        "3d_render",
        "photograph",
        "concept art",
        "anime style",
        "pixel art",
        "collage",
        "vector illustration",
        "charcoal drawing",
        "acrylic painting",
        "ink wash painting",
        "pastel drawing",
        "clay render",
        "mosaic",
        "stained glass",
        "woodcut print",
        "spray paint graffiti",
        "screen print",
        "embroidery",
    ],
    photo: [
        "portrait photography, 85mm lens, eye-level perspective, shallow depth of field",
        "landscape photography, wide angle lens, sharp throughout, generous depth of field",
        "macro photography, extreme close-up, fine detail resolution",
        "street photography, candid, 35mm wide angle, eye-level",
        "fashion photography, studio setup, medium format, controlled lighting",
        "food photography, top-down or 45-degree angle, appetizing styling",
        "architectural photography, tilt-shift lens, corrected perspective, clean geometry",
        "wildlife photography, telephoto lens, natural behavior, environmental context",
        "astrophotography, long exposure, deep sky tracking",
        "documentary style, photojournalistic framing, natural moment",
        "fine art photography, conceptual composition, gallery presentation",
        "product photography, clean background, even lighting, sharp detail",
        "aerial drone photography, top-down perspective, bird's eye composition",
        "underwater photography, natural light from surface, blue-green color cast",
        "infrared photography, false color rendering, surreal foliage tones",
        "long exposure, light trails, smooth water surface, motion abstraction",
        "double exposure, layered imagery, translucent overlapping forms",
        "tilt-shift photography, selective focus plane, miniature scene effect",
        "black and white film, silver grain, high contrast monochrome",
        "editorial magazine photography, styled narrative, composed frame",
        "sports action photography, frozen motion, fast shutter, dynamic angle",
        "night cityscape, long exposure, vibrant urban lighting, time-lapse quality",
    ],
    art_style: [
        "impressionist, visible brushstrokes, focus on light and color over detail",
        "surrealist, dreamlike imagery, unexpected juxtapositions, fantastical elements",
        "art nouveau, flowing organic lines, decorative borders, nature-inspired motifs",
        "pop art, bold primary colors, comic-inspired halftone dots, mass culture references",
        "cubist, fragmented geometric forms, multiple perspectives, angular planes",
        "baroque, dramatic chiaroscuro, rich ornamentation, opulent detail",
        "ukiyo-e, Japanese woodblock print, flat color areas, strong outlines, elegant curves",
        "art deco, geometric patterns, symmetrical compositions, luxurious materials",
        "expressionist, emotional intensity, distorted forms, bold non-naturalistic colors",
        "minimalist, reduced forms, essential elements, generous negative space",
        "psychedelic, vibrant swirling patterns, kaleidoscopic symmetry, intense color",
        "gothic, dark ornate atmosphere, pointed arches, elaborate tracery",
        "romanticism, sublime natural scenery, emotional landscape, dramatic skies",
        "realism, faithful everyday representation, precise detail, natural color",
        "neoclassicism, orderly composition, classical poses, restrained palette",
        "rococo, ornate decoration, pastel colors, playful elegance, asymmetrical design",
        "renaissance, chiaroscuro modeling, linear perspective, balanced pyramidal composition",
        "fauvism, wild expressive colors, simplified forms, non-naturalistic palette",
        "constructivism, geometric abstraction, industrial materials, bold typography",
        "De Stijl, primary colors, grid composition, horizontal and vertical lines",
        "hyperrealism, extreme precision, photo-like detail, smooth surface finish",
        "vaporwave, retro digital aesthetic, pink and teal palette, glitch artifacts, neon grids",
    ],
};

const SCENES = [
    { label:"电影感肖像", w:1024, h:1536, style:"photo",
      high_level_description:"A cinematic close-up portrait with dramatic Rembrandt lighting and an intense gaze, shallow depth of field",
      background:"A dark out-of-focus background with soft circular light orbs and a deep atmosphere",
      aesthetics:"cinematic, dramatic contrast, moody atmosphere, teal and orange",
      lighting:"Rembrandt lighting, triangle of light on cheek, side illumination, deep shadow on half the face",
      medium:"photograph",
      photo:"portrait photography, 85mm lens, eye-level perspective, shallow depth of field",
      art_style:"", style_color_palette:["#C87533","#1A3A4A","#E8D5B7","#2D2D2D","#F0E6D3"],
      regions:[{x:0.15,y:0.05,w:0.7,h:0.7,type:"obj",desc:"A fair-skinned person with a direct intense gaze, dramatic side lighting creating a triangle highlight on one cheek, expression is serious and contemplative",palette:[]}] },
    { label:"赛博朋克都市", w:1360, h:768, style:"photo",
      high_level_description:"A cyberpunk cityscape at night with neon signs, rain-soaked streets, and holographic billboards reflecting off wet pavement",
      background:"A futuristic urban street lined with towering buildings covered in neon signs, wet asphalt road surface reflecting all lights, misty atmosphere",
      aesthetics:"cyberpunk, neon purple and blue, high contrast, wet reflective surfaces",
      lighting:"neon lighting, multicolored reflections, wet pavement glow, ambient colored light",
      medium:"3d_render",
      photo:"night cityscape, long exposure, vibrant neon lighting, wet surface reflections",
      art_style:"", style_color_palette:["#FF00FF","#00FFFF","#1A0A2E","#FF6B35","#0D1B2A"],
      regions:[{x:0,y:0.3,w:1,h:0.4,type:"obj",desc:"A cluster of futuristic skyscrapers covered in glowing neon signs and holographic displays reflecting in the rain",palette:[]},{x:0,y:0.7,w:1,h:0.3,type:"obj",desc:"A lone figure in a hooded coat walking on a rain-slicked sidewalk under neon glow, surrounded by puddles reflecting pink and blue light",palette:[]}] },
    { label:"奇幻魔法森林", w:1024, h:1024, style:"art_style",
      high_level_description:"A mystical enchanted forest with glowing bioluminescent flora, tiny floating lights, and a magical mist weaving through ancient trees",
      background:"An ancient dense forest with towering broad trunks covered in luminous moss, a thick rolling mist at ground level, and beams of light piercing the canopy above",
      aesthetics:"ethereal, otherworldly, soft glow, dreamy saturated colors",
      lighting:"volumetric light, god rays piercing through the canopy, bioluminescent accents from plants and fungi",
      medium:"digital painting",
      photo:"", art_style:"impressionist, visible brushstrokes, emphasis on atmospheric light and color rather than hard detail",
      style_color_palette:["#2ECC71","#9B59B6","#1ABC9C","#F1C40F","#27AE60"],
      regions:[{x:0,y:0,w:0.3,h:1,type:"obj",desc:"An ancient towering tree trunk covered in glowing moss and tiny luminous fungi dots on the left side of the frame",palette:[]},{x:0.7,y:0,w:0.3,h:1,type:"obj",desc:"A second large tree trunk on the right with hanging vines and swirling mist wrapping around its base",palette:[]},{x:0.2,y:0.4,w:0.6,h:0.5,type:"obj",desc:"A winding forest path glowing with bioluminescent blue mushrooms and floating dust-like light particles",palette:[]}] },
    { label:"宁静湖畔风光", w:1360, h:768, style:"photo",
      high_level_description:"A serene lakeside at dawn with mirror-like water reflecting distant snow-capped mountains, gentle mist rising, and a soft pastel sky",
      background:"An expansive lake surface stretching to a low horizon with layered mountain silhouettes in the distance, soft dawn mist, and a sky transitioning from pink to pale blue",
      aesthetics:"soft muted tones, fresh and clear, natural realism, airy atmosphere",
      lighting:"golden hour, soft morning light from behind the mountains, mirror-like reflection on still water",
      medium:"photograph",
      photo:"landscape photography, wide angle lens, generous depth of field, panoramic composition",
      art_style:"", style_color_palette:["#87CEEB","#2C3E50","#ECF0F1","#3498DB","#1A5276"],
      regions:[{x:0,y:0.45,w:1,h:0.35,type:"obj",desc:"The calm lake surface reflecting the mountain silhouettes and soft sky colors with perfect mirror symmetry",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"A rocky shoreline at the lake edge with small pebbles and patches of green moss in soft morning light",palette:[]}] },
    { label:"恐怖古堡", w:1024, h:1536, style:"art_style",
      high_level_description:"A haunted castle interior with a long eerie corridor, flickering candlelight casting long shadows, and heavy cobwebs hanging from the ceiling",
      background:"An ancient castle corridor with rough stone walls, a vaulted stone ceiling with arches, iron candelabras mounted on walls, deep shadow pools between pools of candlelight, and a stone floor with scattered dust",
      aesthetics:"noir, desaturated, strong chiaroscuro, film grain texture, moody darkness",
      lighting:"candlelight, flickering pools of amber light, long dramatic shadows stretching along the floor, partial illumination",
      medium:"concept art",
      photo:"", art_style:"gothic, dark ornate atmosphere, pointed arches, elaborate tracery, moody palette",
      style_color_palette:["#8B0000","#2C2C2C","#D4A574","#1A1A1A","#C0392B"],
      regions:[{x:0.1,y:0,w:0.8,h:0.12,type:"obj",desc:"A vaulted stone ceiling with heavy cobwebs draping between arches, dust particles visible in the light",palette:[]},{x:0,y:0.15,w:0.25,h:0.7,type:"obj",desc:"A rough stone wall on the left with an iron candelabra holding three lit candles casting warm light upward",palette:[]},{x:0.75,y:0.15,w:0.25,h:0.7,type:"obj",desc:"The right stone wall with deep shadow pools and a dark wooden door slightly ajar",palette:[]},{x:0.2,y:0.25,w:0.6,h:0.5,type:"obj",desc:"The corridor vanishing point deep in shadow with a faint arched window at the far end barely visible through darkness",palette:[]}] },
    { label:"产品广告", w:1024, h:1024, style:"photo",
      high_level_description:"A premium product advertisement with refined studio lighting, a clean gradient background, and elegant composition emphasizing texture and form",
      background:"A seamless gradient backdrop transitioning from pure white to soft light grey with a subtle shadow beneath the product",
      aesthetics:"clean, modern, sleek and polished, high gloss, minimal and refined",
      lighting:"studio lighting, three-point setup, softbox overhead, white reflector fill from below, controlled specular highlights",
      medium:"photograph",
      photo:"product photography, macro lens, focus stacking for full sharpness, clean background presentation",
      art_style:"", style_color_palette:["#FFFFFF","#F5F5F5","#E0E0E0","#333333","#C0C0C0"],
      regions:[{x:0.2,y:0.2,w:0.6,h:0.55,type:"obj",desc:"A sleek product bottle with a minimalist label and metallic cap, glossy surface catching a controlled specular highlight along the edge",palette:[]}] },
    { label:"时尚大片", w:1024, h:1536, style:"photo",
      high_level_description:"A fashion magazine editorial portrait with a model in avant-garde clothing and bold artistic makeup against a solid color studio backdrop",
      background:"A solid saturated studio backdrop with smooth even color, clean seamless transition to the floor, minimal set design",
      aesthetics:"high-key, fashion-forward, editorial quality, sharp details, refined color",
      lighting:"softbox key light from above, rim light for edge separation, butterfly lighting pattern on face",
      medium:"photograph",
      photo:"fashion photography, medium format digital, studio setup, controlled directional lighting",
      art_style:"", style_color_palette:["#FF1493","#000000","#FFFFFF","#DC143C","#F0F0F0"],
      regions:[{x:0.15,y:0.05,w:0.7,h:0.85,type:"obj",desc:"A female model with bold red lipstick and geometric eyeliner, wearing an avant-garde structured black jacket with sharp shoulders, one hand on hip, direct confident gaze",palette:[]}] },
    { label:"美食特写", w:1024, h:1024, style:"photo",
      high_level_description:"A gourmet food close-up with elegant plating, fresh ingredients, and appetizing textures captured in soft natural window light",
      background:"A wooden table surface with a subtle linen placemat, soft natural light from a nearby window creating gentle shadows",
      aesthetics:"natural tones, fresh and organic, appetizing textures, soft natural light quality",
      lighting:"side backlight from a window, diffused daylight, gentle highlights on food surfaces, soft shadows on the table",
      medium:"photograph",
      photo:"food photography, 100mm macro lens, 45-degree angle, shallow depth of field on hero ingredient",
      art_style:"", style_color_palette:["#D4A574","#8B4513","#F5DEB3","#2E8B57","#CD853F"],
      regions:[{x:0.1,y:0.1,w:0.8,h:0.5,type:"obj",desc:"A plate with seared steak topped with fresh herbs and a red wine reduction drizzle, garnished with micro greens on the side",palette:[]},{x:0,y:0.6,w:1,h:0.4,type:"obj",desc:"A wooden table surface with a folded white linen napkin, a polished fork and knife placed beside the plate, soft shadows cast by the window light",palette:[]}] },
    { label:"建筑空间", w:1360, h:768, style:"photo",
      high_level_description:"A modern architectural interior with clean geometric lines, interplay of natural light and shadow, and minimalist material palette",
      background:"An open-plan concrete and glass structure with a white ceiling, polished concrete flooring, a floor-to-ceiling window wall allowing natural light to pour in",
      aesthetics:"clean, geometric composition, light-shadow contrast, spatial depth, minimalist refinement",
      lighting:"natural daylight from large windows, skylight diffusion, geometric shadow patterns cast by structural elements",
      medium:"photograph",
      photo:"architectural photography, tilt-shift lens, corrected perspective, symmetrical composition",
      art_style:"", style_color_palette:["#808080","#F5F5F5","#2C3E50","#BDC3C7","#ECF0F1"],
      regions:[{x:0,y:0.2,w:0.4,h:0.6,type:"obj",desc:"A raw concrete wall on the left with horizontal formwork lines and a sharp geometric shadow from the window frame",palette:[]},{x:0.6,y:0.2,w:0.4,h:0.6,type:"obj",desc:"A floor-to-ceiling glass curtain wall on the right framing a view of the sky and city skyline beyond",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"Polished concrete floor reflecting the window grid pattern in soft grey tones",palette:[]}] },
    { label:"动漫角色", w:768, h:1024, style:"art_style",
      high_level_description:"An anime-style character with large expressive eyes, a dynamic pose, vibrant hair color, and clean cel-shaded rendering against a gradient background",
      background:"A gradient background shifting from bright cyan at the top to soft pink at the bottom with floating light particle effects",
      aesthetics:"vibrant, cel-shaded, clean linework, saturated colors, Japanese animation aesthetic",
      lighting:"even soft light, face fill illumination, bright specular highlights on hair strands",
      medium:"anime style",
      photo:"", art_style:"anime style, cel shading, clean outlines, flat color areas with soft shadow shapes, Japanese aesthetic",
      style_color_palette:["#FF6B9D","#C44DFF","#4DC9F6","#FFE066","#FF4757"],
      regions:[{x:0.1,y:0.05,w:0.8,h:0.7,type:"obj",desc:"A female anime character with long flowing pink hair, large bright blue eyes with star-shaped highlights, a school uniform with a red ribbon, one arm raised with a peace sign",palette:[]}] },
    { label:"蒸汽朋克世界", w:1360, h:768, style:"art_style",
      high_level_description:"A steampunk world with brass gear mechanisms, a hydrogen airship floating in the sky, and ornate Victorian architecture",
      background:"An industrial sky with a sepia-toned haze, copper pipe networks along building exteriors, steam venting from pressure valves, and a warm overcast atmosphere",
      aesthetics:"steampunk, brass and copper tones, warm brown palette, retro-futuristic mechanical details",
      lighting:"firelight glow from furnaces, steam diffusion softening the light, warm metallic highlights on brass surfaces",
      medium:"digital painting",
      photo:"", art_style:"art nouveau inspired, flowing organic lines, decorative mechanical details, ornate borders and flourishes",
      style_color_palette:["#B87333","#CD853F","#8B4513","#DAA520","#704214"],
      regions:[{x:0,y:0,w:0.35,h:0.55,type:"obj",desc:"A large mechanical apparatus with brass gears, copper steam pipes with riveted joints, pressure gauges, and a coal furnace glowing orange",palette:[]},{x:0.65,y:0,w:0.35,h:0.55,type:"obj",desc:"A Victorian brick building facade with arched windows, a wrought-iron balcony, and a copper pipe network running up the wall",palette:[]},{x:0.25,y:0.05,w:0.5,h:0.3,type:"obj",desc:"A hydrogen airship with a brass gondola and a large striped canvas envelope floating in the hazy sky",palette:[]}] },
    { label:"末日废墟", w:1360, h:768, style:"photo",
      high_level_description:"Post-apocalyptic city ruins with collapsed concrete buildings, exposed rebar, vegetation reclaiming the structures, and a desolate atmosphere",
      background:"A wide abandoned city street flanked by crumbling high-rise buildings, broken asphalt cracked by tree roots, dust particles suspended in the air, an overcast grey sky above",
      aesthetics:"desaturated, grey-green tones, decay aesthetic, raw and weathered",
      lighting:"overcast diffused light, even grey ambient illumination, no harsh shadows, flat shadowless daylight",
      medium:"photograph",
      photo:"documentary style, photojournalistic framing, natural moment, raw realism",
      art_style:"", style_color_palette:["#556B2F","#696969","#8FBC8F","#2F4F4F","#A9A9A9"],
      regions:[{x:0,y:0,w:0.4,h:0.5,type:"obj",desc:"A partially collapsed concrete building with exposed steel rebar, shattered windows, and climbing ivy covering the remaining facade",palette:[]},{x:0.6,y:0,w:0.4,h:0.5,type:"obj",desc:"A leaning building facade with a large crack running diagonally and a rusted fire escape hanging loose from the wall",palette:[]},{x:0,y:0.6,w:1,h:0.4,type:"obj",desc:"A broken asphalt road surface with large cracks, weeds and grass pushing through, scattered rubble and a rusted car skeleton",palette:[]}] },
    { label:"深海奇遇", w:1024, h:1536, style:"art_style",
      high_level_description:"A fantastical deep-sea world with glowing jellyfish drifting upward, vibrant coral formations, and shafts of light piercing the water from the surface",
      background:"A deep ocean environment with a dark blue gradient fading to black toward the bottom, a coral reef structure on the sea floor, and long rays of sunlight descending from the surface above",
      aesthetics:"ethereal, bioluminescent, deep blue-green tones, dreamy underwater atmosphere",
      lighting:"volumetric light beams from the surface, bioluminescent glow from marine organisms, caustic light patterns on surfaces",
      medium:"digital painting",
      photo:"", art_style:"impressionist, soft blended brushwork, emphasis on atmospheric light and glowing color",
      style_color_palette:["#006994","#40E0D0","#00CED1","#20B2AA","#008B8B"],
      regions:[{x:0.15,y:0.15,w:0.7,h:0.35,type:"obj",desc:"A cluster of translucent glowing jellyfish with long trailing tentacles drifting upward toward the light, their bodies emitting a soft bioluminescent blue",palette:[]},{x:0,y:0.55,w:1,h:0.3,type:"obj",desc:"A coral reef structure with branching corals in shades of orange and purple, sea anemones, and small tropical fish swimming between the formations",palette:[]},{x:0,y:0.85,w:1,h:0.15,type:"obj",desc:"The sandy ocean floor with scattered shells and small glowing organisms embedded in the sediment",palette:[]}] },
    { label:"太空科幻", w:1360, h:768, style:"photo",
      high_level_description:"A space sci-fi scene featuring an interstellar spacecraft drifting through a colorful nebula with dense star fields and distant galaxies",
      background:"Deep space with a swirling emission nebula in magenta and cyan, scattered bright stars of varying sizes, and faint distant spiral galaxies visible in the background",
      aesthetics:"high contrast, cool tones, cosmic scale, deep color saturation",
      lighting:"direct starlight from a nearby star system, ambient nebula glow, spacecraft navigation lights",
      medium:"3d_render",
      photo:"astrophotography, long exposure, deep sky objects, wide field perspective",
      art_style:"", style_color_palette:["#0A0A2E","#4A0080","#00BFFF","#191970","#E0FFFF"],
      regions:[{x:0.2,y:0.25,w:0.6,h:0.35,type:"obj",desc:"A sleek interstellar spacecraft with a long hull, glowing engine nacelles emitting blue exhaust, solar panel arrays, and a cockpit window glowing amber",palette:[]},{x:0,y:0.5,w:1,h:0.5,type:"obj",desc:"A dense nebula cloud in magenta, cyan, and deep purple with bright embedded stars, wisps of cosmic dust, and a spiral galaxy faintly visible in the distance",palette:[]}] },
    { label:"复古怀旧", w:1024, h:1024, style:"photo",
      high_level_description:"A vintage nostalgic street scene with a classic 1960s automobile parked beneath a warm yellow street lamp at dusk in a European old town",
      background:"A narrow European old town street with historic buildings with shuttered windows, cobblestone pavement, a gentle dusk sky transitioning from blue to amber, and a single street lamp casting a warm pool of light",
      aesthetics:"vintage film look, muted warm tones, soft halation, nostalgic atmosphere",
      lighting:"golden hour fading into dusk, street lamp as primary light source, warm directional side light, long soft shadows across the street",
      medium:"photograph",
      photo:"street photography, 50mm lens, candid mood, available light, film character",
      art_style:"", style_color_palette:["#D4A574","#C19A6B","#8B7355","#DAA520","#F5DEB3"],
      regions:[{x:0,y:0,w:0.35,h:0.6,type:"obj",desc:"A row of historic townhouses with warm-lit ground-floor windows, decorative wrought-iron balcony rails, and window boxes with red geraniums",palette:[]},{x:0.65,y:0,w:0.35,h:0.6,type:"obj",desc:"A matching row of buildings on the opposite side with a corner bistro showing amber light through a glass door",palette:[]},{x:0.25,y:0.25,w:0.5,h:0.4,type:"obj",desc:"A vintage teal 1960s sedan parked at the curb with chrome bumpers catching the street lamp reflection and a curved windshield",palette:[]},{x:0,y:0.6,w:1,h:0.4,type:"obj",desc:"Cobblestone paving with a wet sheen reflecting the warm street lamp light and the car's silhouette",palette:[]}] },
    { label:"极简抽象", w:1024, h:1024, style:"art_style",
      high_level_description:"A minimalist abstract composition with precise geometric shapes, generous negative space, and a restrained pure color palette",
      background:"A pure white background with subtle off-white texture, expansive negative space framing the composition",
      aesthetics:"minimalist, reduced forms, less is more, pure and clean, balanced",
      lighting:"even diffused light, no shadows, flat uniform illumination",
      medium:"vector illustration",
      photo:"", art_style:"minimalist, reduced essential forms, generous negative space, clean geometric precision",
      style_color_palette:["#FFFFFF","#000000","#E74C3C","#F5F5F5","#333333"],
      regions:[{x:0.15,y:0.15,w:0.3,h:0.3,type:"obj",desc:"A perfect red circle in the upper-left quadrant, solid fill with no outline, positioned with balanced negative space around it",palette:[]},{x:0.55,y:0.5,w:0.3,h:0.35,type:"obj",desc:"A black right-angled triangle in the lower-right quadrant, sharp clean edges, positioned to counterbalance the red circle",palette:[]}] },
    { label:"微距自然", w:1024, h:1024, style:"photo",
      high_level_description:"An extreme macro nature shot of a dewdrop-covered flower petal with intricate surface texture, backlit by soft warm light",
      background:"Soft out-of-focus green foliage in the background creating a gentle colorful bokeh, natural atmosphere",
      aesthetics:"vibrant natural color, extreme detail, shallow depth of field, fresh morning quality",
      lighting:"backlight through the petal creating translucent glow, rim light on dewdrops, soft diffusion from overcast sky",
      medium:"photograph",
      photo:"macro photography, 100mm macro lens, extreme close-up, natural light, early morning",
      art_style:"", style_color_palette:["#2ECC71","#27AE60","#F1C40F","#E74C3C","#1ABC9C"],
      regions:[{x:0.05,y:0.05,w:0.9,h:0.65,type:"obj",desc:"A pink flower petal filling most of the frame with visible cellular texture, crystal-clear dewdrops of varying sizes catching and refracting the backlight, one large drop in the center showing an inverted image inside",palette:[]}] },
    { label:"街头纪实", w:1360, h:768, style:"photo",
      high_level_description:"An authentic street documentary photograph capturing bustling pedestrians in a busy urban intersection, natural light, candid moment",
      background:"A busy city intersection with mixed commercial architecture, street-level storefronts with awnings, traffic signals, and a grey overcast sky above",
      aesthetics:"documentary style, natural muted colors, candid feel, raw authenticity",
      lighting:"natural light, overcast diffusion, soft even ambient light, no directional shadows",
      medium:"photograph",
      photo:"street photography, 35mm wide angle, candid moment, available light",
      art_style:"", style_color_palette:["#2C3E50","#7F8C8D","#95A5A6","#BDC3C7","#34495E"],
      regions:[{x:0.15,y:0.2,w:0.7,h:0.45,type:"obj",desc:"A crowd of pedestrians crossing a street intersection in various directions, mixed ages and styles of clothing, one person looking directly at the camera, expressions natural and unposed",palette:[]}] },
    { label:"油画古典肖像", w:1024, h:1536, style:"art_style",
      high_level_description:"A classical oil painting portrait of a noble figure in elaborate period clothing against a dark drapery background with masterful chiaroscuro",
      background:"A dark gradient background with heavy velvet drapery in deep burgundy, rich shadow gradient receding into darkness behind the sitter",
      aesthetics:"baroque, dramatic chiaroscuro, rich warm tones, impasto texture, ornate detail",
      lighting:"Rembrandt lighting, single strong light source from upper left, deep shadow on the right side, warm skin illumination",
      medium:"oil painting",
      photo:"", art_style:"baroque, dramatic chiaroscuro, rich ornamentation, classical portrait tradition, visible brushwork",
      style_color_palette:["#8B4513","#DAA520","#2C1810","#F5DEB3","#CD853F"],
      regions:[{x:0.15,y:0.05,w:0.7,h:0.6,type:"obj",desc:"A nobleman with a curled wig and fair skin, wearing an embroidered velvet coat in deep blue with gold trim, a white lace cravat at the neck, a composed authoritative expression with a slight hint of a smile",palette:[]},{x:0,y:0,w:0.2,h:0.8,type:"obj",desc:"Heavy burgundy velvet drapery on the left side with deep folds catching the light at the crest of each fold",palette:[]},{x:0.8,y:0,w:0.2,h:0.8,type:"obj",desc:"Dark velvet drapery on the right falling into near-complete shadow, only the top fold edges catching the light",palette:[]}] },
    { label:"黄金时段风景", w:1360, h:768, style:"photo",
      high_level_description:"A magnificent golden hour landscape with layered mountain silhouettes, dramatic cloud formations, and sun rays spreading across the scene",
      background:"A wide horizon with multiple layers of mountain ridges receding into the distance, a sky filled with textured clouds transitioning from deep orange to purple, and a golden sun low on the horizon",
      aesthetics:"vibrant, high contrast, golden tones, majestic natural beauty",
      lighting:"golden hour, low-angle sunlight, long shadows stretching across the foreground, warm directional rim light on clouds and mountain edges",
      medium:"photograph",
      photo:"landscape photography, wide angle lens, graduated neutral density filter, generous depth of field",
      art_style:"", style_color_palette:["#FF8C00","#FF6347","#FFD700","#4A0080","#191970"],
      regions:[{x:0.25,y:0.1,w:0.5,h:0.15,type:"obj",desc:"The golden sun near the horizon partially obscured by a thin layer of clouds radiating visible sunbeams in all directions",palette:[]},{x:0,y:0.3,w:1,h:0.35,type:"obj",desc:"Three distinct layers of mountain ridges silhouetted against the sunset sky, each layer a deeper purple than the one before it",palette:[]},{x:0,y:0.65,w:1,h:0.35,type:"obj",desc:"A grassy meadow in the foreground with wild grass catching the golden light, long shadows stretching toward the viewer",palette:[]}] },
    { label:"微缩模型场景", w:1360, h:768, style:"photo",
      high_level_description:"A tilt-shift miniature effect photograph making a real city intersection look like a tiny scale model with selective focus creating an extremely shallow depth of field",
      background:"An urban intersection viewed from an elevated angle with buildings arranged like a model train set, bright daylight, and a clear blue sky",
      aesthetics:"vibrant, saturated, high contrast, sharp central detail with graduated blur, toy-like scale",
      lighting:"direct sunlight, bright and even, clear blue sky, crisp shadows with defined edges",
      medium:"photograph",
      photo:"tilt-shift photography, selective focus plane, miniature scene effect, bird's eye composition",
      art_style:"", style_color_palette:["#87CEEB","#98FB98","#FFB6C1","#DDA0DD","#F0E68C"],
      regions:[{x:0.05,y:0.2,w:0.9,h:0.5,type:"obj",desc:"A city intersection with miniature-looking cars in red, blue, and yellow, tiny pedestrian figures crossing crosswalks, and small-scale buildings with colorful facades, all rendered with extreme sharpness in the center fading to blur at the edges",palette:[]}] },
    { label:"古装全身人像", w:768, h:1024, style:"photo",
      high_level_description:"A full-body portrait in traditional Chinese Hanfu, the flowing robes elegant and graceful, set in a classical courtyard garden with morning mist",
      background:"A traditional Chinese courtyard with a red-lacquered wooden wall, grey tile roof eaves, and a plum blossom branch extending from the left, soft morning mist hanging in the air",
      aesthetics:"classical Eastern elegance, soft muted tones, refined and graceful, natural light",
      lighting:"natural soft light, diffused morning skylight, even gentle illumination across the figure and courtyard",
      medium:"photograph",
      photo:"portrait photography, 85mm lens, full-body framing, soft natural light, classical composition",
      art_style:"", style_color_palette:["#C0392B","#F5DEB3","#8B4513","#2C3E50","#D4A574"],
      regions:[{x:0.05,y:0.05,w:0.9,h:0.1,type:"obj",desc:"A traditional grey tile roof eaves with carved wooden brackets and a plum blossom branch with pink flowers extending into the frame",palette:[]},{x:0.1,y:0.1,w:0.8,h:0.7,type:"obj",desc:"A woman in full-length flowing Hanfu in pale celadon green and cream, with wide silk sleeves and a layered skirt, her hair styled in a classical updo with a jade hairpin, hands clasped gracefully at the waist, a serene gentle expression",palette:[]},{x:0,y:0.8,w:1,h:0.2,type:"obj",desc:"A stone-paved courtyard ground with grey flagstones, a few fallen pink plum blossom petals scattered near the hem of the robe",palette:[]}] },
    { label:"现代全身人像", w:768, h:1024, style:"photo",
      high_level_description:"A modern full-body fashion portrait with a model in contemporary streetwear, a confident pose, set against an urban backdrop with late afternoon light",
      background:"A clean urban street with a light grey wall, a minimalist architectural backdrop, and a soft blue sky with wispy clouds",
      aesthetics:"clean modern, sharp contrast, editorial clarity, fashion-forward",
      lighting:"side light with a soft fill from the opposite side, defined facial contours, bright natural daylight",
      medium:"photograph",
      photo:"fashion photography, 50mm lens, full-body styling, natural light with reflector fill",
      art_style:"", style_color_palette:["#2C3E50","#E74C3C","#ECF0F1","#F39C12","#34495E"],
      regions:[{x:0.08,y:0.05,w:0.84,h:0.75,type:"obj",desc:"A young man in an oversized cream knit sweater, loose beige trousers, and white sneakers, one hand in a pocket, the other holding a phone, a relaxed confident stance, looking slightly off-camera with a neutral expression",palette:[]}] },
    { label:"俯瞰视角大场景", w:1360, h:768, style:"photo",
      high_level_description:"A breathtaking aerial panoramic view showing a river winding through a dramatic valley with layered mountain ranges under golden hour light",
      background:"A vast landscape seen from altitude with a meandering river cutting through a valley, multiple mountain ranges receding to the horizon, cloud shadows creating areas of light and dark on the terrain",
      aesthetics:"majestic and vast, high contrast, rich detail across the scene, saturated natural colors",
      lighting:"golden hour aerial light, low-angle illumination emphasizing terrain texture, long shadows from mountain ridges",
      medium:"photograph",
      photo:"aerial drone photography, wide angle lens, top-down perspective, panoramic landscape",
      art_style:"", style_color_palette:["#2ECC71","#3498DB","#F39C12","#8E44AD","#1ABC9C"],
      regions:[{x:0,y:0.35,w:1,h:0.35,type:"obj",desc:"A wide meandering river with a blue-green color snaking through the valley floor with visible sandbars and oxbow bends",palette:[]},{x:0,y:0.7,w:1,h:0.3,type:"obj",desc:"A dense pine forest covering the lower valley slopes with patches of exposed rock and small clearings visible through the canopy",palette:[]}] },
    { label:"厚涂游戏原画", w:1360, h:768, style:"art_style",
      high_level_description:"An impasto game concept art piece with a heroic character standing on a battlefield under a dramatic stormy sky, with bold layered brushwork",
      background:"A fantasy battlefield with a dark stormy sky, smoking ruins in the distance, a rugged rocky terrain, and dramatic atmospheric perspective with dust and mist",
      aesthetics:"impasto texture, bold visible brushwork, high saturation, cinematic epic composition",
      lighting:"dramatic volumetric lighting, god rays breaking through storm clouds, rim light on the central figure, floating dust particles catching the light",
      medium:"digital painting",
      photo:"", art_style:"impasto technique, game concept art, thick layered strokes, painterly epic composition",
      style_color_palette:["#8B0000","#DAA520","#2C1810","#4A0080","#FF8C00"],
      regions:[{x:0,y:0,w:1,h:0.25,type:"obj",desc:"A stormy sky with dark purple-blue clouds parted in the center revealing golden light, god rays descending diagonally through the scene",palette:[]},{x:0.25,y:0.15,w:0.5,h:0.6,type:"obj",desc:"A warrior figure in dark armor with a red cape billowing in the wind, holding a large sword point-down, standing on a rocky outcrop with a heroic silhouette against the light",palette:[]},{x:0,y:0.7,w:1,h:0.3,type:"obj",desc:"A rocky terrain with broken stone, scattered weapons, and smoke rising from small fires, rendered with thick palette-knife-style brush strokes",palette:[]}] },
    { label:"3D超写实修仙", w:1024, h:1024, style:"photo",
      high_level_description:"A hyperrealistic 3D rendered cultivation fantasy scene with a figure ascending through golden clouds toward a celestial light, floating mountain peaks and mystical energy",
      background:"A sea of golden-tinted clouds with floating mountain peaks at various altitudes, a brilliant celestial light source above, and streams of luminous particles flowing through the scene",
      aesthetics:"hyperrealistic, surreal and mystical, luminous, high dynamic range, ethereal atmosphere",
      lighting:"volumetric golden light from above piercing through cloud layers, divine atmospheric glow, rim light on all foreground elements",
      medium:"3d_render",
      photo:"", art_style:"hyperrealism combined with fantasy surrealism, extreme detail, smooth polished surface finish",
      style_color_palette:["#FFD700","#FFFFFF","#1A0A2E","#00BFFF","#FF4500"],
      regions:[{x:0,y:0,w:1,h:0.3,type:"obj",desc:"A brilliant golden light source radiating from the upper center with visible volumetric rays spreading outward through layered clouds",palette:[]},{x:0.2,y:0.2,w:0.6,h:0.5,type:"obj",desc:"A floating rocky mountain peak with ancient pine trees and a small traditional pavilion on top, a figure in flowing white robes standing on the edge with arms raised toward the light, surrounded by glowing particles",palette:[]},{x:0,y:0.65,w:1,h:0.35,type:"obj",desc:"A lower sea of golden and pink clouds with smaller floating stone fragments, a waterfall cascading off the side of the main island into the void below",palette:[]}] },
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

// ──────────────────────────────────────────────
//  restoreWorkflowData — handles both flat (old) and
//  nested (Ideogram 4) formats from saved prompt_data
// ──────────────────────────────────────────────
function restoreWorkflowData(node, raw) {
    const s = node._pb;
    let d;
    try { d = JSON.parse(raw); } catch(e) { return; }
    if (!d) return;

    // Detect nested format (has composition_deconstruction)
    if (d.compositional_deconstruction) {
        s.high_level_description = d.high_level_description || "";
        const sd = d.style_description || {};
        s.aesthetics = sd.aesthetics || "";
        s.lighting = sd.lighting || "";
        s.medium = sd.medium || "";
        s.photo_style = sd.photo || "";
        s.art_style = sd.art_style || "";
        s.style = sd.photo ? "photo" : (sd.art_style ? "art_style" : "none");
        s.style_color_palette = sd.color_palette || [];

        const cd = d.compositional_deconstruction || {};
        s.background = cd.background || "";

        const elements = cd.elements || [];
        s.regions = elements.map(el => {
            const r = {
                type: el.type || "obj",
                text: el.text || "",
                desc: el.desc || "",
                palette: el.color_palette || [],
                x: 0, y: 0, w: 1, h: 0
            };
            if (el.bbox && el.bbox.length === 4) {
                r.x = Math.min(el.bbox[1] / 1000, 1);
                r.y = Math.min(el.bbox[0] / 1000, 1);
                r.w = Math.min((el.bbox[3] - el.bbox[1]) / 1000, 1 - r.x);
                r.h = Math.min((el.bbox[2] - el.bbox[0]) / 1000, 1 - r.y);
            }
            return r;
        });
    } else {
        // Flat format — direct assign
        Object.assign(s, d);
        if (!s.regions) s.regions = [];
    }
    if (s.activeRegion == null) s.activeRegion = -1;
}

function sync() {
    const node = currentNode; if (!node) return;
    syncPreview(node); saveState(node);
    if (app?.graph) app.graph.setDirtyCanvas(true, true);
}

// ──────────────────────────────────────────────
//  saveState — transforms flat pb structure into
//  Ideogram 4 compliant JSON caption schema
// ──────────────────────────────────────────────
function saveState(node) {
    const w = node.widgets?.find((w) => w.name === "prompt_data");
    if (!w) return;
    const s = node._pb;

    const caption = {};

    if (s.high_level_description) {
        caption.high_level_description = s.high_level_description;
    }

    // style_description — only emit when it has meaningful content
    const sd = {};
    let hasSD = false;
    if (s.aesthetics) { sd.aesthetics = s.aesthetics; hasSD = true; }
    if (s.lighting) { sd.lighting = s.lighting; hasSD = true; }
    if (s.medium) { sd.medium = s.medium; hasSD = true; }
    if (s.style === "photo" && s.photo_style) {
        sd.photo = s.photo_style; hasSD = true;
    } else if (s.style === "art_style" && s.art_style) {
        sd.art_style = s.art_style; hasSD = true;
    }
    if (s.style_color_palette && s.style_color_palette.length > 0) {
        sd.color_palette = s.style_color_palette.map(c => {
            if (!c.startsWith("#")) c = "#" + c;
            return c.toUpperCase();
        });
        hasSD = true;
    }
    if (hasSD) caption.style_description = sd;

    // compositional_deconstruction — always emit when data exists
    const cd = {};
    let hasCD = false;
    if (s.background) { cd.background = s.background; hasCD = true; }

    const elements = [];
    for (const region of (s.regions || [])) {
        const el = { type: region.type || "obj" };

        if (region.x !== undefined && region.y !== undefined &&
            region.w !== undefined && region.h !== undefined &&
            region.w > 0 && region.h > 0) {
            const x1 = Math.round(region.x * 1000);
            const y1 = Math.round(region.y * 1000);
            const x2 = Math.round((region.x + region.w) * 1000);
            const y2 = Math.round((region.y + region.h) * 1000);
            if (x2 > 0 && y2 > 0) {
                el.bbox = [Math.min(y1, 1000), Math.min(x1, 1000), Math.min(y2, 1000), Math.min(x2, 1000)];
            }
        }

        if (region.type === "text" && region.text) {
            el.text = region.text;
        }
        if (region.desc) {
            el.desc = region.desc;
        }
        if (region.palette && region.palette.length > 0) {
            el.color_palette = region.palette.map(c => {
                if (!c.startsWith("#")) c = "#" + c;
                return c.toUpperCase();
            });
        }
        elements.push(el);
    }

    if (elements.length > 0) { cd.elements = elements; hasCD = true; }
    if (hasCD) caption.compositional_deconstruction = cd;

    w.value = JSON.stringify(caption, null, 2);
}

function syncPreview(node) {
    if (!node._pbPV) return;
    const s = node._pb;
    const lines = [];
    if (s.high_level_description) lines.push(`HLD: ${s.high_level_description}`);
    if (s.aesthetics) lines.push(`Aesthetic: ${s.aesthetics}`);
    if (s.lighting) lines.push(`Lighting: ${s.lighting}`);
    if (s.medium) lines.push(`Medium: ${s.medium}`);
    if (s.style === "photo" && s.photo_style) lines.push(`Photo: ${s.photo_style}`);
    else if (s.style === "art_style" && s.art_style) lines.push(`Art: ${s.art_style}`);
    if (s.background) lines.push(`BG: ${s.background}`);
    if (s.regions.length) {
        lines.push(`Elements: ${s.regions.length}`);
        for (let i = 0; i < s.regions.length; i++) {
            const rg = s.regions[i];
            let t = `  [${String(i+1).padStart(2,"0")}] ${rg.type}`;
            if (rg.x !== undefined) t += ` [${Math.round(rg.x*1000)},${Math.round(rg.y*1000)},${Math.round((rg.x+rg.w)*1000)},${Math.round((rg.y+rg.h)*1000)}]`;
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
            // desc text clipped
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

    try{
        node._pbVisObs=new IntersectionObserver((entries)=>{
            if(entries.some(en=>en.isIntersecting))fitCanvas();
        });
        node._pbVisObs.observe(cvWrap);
    }catch(e){}
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
        draw(); syncPreview(node);
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
    descInp.placeholder = "元素描述(英文)";
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
    const swapBtn=document.createElement("button");swapBtn.className="cj-pb-btn";swapBtn.textContent="\u21C4";swapBtn.title="交换宽高";
    swapBtn.addEventListener("click",()=>{const tmp=s.width;s.width=s.height;s.height=tmp;wInp.value=s.width;hInp.value=s.height;node._cvFit?.();sync();});
    const hInp=document.createElement("input");hInp.className="cj-pb-num";hInp.type="number";hInp.min="64";hInp.max="16384";hInp.step="16";hInp.value=s.height;
    hInp.addEventListener("input",()=>{s.height=parseInt(hInp.value)||1024;node._cvFit?.();sync();});
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
    photoR.appendChild(photoI);photoR.appendChild(mkDropdown(PRESETS.photo,v=>{photoI.value=v;s.photo_style=v;sync();}));
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
        {l:"描述:",t:"整体画面概述（英文）",ml:false,p:PRESETS.high_level_description,k:"high_level_description"},
        {l:"背景:",t:"场景背景描述（英文）",ml:false,p:PRESETS.background,k:"background"},
        {l:"美学:",t:"美学风格（英文，禁止: film grain/DOF/bokeh等渲染术语）",ml:false,p:PRESETS.aesthetics,k:"aesthetics"},
        {l:"光影:",t:"光照（英文，禁止: warm作为调色形容词）",ml:false,p:PRESETS.lighting,k:"lighting"},
        {l:"媒介:",t:"媒介（仅媒介名称，如photograph/3d_render/digital painting）",ml:false,p:PRESETS.medium,k:"medium"},
    ];
    const fEls={};
    for(const f of fields){
        const r=mkParamField(f.l,f.t,f.ml,f.p,()=>s[f.k]||"",v=>{s[f.k]=v;});
        fEls[f.k]=r;wrap.appendChild(r.row);
    }

    // style color palette (max 16 per spec)
    const scpR=mkRow("色板:","风格色板（最多16色）");
    const scpSwatches=document.createElement("div");scpSwatches.style.cssText="display:flex;gap:3px;flex:1;flex-wrap:wrap;";
    function buildScpSwatches(){
        scpSwatches.innerHTML="";
        (s.style_color_palette||[]).forEach((c,i)=>{
            const sw=document.createElement("div");sw.className="cj-pb-sw";sw.style.cssText=`background:${c};cursor:pointer;width:18px;height:18px;border-radius:3px;`;
            sw.title=`${c} — 点击移除`;
            sw.addEventListener("click",()=>{s.style_color_palette.splice(i,1);buildScpSwatches();sync();});
            scpSwatches.appendChild(sw);
        });
        if((s.style_color_palette||[]).length<16){
            const addB=document.createElement("div");addB.className="cj-pb-sw";addB.style.cssText="background:#333;cursor:pointer;width:18px;height:18px;border-radius:3px;display:flex;align-items:center;justify-content:center;color:#888;font-size:12px;";addB.textContent="+";addB.title="添加颜色";
            const ci=document.createElement("input");ci.type="color";ci.value="#ffffff";ci.style.cssText="position:absolute;opacity:0;width:0;height:0;pointer-events:none;";
            addB.appendChild(ci);
            addB.style.position="relative";
            addB.addEventListener("click",()=>ci.click());
            ci.addEventListener("input",()=>{if(!s.style_color_palette)s.style_color_palette=[];const h=ci.value.toUpperCase();if(!s.style_color_palette.includes(h)){s.style_color_palette.push(h);}buildScpSwatches();sync();});
            scpSwatches.appendChild(addB);
        }
    }
    buildScpSwatches();
    scpR.appendChild(scpSwatches);wrap.appendChild(scpR);

    // region edit panel
    const regionPanel = document.createElement("div"); regionPanel.className = "cj-pb-panel";
    node._pbPanel = regionPanel;
    wrap.appendChild(regionPanel);

    // canvas
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
            node._pb={width:1360,height:768,style:"none",high_level_description:"",background:"",aesthetics:"",lighting:"",medium:"",photo_style:"",art_style:"",style_color_palette:[],regions:[],activeRegion:-1};
            const pdW=node.widgets?.find(w=>w.name==="prompt_data");
            if(pdW){pdW.hidden=true;pdW.computeSize=()=>[0,-4];if(pdW.value){try{restoreWorkflowData(node,pdW.value);}catch(e){}}}
            buildUI(node);
            node.setSize([Math.max(440,node.size[0]),Math.max(500,node.size[1])]);
            chainCallback(node,"onRemoved",()=>{
                if(node._pbVisObs){node._pbVisObs.disconnect();node._pbVisObs=null;}
                if(node._pbResizeObs){node._pbResizeObs.disconnect();node._pbResizeObs=null;}
            });
        });
    }
});

console.log("CJ-Nodes PromptBuilder v2 — Ideogram 4 compliant");
