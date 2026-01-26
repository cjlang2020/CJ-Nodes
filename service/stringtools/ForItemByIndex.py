import random

class ForItemByIndex:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required":
                {
                "text": ("STRING", {"default": " ", "multiline": False}),
                "count": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "isRandom": ("BOOLEAN", {"default": False}),
                "min": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "max": ("INT", {"default": 5, "min": 1, "max": 9999}),
                }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("array", "count")
    FUNCTION = "process_text"
    OUTPUT_IS_LIST = (True, False)
    CATEGORY = "luy/字符处理"

    def process_text(self, text, count, isRandom, min, max):
        if isRandom:
            count = random.randint(min, max)

        if not text.strip():
            result_array = [""] * count
        else:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                result_array = [""] * count
            else:
                result_array = []
                for i in range(count):
                    result_array.append(lines[i % len(lines)])

        return (result_array, count)