import os
import re

# 测试实际代码的_extract_parts逻辑
def _extract_parts(actual_value):
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

# 测试几个实际的文件行
test_lines = [
    "大师作品 (masterpiece)",
    "高质量 (high quality)",
    "1girl (1girl)",
    "动漫风格 (anime style)",
]

print("=== Testing _extract_parts ===")
for line in test_lines:
    cn, en = _extract_parts(line)
    print(f"Input: '{line}'")
    print(f"  -> Chinese: '{cn}', English: '{en}'")
    print()