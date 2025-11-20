import json
import os
from tkinter import messagebox
from config import OUTPUT_DIR
from PIL import Image, ImageDraw, ImageFont
import effects

def save_project_to_path(project_data, save_path):
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        messagebox.showerror("错误", f"保存工程失败: {e}")
        return False

def load_project_from_path(load_path):
    try:
        with open(load_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("错误", f"加载工程失败: {e}")
        return None

def save_image(final_img, save_name, text_layers=None, base_image_path=None, effects_opts=None):
    """Save image to output dir. Optional rendering/effects:

    - `text_layers`: list of layer dicts (if present and stroke requested, used to re-render text with stroke)
    - `base_image_path`: path to base image to re-render text on (required when re-rendering stroke)
    - `effects_opts`: dict of effect options, supported keys:
        - stroke_width (int), stroke_fill (color)
        - shadow: bool, shadow_offset: (x,y), shadow_blur: int, shadow_color: (r,g,b,a)
        - background_name: filename under `backgroundImages/` to composite onto
    """
    if not save_name:
        messagebox.showerror("错误", "未指定保存文件名")
        return False

    img_to_save = final_img

    # Optionally re-render text with stroke if requested
    if effects_opts and effects_opts.get("stroke_width"):
        if text_layers and base_image_path and os.path.exists(base_image_path):
            try:
                img = Image.open(base_image_path).convert("RGBA")
                draw = ImageDraw.Draw(img)
                for td in text_layers:
                    font = ImageFont.truetype(td["font"], td["size"])
                    stroke_w = effects_opts.get("stroke_width", 0)
                    stroke_fill = effects_opts.get("stroke_fill", "black")
                    draw.text((td["x"], td["y"]), td["text"], fill=td.get("color", "black"), font=font, stroke_width=stroke_w, stroke_fill=stroke_fill)
                img_to_save = img
            except Exception as e:
                messagebox.showerror("错误", f"渲染带描边的图片失败: {e}")
                return False

    # Optionally apply shadow
    if effects_opts and effects_opts.get("shadow"):
        try:
            offset = effects_opts.get("shadow_offset", (10, 10))
            blur = effects_opts.get("shadow_blur", 10)
            shadow_color = effects_opts.get("shadow_color", (0, 0, 0, 160))
            img_to_save = effects.add_drop_shadow(img_to_save, offset=offset, blur_radius=blur, shadow_color=shadow_color)
        except Exception as e:
            messagebox.showerror("错误", f"应用投影失败: {e}")
            return False

    # Optionally composite on background
    if effects_opts and effects_opts.get("background_name"):
        try:
            bg_name = effects_opts.get("background_name")
            bg_path = os.path.join("backgroundImages", bg_name)
            img_to_save = effects.composite_on_background(img_to_save, bg_path, center=effects_opts.get("center", True))
        except Exception as e:
            messagebox.showerror("错误", f"合成背景失败: {e}")
            return False

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        img_to_save.save(os.path.join(OUTPUT_DIR, f"{save_name}.png"))
        return True
    except Exception as e:
        messagebox.showerror("错误", f"保存图片失败: {e}")
        return False
