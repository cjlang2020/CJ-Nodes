import os
import random
import glob
from datetime import datetime

class FileReadDeal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":
                {
                "dirPath": ("STRING", {"default": "", "multiline": False}),
                "count": ("INT", {"default": 5, "min": 1, "max": 9999}),
                "isRandom": ("BOOLEAN", {"default": False}),
                "min_count": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "max_count": ("INT", {"default": 5, "min": 1, "max": 9999}),
                }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("array", "count")
    OUTPUT_IS_LIST = (True, False)
    FUNCTION = "read_files"
    CATEGORY = "luy/文件处理"

    def read_files(self, dirPath, count, isRandom, min_count, max_count):
        if not dirPath.strip() or not os.path.exists(dirPath):
            return ([], 0)

        txt_files = glob.glob(os.path.join(dirPath, "*.txt"))
        txt_files.sort()

        if not txt_files:
            return ([], 0)

        if isRandom:
            count = random.randint(min_count, max_count)

        count = min(count, len(txt_files))

        if isRandom:
            selected_files = random.sample(txt_files, count)
        else:
            selected_files = txt_files[:count]

        result_array = []
        for file_path in selected_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    result_array.append(content)
            except Exception as e:
                result_array.append(f"Error reading {os.path.basename(file_path)}: {str(e)}")

        return (result_array, len(result_array))


class FileSaveDeal:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":
                {
                "fileContent": ("STRING", {"default": "", "multiline": False}),
                "savePath": ("STRING", {"default": "", "multiline": False}),
                }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "save_file"
    CATEGORY = "luy/文件处理"

    def save_file(self, fileContent, savePath):
        if not savePath.strip():
            return ("",)

        if not os.path.exists(savePath):
            try:
                os.makedirs(savePath, exist_ok=True)
            except Exception as e:
                return (f"Error creating directory: {str(e)}",)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{timestamp}.txt"
        filepath = os.path.join(savePath, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fileContent)
            return (savePath,)
        except Exception as e:
            return (f"Error saving file: {str(e)}",)