import random
import os
import re
import time

# 全局缓存：存储当前有效的路径和对应的下拉框配置
NODE_INPUT_CACHE = {
    "last_path": "",
    "input_spec": {}
}

class EditPromptNode:
    def __init__(self):
        # 初始化随机种子，避免伪随机固定
        random.seed(time.time() + os.getpid())

    @classmethod
    def _get_options_folder(cls, custom_path):
        """获取选项文件夹路径（使用自定义入参路径）"""
        if not os.path.isabs(custom_path):
            return os.path.join(os.path.dirname(__file__), custom_path)
        return custom_path

    @classmethod
    def _scan_options_files(cls, custom_path):
        """扫描指定路径下的所有txt文件，按数字序号升序排序"""
        options_folder = cls._get_options_folder(custom_path)
        if not os.path.exists(options_folder):
            os.makedirs(options_folder)
            print(f"提示：自定义路径 {options_folder} 不存在，已自动创建")
            return []

        numbered_files = []
        for filename in os.listdir(options_folder):
            if filename.endswith(".txt"):
                match = re.match(r'^(\d+)-', filename)
                if match:
                    file_number = int(match.group(1))
                    param_name = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
                    numbered_files.append((file_number, param_name, filename))
                else:
                    numbered_files.append((9999, os.path.splitext(filename)[0], filename))

        numbered_files.sort(key=lambda x: x[0])
        return numbered_files

    @classmethod
    def _split_display_and_value(cls, line):
        """兼容双格式拆分"""
        if "##" in line:
            parts = line.split("##", 1)
            display_text = parts[0].strip()
            actual_value = parts[1].strip()
            return display_text, actual_value, True
        else:
            full_text = line.strip()
            return full_text, full_text, False

    @classmethod
    def _load_options(cls, custom_path, filename):
        """加载指定路径下文件的下拉框选项"""
        options_folder = cls._get_options_folder(custom_path)
        options = ["忽略 (Ignore)", "随机 (Random)"]
        line_full_info = []
        try:
            file_path = os.path.join(options_folder, filename)
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        d, a, s = cls._split_display_and_value(stripped_line)
                        options.append(d)
                        line_full_info.append((d, a, s))
        except FileNotFoundError:
            print(f"警告：{options_folder} 路径下未找到文件 {filename}")
        return options, line_full_info

    @classmethod
    def _get_actual_value_and_flag(cls, custom_path, filename, display_text):
        """反向获取指定路径下文件的actual_value和is_has_Sharp"""
        if display_text in ["忽略 (Ignore)", "随机 (Random)"]:
            return display_text, False

        options_folder = cls._get_options_folder(custom_path)
        try:
            file_path = os.path.join(options_folder, filename)
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        d, a, s = cls._split_display_and_value(stripped_line)
                        if d == display_text:
                            return a, s
            return display_text, False
        except FileNotFoundError:
            print(f"警告：{options_folder} 路径下未找到文件 {filename}")
            return display_text, False

    @classmethod
    def _generate_input_spec(cls, custom_path):
        """动态生成输入参数规范（核心：路径变更时重新生成下拉框）"""
        # 基础输入参数（固定）
        required_inputs = {
            "自定义文件路径": ("STRING", {
                "default": custom_path,
                "placeholder": "输入txt文件存放路径，支持相对/绝对路径",
                "tooltip": "例如：ai_prompt/E 或 D:/prompt_files，修改后请刷新节点"
            }),
            "启用选择节点": ("BOOLEAN", {"default": True})
        }

        # 动态生成路径下的txt文件对应的下拉框
        sorted_files = cls._scan_options_files(custom_path)
        for _, param_name, filename in sorted_files:
            options, _ = cls._load_options(custom_path, filename)
            required_inputs[param_name] = (options,)

        return {
            "required": required_inputs,
            "optional": {
                "txt_str": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "请输入自定义提示词...会串接到前面",
                    "rows": 5
                }),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": True, "tooltip": "The random seed used for creating the noise."}),
            }
        }

    @classmethod
    def INPUT_TYPES(cls):
        """初始化输入参数（首次加载）"""
        default_path = "ai_prompt/E"
        NODE_INPUT_CACHE["last_path"] = default_path
        NODE_INPUT_CACHE["input_spec"] = cls._generate_input_spec(default_path)
        return NODE_INPUT_CACHE["input_spec"]

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        """
        ComfyUI核心方法：验证输入时触发，实现下拉框动态刷新
        当自定义路径变更时，重新生成输入参数规范
        """
        current_path = kwargs.get("自定义文件路径", "ai_prompt/E")
        # 路径未变化，直接返回验证通过
        if current_path == NODE_INPUT_CACHE["last_path"]:
            return True

        # 路径变化，重新生成输入参数并更新缓存
        print(f"检测到路径变更：{NODE_INPUT_CACHE['last_path']} → {current_path}，刷新下拉框...")
        new_input_spec = cls._generate_input_spec(current_path)
        NODE_INPUT_CACHE["last_path"] = current_path
        NODE_INPUT_CACHE["input_spec"] = new_input_spec

        # 强制刷新节点输入参数（ComfyUI关键操作）
        cls.INPUT_TYPES = lambda: new_input_spec
        return True

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("中文标签", "英文标签", "中英混合标签", "包含主题内容")
    FUNCTION = "generate_text"
    CATEGORY = "luy/提示词"

    def random_choice(self, custom_path, selected_display, filename):
        """随机选择逻辑（确保选当前下拉框有效数据）"""
        if selected_display != "随机 (Random)":
            a, s = self._get_actual_value_and_flag(custom_path, filename, selected_display)
            return selected_display, a, s

        options, line_full_info = self._load_options(custom_path, filename)
        actual_line_info = [info for info in line_full_info if info[0] not in ["忽略 (Ignore)", "随机 (Random)"]]

        if not actual_line_info:
            error_msg = f"错误：{custom_path} 路径下 {filename} 中无有效随机选项！"
            print(error_msg)
            return "忽略 (Ignore)", "忽略 (Ignore)", False

        random.seed(time.time() * 1000000 + os.getpid() + random.randint(0, 1000000))
        random_info = random.choice(actual_line_info)
        print(f"随机选择结果：{custom_path}/{filename} → {random_info[0]}")
        return random_info[0], random_info[1], random_info[2]

    def _extract_parts(self, actual_value):
        """解析中英文部分"""
        if not actual_value or actual_value in ["忽略 (Ignore)", "随机 (Random)"]:
            return "", ""

        bracket_pattern = r'^(.*?)\s*[（(]\s*(.*?)\s*[）)]$'
        match = re.match(bracket_pattern, actual_value)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        else:
            if re.search(r'[\u4e00-\u9fa5]', actual_value):
                return actual_value.strip(), ""
            else:
                return "", actual_value.strip()

    def generate_text(self, 自定义文件路径, txt_str, 启用选择节点=True,** kwargs):
        """核心执行方法（使用自定义路径）"""
        sorted_files = self._scan_options_files(自定义文件路径)
        fields_with_filename = [(param_name, filename) for _, param_name, filename in sorted_files]

        if not 启用选择节点:
            clean_txt = txt_str.strip()
            return (clean_txt, clean_txt, clean_txt, "")

        field_cache = {}
        for param_name, filename in fields_with_filename:
            selected_display = kwargs.get(param_name, "忽略 (Ignore)")
            final_display, actual_value, is_has_Sharp = self.random_choice(自定义文件路径, selected_display, filename)
            field_cache[param_name] = {
                "final_display": final_display,
                "actual_value": actual_value,
                "is_has_Sharp": is_has_Sharp,
                "filename": filename
            }

        chinese_keywords = []
        english_keywords = []
        mix_keywords = []
        content_with_topic = []
        txt_str_clean = txt_str.strip().rstrip(",").lstrip(",")

        for param_name in [p for p, _ in fields_with_filename]:
            cache = field_cache[param_name]
            actual_value = cache["actual_value"]
            final_display = cache["final_display"]
            is_has_Sharp = cache["is_has_Sharp"]
            filename = cache["filename"]

            if actual_value == "忽略 (Ignore)":
                continue

            chinese_part, english_part = self._extract_parts(actual_value)

            if chinese_part and chinese_part not in chinese_keywords:
                chinese_keywords.append(chinese_part)
            if english_part and english_part not in english_keywords:
                english_keywords.append(english_part)
            if chinese_part and english_part:
                mix_str = f"{chinese_part}（{english_part}）"
                if mix_str not in mix_keywords:
                    mix_keywords.append(mix_str)
            elif chinese_part and chinese_part not in mix_keywords:
                mix_keywords.append(chinese_part)
            elif english_part and english_part not in mix_keywords:
                mix_keywords.append(english_part)

            if is_has_Sharp:
                content_item = f"{final_display}：{actual_value}"
            else:
                pure_filename = re.sub(r'^\d+-', '', os.path.splitext(filename)[0])
                content_item = f"{pure_filename}：{final_display}"
            content_with_topic.append(content_item)

        def join_keywords(base, keywords):
            if not keywords:
                return base
            kw_str = ",".join(keywords)
            return f"{base},{kw_str}" if base else kw_str

        chinese_result = join_keywords(txt_str_clean, chinese_keywords)
        english_result = join_keywords(txt_str_clean, english_keywords)
        mix_result = join_keywords(txt_str_clean, mix_keywords)
        content_result = "、".join(content_with_topic)

        print("生成的中文提示词：", chinese_result)
        print("生成的英文提示词：", english_result)
        print("生成的中英混合提示词：", mix_result)
        print("包含主题内容：", content_result)

        return (chinese_result, english_result, mix_result, content_result)