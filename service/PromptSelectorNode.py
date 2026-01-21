import random
import os
import re

class PromptSelectorNode:
    def __init__(self):
        super().__init__()
        self.prompt = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "提示词": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入提示词...",
                    "rows": 5
                })
            },
            "optional": {}
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出提示词",)
    FUNCTION = "process_prompt"
    CATEGORY = "luy/提示词"

    def process_prompt(self, 提示词):
        self.prompt = 提示词
        return (self.prompt,)


class PromptGenerator:
    def __init__(self):
        pass

    @classmethod
    def _get_options_folder(cls):
        """获取选项文件夹路径"""
        return os.path.join(os.path.dirname(__file__), "prompt_options")

    @classmethod
    def _scan_options_files(cls):
        """扫描选项文件夹中的所有txt文件，并按文件名的数字序号从小到大排序"""
        options_folder = cls._get_options_folder()
        if not os.path.exists(options_folder):
            os.makedirs(options_folder)
            return []  # 改为返回列表，保留排序顺序

        numbered_files = []
        for filename in os.listdir(options_folder):
            if filename.endswith(".txt"):
                # 提取文件名开头的数字序号（适配“1-适用场景.txt”格式）
                match = re.match(r'^(\d+)-', filename)
                if match:
                    file_number = int(match.group(1))
                    # 提取参数名（去掉序号和后缀）
                    param_name = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
                    numbered_files.append((file_number, param_name, filename))
                else:
                    # 无序号文件排最后
                    numbered_files.append((9999, os.path.splitext(filename)[0], filename))

        # 严格按数字序号升序排序
        numbered_files.sort(key=lambda x: x[0])
        return numbered_files  # 返回排序后的列表（包含序号、参数名、文件名）

    @classmethod
    def _load_options(cls, filename):
        """加载单个文件的选项"""
        options = ["忽略 (Ignore)"]
        options.append("随机 (Random)")
        try:
            file_path = os.path.join(cls._get_options_folder(), filename)
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        options.append(stripped_line)
        except FileNotFoundError:
            print(f"警告：未找到文件 {filename}")
        return options

    @classmethod
    def INPUT_TYPES(cls):
        """动态生成输入类型，严格按文件名序号排序"""
        required_inputs = {}
        # 获取排序后的文件列表
        sorted_files = cls._scan_options_files()
        # 按排序顺序生成参数
        for _, param_name, filename in sorted_files:
            required_inputs[param_name] = (cls._load_options(filename),)

        # 添加布尔值参数
        required_inputs["启用选择节点"] = ("BOOLEAN", {"default": True})

        return {
            "required": required_inputs,
            "optional": {
                "txt_str": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入自定义提示词...会串接到前面",
                    "rows": 5
                }),  # lora关键词
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True, "tooltip": "The random seed used for creating the noise."}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("中文标签", "英文标签", "中英混合标签", "包含主题内容")
    FUNCTION = "generate_text"
    CATEGORY = "luy/提示词"

    def random_choice(self, selected_option, options):
        if selected_option == "随机 (Random)":
            actual_options = [opt for opt in options if "随机" not in opt and "忽略" not in opt]
            return random.choice(actual_options) if actual_options else selected_option
        return selected_option

    def _extract_parts(self, text):
        """提取中文部分和英文部分"""
        if not text or "忽略" in text or "随机" in text:
            return "", ""

        if " (" in text and text.endswith(")"):
            parts = text.split(" (")
            chinese_part = parts[0].strip()
            english_part = parts[1][:-1].strip()  # 去掉最后的)
            return chinese_part, english_part
        else:
            return text.strip(), ""

    def generate_text(self, txt_str, 启用选择节点=True,** kwargs):
        """动态处理所有参数（严格按序号顺序）"""
        # 获取排序后的字段列表
        sorted_files = self._scan_options_files()
        fields = [param_name for _, param_name, _ in sorted_files]

        # 如果未启用选择节点，直接返回txt_str内容
        if not 启用选择节点:
            return (txt_str.strip(), txt_str.strip(), txt_str.strip(), "")

        selections = {}
        for field in fields:
            value = kwargs.get(field, "忽略 (Ignore)")
            # 获取该字段对应的选项列表
            field_options = self.INPUT_TYPES()['required'][field][0]
            selections[field] = self.random_choice(value, field_options)

        # 按序号顺序收集中文、英文等关键词
        chinese_keywords = []
        english_keywords = []
        mix_keywords = []
        dropdown_selections = []

        for field in fields:
            value = selections[field]
            if "忽略" not in value:
                chinese_part, english_part = self._extract_parts(value)
                if chinese_part:
                    dropdown_selections.append(f"{field}（{chinese_part}）")
                if chinese_part:
                    chinese_keywords.append(chinese_part)
                if english_part:
                    english_keywords.append(english_part)
                if chinese_part and english_part:
                    mix_keywords.append(f"{chinese_part} ({english_part})")
                elif chinese_part:
                    mix_keywords.append(chinese_part)
                elif english_part:
                    mix_keywords.append(english_part)

        # 处理基础提示词并拼接结果
        txt_str_clean = txt_str.strip().rstrip(",").lstrip(",")
        def join_keywords(base, keywords):
            if not keywords:
                return base
            if not base:
                return ",".join(keywords)
            return f"{base},{','.join(keywords)}"

        chinese_result = join_keywords(txt_str_clean, chinese_keywords)
        english_result = join_keywords(txt_str_clean, english_keywords)
        mix_result = join_keywords(txt_str_clean, mix_keywords)
        dropdown_result = "、".join(dropdown_selections)

        return (chinese_result, english_result, mix_result, dropdown_result)



