import random
import string
from PIL import ImageFont
from tkinter import messagebox
from config import DICT_FILE

def generate_random_text(random_mode, random_length, dict_path=DICT_FILE, random_min=None, random_max=None):
    """Generate random text according to mode.

    Returns string or None on error.
    """
    if random_mode == "单词":
        try:
            with open(dict_path, "r", encoding="utf-8") as file:
                words = [w.strip() for w in file.readlines() if w.strip()]
                if not words:
                    messagebox.showerror("错误", "字典文件为空")
                    return None
                random_words = random.sample(words, min(len(words), random_length))
                return " ".join(random_words)
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到字典文件")
            return None
    elif random_mode == "数字编码":
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=random_length))
    elif random_mode == "随机数字":
        try:
            if random_min is None or random_max is None:
                messagebox.showerror("错误", "未提供数字范围")
                return None
            if random_min > random_max:
                messagebox.showerror("错误", "最小值不能大于最大值")
                return None
            random_number = random.randint(random_min, random_max)
            return str(random_number).zfill(random_length)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字范围")
            return None
    return None

def randomize_selected_layers(text_layers):
    """Mutate `text_layers` list: for layers with `use_random` True, regenerate their `text`.

    Each layer is expected to be a dict that may contain keys:
    - random_mode
    - random_length
    - random_min
    - random_max
    - use_random
    """
    for text_data in text_layers:
        if text_data.get("use_random", False):
            random_mode = text_data.get("random_mode", "数字编码")
            random_length = text_data.get("random_length", 1)
            if random_mode == "随机数字":
                random_min = text_data.get("random_min")
                random_max = text_data.get("random_max")
                if random_min is None or random_max is None:
                    messagebox.showerror("错误", "未找到数字范围")
                    return
                if random_min > random_max:
                    messagebox.showerror("错误", "最小值不能大于最大值")
                    return
                random_string = generate_random_text(random_mode, random_length, random_min=random_min, random_max=random_max)
            else:
                random_string = generate_random_text(random_mode, random_length)

            if random_string is not None:
                text_data["text"] = random_string
