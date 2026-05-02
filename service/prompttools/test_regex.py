import re

# 测试代码中的正则
bracket_pattern = r'^(.*?)\s*[（(]\s*(.*?)\s*[）)]$'

# 测试数据（当前txt文件的格式）
test_cases = [
    '大师作品 (masterpiece)',
    '龙珠 (Dragon Ball)',
    '紫罗兰永恒花园 (Violet Evergarden)',
    '1girl (1girl)',
    '安全 (safe)',
    '高质量 (high quality)',
    '室内 (indoor)',
]

print('=== Test Regex Matching ===')
for text in test_cases:
    match = re.match(bracket_pattern, text)
    if match:
        chinese = match.group(1).strip()
        english = match.group(2).strip()
        print(f'MATCH: "{text}"')
        print(f'   Chinese: "{chinese}" English: "{english}"')
    else:
        print(f'NO MATCH: "{text}"')