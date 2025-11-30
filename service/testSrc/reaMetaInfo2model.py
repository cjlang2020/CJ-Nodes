from safetensors.torch import load_file, save_file
import json

def read_metadata(file_path):
    # 直接解析文件头获取元数据（兼容旧版本）
    with open(file_path, "rb") as f:
        header = f.read(8)
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        print(header_data)
        return json.loads(header_data).get("__metadata__", {})

# 使用示例
if __name__ == "__main__":
    output_file = "D:/AI/comfyui_models/loras/zImage/DetailedEyes_Z-Image.safetensors"  # 避免覆盖原文件
    meta = read_metadata(output_file)
    print(meta)