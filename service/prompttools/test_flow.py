import re

def _extract_parts(text):
    """和代码中一样的解析逻辑"""
    if not text or "忽略" in text or "随机" in text:
        return "", ""
    
    bracket_pattern = r'^(.*?)\s*[（(]\s*(.*?)\s*[）)]$'
    match = re.match(bracket_pattern, text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    else:
        if re.search(r'[\u4e00-\u9fa5]', text):
            return text.strip(), ""
        else:
            return "", text.strip()

# 模拟几个标签的处理
test_tags = [
    "大师作品 (masterpiece)",
    "高质量 (high quality)",
    "龙珠 (Dragon Ball)",
    "安全 (safe)",
    "1girl (1girl)",
]

chinese_keywords = []
english_keywords = []
mix_keywords = []

print("=== 模拟处理流程 ===")
for tag in test_tags:
    chinese_part, english_part = _extract_parts(tag)
    
    print(f"原始: {tag}")
    print(f"  拆分: 中文='{chinese_part}' 英文='{english_part}'")
    
    if chinese_part:
        chinese_keywords.append(chinese_part)
    if english_part:
        english_keywords.append(english_part)
    
    # mix构建逻辑
    if chinese_part and english_part:
        mix_keywords.append(f"{chinese_part}（{english_part}）")
    elif chinese_part:
        mix_keywords.append(chinese_part)
    elif english_part:
        mix_keywords.append(english_part)

print("\n=== 最终结果 ===")
print(f"chinese_keywords: {chinese_keywords}")
print(f"english_keywords: {english_keywords}")
print(f"mix_keywords: {mix_keywords}")