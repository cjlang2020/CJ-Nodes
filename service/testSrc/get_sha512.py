import hashlib
import os

def calculate_sha512(file_path, chunk_size=4096):
    """
    计算文件的 SHA-512 哈希值

    参数:
        file_path (str): 文件的绝对/相对路径
        chunk_size (int): 读取文件的分块大小（默认4096字节，可根据文件大小调整）

    返回:
        str: 文件的 SHA-512 哈希值（小写十六进制）
        None: 文件不存在/无法读取时返回None
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：文件 '{file_path}' 不存在！")
        return None

    # 检查是否是文件（而非文件夹）
    if not os.path.isfile(file_path):
        print(f"错误：'{file_path}' 不是一个文件！")
        return None

    try:
        # 创建 SHA-512 哈希对象
        sha512_hash = hashlib.sha512()

        # 分块读取文件（避免大文件占用过多内存）
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha512_hash.update(chunk)

        # 返回十六进制哈希值
        return sha512_hash.hexdigest()

    except PermissionError:
        print(f"错误：没有权限读取文件 '{file_path}'！")
        return None
    except Exception as e:
        print(f"读取文件时发生错误：{str(e)}")
        return None

def main():
    # 计算 SHA-512
    hash_value = calculate_sha512("D:/AI/comfyui_models/Qwen-Image-i2L/Qwen-Image-i2L-Fine.safetensors")

    # 输出结果
    if hash_value:
        print("\n========== SHA-512 哈希值 ==========")
        print(f"文件路径：")
        print(f"SHA-512：{hash_value}")
        print("====================================")

if __name__ == "__main__":
    main()