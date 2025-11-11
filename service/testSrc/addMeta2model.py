from safetensors.torch import load_file, save_file
import json

def add_metadata(input_path, output_path, new_meta):
    # 加载张量（旧版本只能先加载张量）
    tensors = load_file(input_path, device="cpu")
    with open(input_path, "rb") as f:
        header = f.read(8)  # 读取头部长度标识
        header_len = int.from_bytes(header, byteorder="little")
        header_data = f.read(header_len).decode("utf-8")
        original_meta = json.loads(header_data).get("__metadata__", {})

    # 合并元数据
    updated_meta = {**original_meta,** new_meta}

    # 保存新文件（包含更新后的元数据）
    save_file(tensors, output_path, metadata=updated_meta)
    print(f"已添加元数据并保存到: {output_path}")

# 使用示例
if __name__ == "__main__":
    input_file = "D:/AI/comfyui_models/loras/FLUX/风格艺术插画女孩(anime girl)_v1.0.safetensors"
    output_file = "D:/AI/风格艺术插画女孩(anime girl)_v1.0.safetensors"  # 避免覆盖原文件

    # 添加元数据
    add_metadata(input_file, output_file, {
        "lora_keywords": "目标移除LoRA模型","ceshi":"哈哈"
    })