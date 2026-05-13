import os
import re

# 检查所有txt文件中是否有不符合 "中文 (英文)" 格式的行
options_folder = os.path.join(os.path.dirname(__file__), "prompt_anima")

bracket_pattern = r'^(.*?)\s*[（(]\s*(.*?)\s*[）)]$'

all_files = []
for f in os.listdir(options_folder):
    if f.endswith('.txt'):
        all_files.append(f)

issues = []
for filename in all_files:
    with open(os.path.join(options_folder, filename), 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 尝试匹配
            match = re.match(bracket_pattern, line)
            if not match:
                # 不匹配，可能是纯中文或纯英文
                has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', line))
                has_english = bool(re.search(r'[a-zA-Z]', line))
                
                if has_chinese and has_english:
                    issues.append(f"{filename}:{i} -> {line}")

if issues:
    print("=== 发现格式问题 ===")
    for issue in issues:
        print(issue)
else:
    print("All files have consistent format!")