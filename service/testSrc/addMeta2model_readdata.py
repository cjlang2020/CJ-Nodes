import json

def read_metadata(file_path):
    with open(file_path, "rb") as f:
        header = f.read(8)
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        return json.loads(header_data).get("__metadata__", {})

def get_core_tags(meta, min_count=10):
    """
    从元数据中提取核心标签
    :param meta: 读取到的完整元数据
    :param min_count: 核心标签的最小出现次数（可调整）
    :return: 排序后的核心标签列表（按出现次数降序）
    """
    # 提取标签频率字符串并解析为JSON
    tag_freq_str = meta.get("ss_tag_frequency", "{}")
    try:
        tag_freq_dict = json.loads(tag_freq_str)
    except json.JSONDecodeError:
        print("标签数据解析失败")
        return []

    # 提取所有标签（忽略数据集分组键，如"5_zkz"）
    all_tags = {}
    for dataset_key, tags in tag_freq_dict.items():
        for tag, count in tags.items():
            all_tags[tag] = count  # 若有重复标签（多数据集），取最后一次出现的计数

    # 筛选核心标签（出现次数≥min_count）并按次数降序排序
    core_tags = [(tag, count) for tag, count in all_tags.items() if count >= min_count]
    core_tags.sort(key=lambda x: x[1], reverse=True)

    return core_tags

# 使用示例
if __name__ == "__main__":
    output_file = "D:/AI/comfyui_models/loras/SDXL/SDXL人造人18号_v1.0.safetensors"
    meta = read_metadata(output_file)
    print("读取到的元数据：", meta)
    print("\n" + "="*50)

    # 读取核心标签（最小出现次数设为10，可根据需求调整）
    core_tags = get_core_tags(meta, min_count=1)
    print("核心标签（出现次数≥1）：")
    tags=""
    for tag, count in core_tags:
        print(f"{tag}: {count}次、")
        tags=tags+tag+","
    print(f"核心标签：{tags}")