from safetensors.torch import load_file, save_file
import json

def read_metadata(file_path):
    # 直接解析文件头获取元数据（兼容旧版本）
    with open(file_path, "rb") as f:
        header = f.read(8)
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        return json.loads(header_data).get("__metadata__", {})

# 使用示例
if __name__ == "__main__":
    output_file = "D:/AI/风格艺术插画女孩(anime girl)_v1.0.safetensors"  # 避免覆盖原文件
    meta = read_metadata(output_file)
    if "lora_keywords" in meta:
        # 存在时再访问
        print("lora_keywords 的值：", meta["lora_keywords"])
    else:
        print("元数据中不存在 'lora_keywords23'")