class Wan22PromptSelector:
    CATEGORY = "luy/提示词"
    FUNCTION = "generate_prompt"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("提示词",)

    # 动态控制模块选项（空选项及非空选项均基于文档内容）
    运动场景选项 = [
        "——",  # 空选项
        "跑步", "走路", "奔跑", "后空翻", "前空翻",
        "倒退走路", "向上立定跳跃", "飞行", "自由落体", "跑酷动作"
    ]

    人物情绪选项 = [
        "——",  # 空选项
        "愤怒", "恐惧", "高兴", "悲伤", "惊讶",
        "忧虑", "困惑", "欣慰", "狂喜", "绝望",
        "平静", "期待", "羞涩", "厌恶", "自豪"
    ]

    运镜方式选项 = [
        "——",  # 空选项
        "镜头推进", "镜头拉远", "镜头向左平移", "镜头向右平移", "镜头上摇",
        "手持镜头", "跟随镜头", "环绕运镜", "镜头旋转", "俯拍",
        "仰拍", "平视镜头", "延时摄影", "慢动作摄影", "快动作摄影","推拉运镜，慢速推进，摄像机缓慢向前靠近主体",
        "推拉运镜，慢速拉出 - 摄像机缓慢向后远离主体",
        "快速推进 - 摄像机急速向前逼近主体面部，营造紧迫感",
        "眩晕效果（滑动变焦）- 摄像机后移同时变焦放大，背景扩展",
        "无限尺度连续镜头，极致微距变焦，从面部到眼部微观视角的变焦过渡",
        "无限尺度连续镜头，宇宙级超速变焦，从太空到街道的快速变焦转换",
        "角色定位构图，过肩镜头 - 摄像机置于角色 A 肩后框取角色 B",
        "角色定位构图，鱼眼 / 窥视镜镜头，极端广角畸变，圆形画框",
        "障碍物与环境互动，遮蔽物后揭示（擦拭式运动）, 摄像机横向滑过柱体展现街道景象",
        "障碍物与环境互动，穿行镜头（飞越空隙）, 摄像机穿过窗户进入室内",
        "焦点与镜头操控，模糊转清晰（淡入）, 从完全失焦开始缓慢聚焦至清晰",
        "焦点与镜头操控，焦点转移（前景至背景）",
        "三脚架运镜，上摇镜头",
        "三脚架运镜，下摇镜头",
        "滑轨横向运镜，左横移，摄像机沿轨道向左横向移动",
        "滑轨横向运镜，右横移，摄像机沿轨道向右横向移动",
        "环绕运镜，180 度环绕，摄像机绕主体半周运动",
        "环绕运镜，快速 360 度旋转，摄像机绕主体急速旋转一周",
        "环绕运镜，慢速电影弧线运镜，摄像机沿宽曲线运动展现侧面轮廓",
        "垂直运动（升降台）, 台座下降，摄像机垂直下降",
        "垂直运动（升降台）, 台座上升，摄像机从腰部垂直上升至眼平高度",
        "垂直运动（升降台）, 吊臂上升（俯角揭示）, 摄像机升向高空",
        "垂直运动（升降台）, 吊臂下降（着陆）, 摄像机缓慢下降至主体",
        "光学镜头特效，平滑光学变焦推进，镜头放大主体，摄像机保持静止",
        "光学镜头特效，平滑光学变焦拉出，镜头拓宽视野，背景虚化",
        "光学镜头特效，骤拉变焦（冲击变焦）, 急速变焦直推眼部",
        "无人机 / 航拍视角，无人机飞越，高空向前飞越景观",
        "无人机 / 航拍视角，史诗级无人机揭示，上升并俯仰展现全景",
        "无人机 / 航拍视角，大规模无人机环绕，环绕岛屿的宏大全景环绕",
        "无人机 / 航拍视角，垂直俯拍（上帝视角）, 镜头垂直向下，缓慢旋转",
        "无人机 / 航拍视角，FPV 无人机俯冲（瀑布俯冲）, 沿瀑布俯冲的激进俯冲运动",
        "风格化动态运镜，手持纪实风格，手持摄像机抖动，自然运动，纪实风格",
        "风格化动态运镜，快速摇镜，摄像机迅猛横向摇动，产生极端动态模糊",
        "风格化动态运镜，荷兰角（滚转）, 摄像机沿 Z 轴倾斜",
        "主体追踪（引领与跟随）, 引领镜头（反向追踪）, 摄像机后移匹配主体速度",
        "主体追踪（引领与跟随）, 跟随镜头（正向追踪）, 摄像机跟随主体同步移动",
        "主体追踪（引领与跟随）, 平行侧跟，摄像机与主体平行横向移动",
        "主体追踪（引领与跟随）, 第一人称行走，摄像机模拟步行前进的起伏运动",
        "时间与速度操控，超延时摄影（移动延时）, 摄像机快速前进，时间加速，光影拖尾",
        "时间与速度操控，子弹时间（凝固瞬间）, 时间冻结，超慢动作，摄像机右向环绕",
        "极端定向与透视，桶滚旋转（漩涡盗梦镜头）, 摄像机前进时顺时针 360 度旋转，制造眩晕感",
        "极端定向与透视，虫眼追踪（地面视角）低角度追踪，摄像机沿地面移动仰视主体"
    ]

    # 影视级美学控制模块选项（基于文档影视级美学控制章节）
    光源类型选项 = [
        "——",  # 空选项
        "日光", "人工光", "月光", "实用光", "火光",
        "荧光", "阴天光", "混合光", "晴天光"
    ]

    光线类型选项 = [
        "——",  # 空选项
        "柔光", "硬光", "顶光", "背光", "底光", "边缘光", "侧光",
        "低对比度光", "高对比度光", "剪影光", "黎明光", "黄昏光", "日落光"
    ]

    镜头类型选项 = [
        "——",  # 空选项
        "干净的单人镜头", "双人镜头", "三人镜头", "群像镜头", "定场镜头"
    ]

    焦距选项 = [
        "——",  # 空选项
        "中焦距", "广角", "长焦", "望远", "超广角-鱼眼"
    ]

    色调选项 = [
        "——",  # 空选项
        "暖色调", "冷色调", "高饱和度", "低饱和度"
    ]

    # 风格化模块选项（基于文档风格化章节）
    视觉风格选项 = [
        "——",  # 空选项
        "日系动漫","人像写实","赛博朋克", "勾线插画", "废土风格", "毛毡风格",
        "3D卡通", "像素风格", "木偶动画", "水彩画"
    ]

    特效镜头选项 = [
        "——",  # 空选项
        "移轴摄影", "延时拍摄"
    ]

    # 场景类型选项（基于文档场景定义）
    场景类型选项 = [
        "——",  # 空选项
        "自然场景（田野/森林/山脉）", "城市场景（街道/室内/建筑）",
        "虚构场景（异世界/太空/梦境）"
    ]

    # 节点输入参数定义
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "场景类型": (s.场景类型选项, {"default": "——"}),
                "运动场景": (s.运动场景选项, {"default": "——"}),
                "人物情绪": (s.人物情绪选项, {"default": "——"}),
                "运镜方式": (s.运镜方式选项, {"default": "——"}),
                "光源类型": (s.光源类型选项, {"default": "——"}),
                "光线类型": (s.光线类型选项, {"default": "——"}),
                "镜头类型": (s.镜头类型选项, {"default": "——"}),
                "焦距": (s.焦距选项, {"default": "——"}),
                "色调": (s.色调选项, {"default": "——"}),
                "视觉风格": (s.视觉风格选项, {"default": "——"}),
                "特效镜头": (s.特效镜头选项, {"default": "——"}),
            }
        }

    # 提示词生成逻辑（遵循文档提示词公式）
    def generate_prompt(self, 场景类型, 运动场景, 人物情绪, 运镜方式,
                       光源类型, 光线类型, 镜头类型, 焦距, 色调, 视觉风格, 特效镜头):
        # 筛选非空选项
        elements = [
            场景类型 if 场景类型 != "——" else "",
            f"主体{运动场景}" if 运动场景 != "——" else "",
            f"呈现{人物情绪}" if 人物情绪 != "——" else "",
            运镜方式 if 运镜方式 != "——" else "",
            光源类型 if 光源类型 != "——" else "",
            光线类型 if 光线类型 != "——" else "",
            镜头类型 if 镜头类型 != "——" else "",
            焦距 if 焦距 != "——" else "",
            色调 if 色调 != "——" else "",
            f"{视觉风格}风格" if 视觉风格 != "——" else "",
            特效镜头 if 特效镜头 != "——" else ""
        ]
        # 去除空字符串并拼接
        prompt_parts = [e for e in elements if e]
        prompt = "，".join(prompt_parts) if prompt_parts else ""
        return (prompt,)
