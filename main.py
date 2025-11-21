import tkinter as tk 
from tkinter import colorchooser, Listbox
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import random
import string
import json
from tkinter import filedialog
import assets
import generator
import io_ops
import config

def save_project():
    if img is None:
        messagebox.showerror("错误", "没有打开的图片")
        return

    project_data = {
        "image_path": img_path,
        "text_layers": text_layers,
        "image_layers": [{"path": il.get("path"), "x": il.get("x"), "y": il.get("y"), "w": il.get("w"), "h": il.get("h")} for il in image_layers]
    }

    save_path = tk.filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON 文件", "*.json")]
    )

    if save_path:
        ok = io_ops.save_project_to_path(project_data, save_path)
        if ok:
            messagebox.showinfo("成功", "工程已保存")

def load_project():
    global img, img_path, img_tk, draw, text_layers

    load_path = tk.filedialog.askopenfilename(
        filetypes=[("JSON 文件", "*.json")]
    )

    if load_path:
        project_data = io_ops.load_project_from_path(load_path)
        if not project_data:
            return

        try:
            img_path = project_data["image_path"]
            img = Image.open(img_path)
            draw = ImageDraw.Draw(img)
            img_tk = ImageTk.PhotoImage(img)
            try:
                canvas.delete("all")
            except Exception:
                pass
            canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            canvas.configure(scrollregion=(0, 0, img.width, img.height))

            text_layers = project_data.get("text_layers", [])
            image_layers.clear()
            # restore image layers if present (store metadata -> reopen scaled images)
            for il in project_data.get("image_layers", []):
                try:
                    p = il.get("path")
                    w = il.get("w")
                    h = il.get("h")
                    x = il.get("x", 0)
                    y = il.get("y", 0)
                    pil = Image.open(p).convert("RGBA")
                    if w and h:
                        pil = pil.resize((int(w), int(h)), Image.LANCZOS)
                    image_layers.append({"path": p, "pil": pil, "w": pil.width, "h": pil.height, "x": int(x), "y": int(y)})
                except Exception:
                    # skip problematic image layers
                    continue

            update_layer_list()
            update_image_layer_list()
            preview_text()

            messagebox.showinfo("成功", "工程已加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载工程失败: {e}")

def load_images():
    return assets.load_images()

def load_fonts():
    return assets.load_fonts()

def open_image(*args):
    global img, img_tk, img_path, draw, text_layers, preview_text_data
    img_path = "licenseImages/" + image_var.get()
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    img_tk = ImageTk.PhotoImage(img)
    size_entry.delete(0, tk.END)
    size_entry.insert(0, str(min(img.width, img.height) // 10))
    x_entry.delete(0, tk.END)
    x_entry.insert(0, "0")
    y_entry.delete(0, tk.END)
    y_entry.insert(0, "0")
    # 根据用户选择决定是否清空现有图层
    if clear_layers_var.get():
        text_layers.clear()
        image_layers.clear()
        preview_text_data = {}
        update_layer_list()
        update_image_layer_list()
    # 总是刷新画布显示（但如果不清空图层，则保留图层信息）
    preview_text()

def validate_coordinates(value, max_value):
    return value.isdigit() and 0 <= int(value) <= max_value

def preview_text(*args):
    if img is None:
        return
    preview_img = img.copy()
    preview_draw = ImageDraw.Draw(preview_img)

    # 先绘制已添加的图片图层
    for il in image_layers:
        try:
            pil = il.get("pil")
            if pil:
                preview_img.paste(pil, (int(il.get("x", 0)), int(il.get("y", 0))), pil)
        except Exception:
            continue

    # 绘制预览中的图片（当前图片图层的预览）
    if preview_image_data:
        try:
            pil = preview_image_data.get("pil")
            if pil:
                preview_img.paste(pil, (int(preview_image_data.get("x", 0)), int(preview_image_data.get("y", 0))), pil)
                # 描边矩形框
                bbox = (preview_image_data.get("x", 0), preview_image_data.get("y", 0), preview_image_data.get("x", 0) + pil.width, preview_image_data.get("y", 0) + pil.height)
                preview_draw.rectangle(bbox, outline="black", width=2)
        except Exception:
            pass

    # 绘制已经添加的文字（不绘制矩形框）
    for text_data in text_layers:
        font = ImageFont.truetype(text_data["font"], text_data["size"])
        x, y = text_data["x"], text_data["y"]
        text = text_data["text"]
        color = text_data["color"]

        preview_draw.text((x, y), text, fill=color, font=font)

    # 绘制预览中的文字（当前文本框中的文字，保留矩形框）
    if preview_text_data:
        font = ImageFont.truetype(preview_text_data["font"], preview_text_data["size"])
        x, y = preview_text_data["x"], preview_text_data["y"]
        text = preview_text_data["text"]
        color = preview_text_data["color"]
        
        preview_draw.text((x, y), text, fill=color, font=font)
        bbox = preview_draw.textbbox((x, y), text, font=font)
        preview_draw.rectangle(bbox, outline="black", width=3)

    global img_tk
    img_tk = ImageTk.PhotoImage(preview_img)
    # clear previous canvas items and show new image
    try:
        canvas.delete("all")
    except Exception:
        pass
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
    # set scrollregion to image size so scrollbars work
    canvas.configure(scrollregion=(0, 0, preview_img.width, preview_img.height))

def update_preview_text(event=None):
    if img is None:
        return
    x = x_entry.get()
    y = y_entry.get()
    
    if not validate_coordinates(x, img.width) or not validate_coordinates(y, img.height):
        return
    
    global preview_text_data
    preview_text_data = {
        "text": text_entry.get(),
        "x": int(x),
        "y": int(y),
        "font": "fonts/" + font_var.get(),
        "size": int(size_entry.get()),
        "color": color_var.get()
    }
    preview_text()

def add_text():
    global preview_text_data
    if img is None or not preview_text_data:
        return
    
    # 添加随机模式和长度到图层数据
    preview_text_data["random_mode"] = random_type.get()  # 当前随机模式
    preview_text_data["random_length"] = int(random_length_entry.get())  # 当前随机长度
    preview_text_data["use_random"] = use_random_var.get()  # 是否使用随机
    
    # 如果随机模式是“随机数字”，存储数字范围
    if preview_text_data["random_mode"] == "随机数字":
        try:
            preview_text_data["random_min"] = int(random_digit_min_entry.get())  # 最小值
            preview_text_data["random_max"] = int(random_digit_max_entry.get())  # 最大值
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字范围")
            return
    
    text_layers.append(preview_text_data.copy())
    update_layer_list()
    preview_text_data = {}
    preview_text()

def remove_text():
    selected = layer_listbox.curselection()
    if selected:
        del text_layers[selected[0]]
        update_layer_list()
        preview_text()

def browse_image_file():
    p = tk.filedialog.askopenfilename(title="选择图片文件", filetypes=[("图片", "*.png *.jpg *.jpeg *.bmp *.gif")])
    if p:
        image_path_entry.delete(0, tk.END)
        image_path_entry.insert(0, p)

def open_image_layer():
    """Open the selected image for adding as a layer and scale to target size for preview."""
    global preview_image_data
    if img is None:
        messagebox.showerror("错误", "请先打开背景图片")
        return
    p = image_path_entry.get()
    if not p:
        messagebox.showerror("错误", "请选择要添加的图片文件")
        return
    try:
        w_val = width_entry.get()
        h_val = height_entry.get()
        w = int(w_val) if w_val.isdigit() else None
        h = int(h_val) if h_val.isdigit() else None
        pil = Image.open(p).convert("RGBA")
        if w and h:
            pil = pil.resize((w, h), Image.LANCZOS)
        x = int(x_img_entry.get()) if x_img_entry.get().isdigit() else 0
        y = int(y_img_entry.get()) if y_img_entry.get().isdigit() else 0
        preview_image_data = {"path": p, "pil": pil, "w": pil.width, "h": pil.height, "x": x, "y": y}
        preview_text()
    except Exception as e:
        messagebox.showerror("错误", f"打开图片失败: {e}")

def add_image_layer():
    global preview_image_data
    if img is None:
        messagebox.showerror("错误", "请先打开背景图片")
        return
    if not preview_image_data:
        messagebox.showerror("错误", "请先预览要添加的图片图层")
        return
    # append a copy (keep pil in memory)
    image_layers.append({"path": preview_image_data.get("path"), "pil": preview_image_data.get("pil"), "w": preview_image_data.get("w"), "h": preview_image_data.get("h"), "x": preview_image_data.get("x"), "y": preview_image_data.get("y")})
    update_image_layer_list()
    preview_image_data = {}
    preview_text()

def remove_image_layer():
    selected = image_layer_listbox.curselection()
    if selected:
        del image_layers[selected[0]]
        update_image_layer_list()
        preview_text()

def save_image():
    if img is None:
        return
    final_img = img.copy()
    # paste image layers first
    for il in image_layers:
        try:
            pil = il.get("pil")
            if pil:
                final_img.paste(pil, (int(il.get("x", 0)), int(il.get("y", 0))), pil)
        except Exception:
            continue

    final_draw = ImageDraw.Draw(final_img)
    # draw text layers (optionally with stroke)
    stroke_opts = None
    if use_stroke_var.get():
        try:
            sw = int(stroke_width_entry.get())
        except Exception:
            sw = 0
        stroke_fill = stroke_color_var.get()
        stroke_opts = {"stroke_width": sw, "stroke_fill": stroke_fill}

    for text_data in text_layers:
        font = ImageFont.truetype(text_data["font"], text_data["size"])
        if stroke_opts and stroke_opts.get("stroke_width", 0) > 0:
            final_draw.text((text_data["x"], text_data["y"]), text_data["text"], fill=text_data["color"], font=font, stroke_width=stroke_opts["stroke_width"], stroke_fill=stroke_opts.get("stroke_fill"))
        else:
            final_draw.text((text_data["x"], text_data["y"]), text_data["text"], fill=text_data["color"], font=font)

    # Build effects options (shadow/background), do NOT include stroke because already applied
    effects_opts = {}
    if use_shadow_var.get():
        try:
            ox = int(shadow_offset_x.get())
        except Exception:
            ox = 10
        try:
            oy = int(shadow_offset_y.get())
        except Exception:
            oy = 10
        try:
            blur = int(shadow_blur_entry.get())
        except Exception:
            blur = 10
        sc = hex_to_rgba(shadow_color_var.get(), alpha=160)
        if sc is None:
            sc = (0, 0, 0, 160)
        effects_opts.update({"shadow": True, "shadow_offset": (ox, oy), "shadow_blur": blur, "shadow_color": sc})

    if bg_var.get():
        effects_opts["background_name"] = bg_var.get()
        effects_opts["center"] = center_bg_var.get()

    save_name = save_entry.get()
    if save_name:
        ok = io_ops.save_image(final_img, save_name, text_layers=None, base_image_path=None, effects_opts=effects_opts if effects_opts else None)
        if ok:
            messagebox.showinfo("成功", "图片已保存")

def choose_color():
    color_code = colorchooser.askcolor(title="选择颜色")[1]
    if color_code:
        color_var.set(color_code)
        color_display.config(bg=color_code)
        update_preview_text()

def update_layer_list():
    layer_listbox.delete(0, tk.END)
    for i, text_data in enumerate(text_layers):
        random_mode = text_data.get("random_mode", "数字编码")
        random_length = text_data.get("random_length", 1)
        use_random = text_data.get("use_random", False)
        layer_info = f"{i + 1}: {text_data['text']} (模式: {random_mode}, 长度: {random_length}, 使用随机: {'是' if use_random else '否'}"
        
        # 如果随机模式是“随机数字”，显示数字范围
        if random_mode == "随机数字":
            random_min = text_data.get("random_min")
            random_max = text_data.get("random_max")
            if random_min is not None and random_max is not None:
                layer_info += f", 范围: {random_min}-{random_max}"
        
        layer_info += ")"
        layer_listbox.insert(tk.END, layer_info)

def update_image_layer_list():
    # list image layers in a separate listbox
    try:
        image_layer_listbox.delete(0, tk.END)
    except Exception:
        return

    for i, il in enumerate(image_layers):
        info = f"{i + 1}: {os.path.basename(il.get('path',''))} (大小: {il.get('w')}x{il.get('h')}, 位置: {il.get('x')},{il.get('y')})"
        image_layer_listbox.insert(tk.END, info)

def adjust_x(offset):
    x = int(x_entry.get()) + offset
    x = max(0, min(x, img.width))
    x_entry.delete(0, tk.END)
    x_entry.insert(0, str(x))
    update_preview_text()

def adjust_y(offset):
    y = int(y_entry.get()) + offset
    y = max(0, min(y, img.height))
    y_entry.delete(0, tk.END)
    y_entry.insert(0, str(y))
    update_preview_text()

def adjust_font_size(offset):
    size = int(size_entry.get()) + offset
    size = max(1, size)  # 防止字体大小小于 1
    size_entry.delete(0, tk.END)
    size_entry.insert(0, str(size))
    update_preview_text()

def generate_random_text(random_mode, random_length):
    return generator.generate_random_text(random_mode, random_length)

def random_text():
    length = random_length_entry.get()
    if not length.isdigit() or int(length) <= 0:
        messagebox.showerror("错误", "请输入有效的长度值")
        return

    length = int(length)
    text_type = random_type.get()
    # 如果是“随机数字”模式，使用输入框中的值
    if text_type == "随机数字":
        try:
            min_value = int(random_digit_min_entry.get())
            max_value = int(random_digit_max_entry.get())
            random_string = generator.generate_random_text(text_type, length, random_min=min_value, random_max=max_value)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字范围")
            return
    else:
        random_string = generator.generate_random_text(text_type, length)

    if random_string is not None:
        text_entry.delete(0, tk.END)
        text_entry.insert(0, random_string)
        update_preview_text()

def randomize_selected_layers():
    generator.randomize_selected_layers(text_layers)
    update_layer_list()
    preview_text()

# 初始化 GUI
root = tk.Tk()
root.title("屁眼通红证件办理器v1.0————VRC办证刻章局  HX2 xianglong90")

# 添加存档和读档按钮
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="文件", menu=file_menu)

file_menu.add_command(label="存档", command=save_project)
file_menu.add_command(label="读档", command=load_project)

# 窗口内容
image_list = load_images()
font_list = load_fonts()

default_image = image_list[0] if image_list else ""
default_font = font_list[0] if font_list else ""

image_var = tk.StringVar(root, default_image)
font_var = tk.StringVar(root, default_font)
color_var = tk.StringVar(root, "black")
preview_text_data = {}
# 是否在切换背景图片时清空所有图层
clear_layers_var = tk.BooleanVar(value=True)

#右侧栏
right_frame = tk.Frame(root,width=300)
# do not pack now; will be embedded into a scrollable right container after center is created

# 其他控件初始化代码
random_type = tk.StringVar(value="单词")  # 创建随机模式变量
random_length_entry = tk.Entry(right_frame)  # 创建随机长度输入框

# 初始化随机模式和长度
random_type.set("数字编码")  # 默认模式为“数字编码”
random_length_entry.delete(0, tk.END)
random_length_entry.insert(0, "1")  # 默认长度为 1


# 顶部栏
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

# 图片选择
image_label = tk.Label(top_frame, text="选择图片:")
image_label.pack(side=tk.LEFT)
image_var.trace("w", open_image)
image_dropdown = tk.OptionMenu(top_frame, image_var, *image_list)
image_dropdown.pack(side=tk.LEFT, padx=10)
# 切换图片时是否清空所有图层
clear_layers_cb = tk.Checkbutton(top_frame, text="是否清空图层", variable=clear_layers_var)
clear_layers_cb.pack(side=tk.LEFT, padx=6)

# 字体选择
font_label = tk.Label(top_frame, text="选择字体:")
font_label.pack(side=tk.LEFT)
font_dropdown = tk.OptionMenu(top_frame, font_var, *font_list)
font_dropdown.pack(side=tk.LEFT, padx=10)

# 左侧栏（字体相关设置） — 使用可滚动区域以容纳较多控件
left_container = tk.Frame(root)
left_container.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

# Canvas + scrollbar
left_canvas = tk.Canvas(left_container, borderwidth=0,width=200)
left_scrollbar = tk.Scrollbar(left_container, orient=tk.VERTICAL, command=left_canvas.yview)
left_canvas.configure(yscrollcommand=left_scrollbar.set)

left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 内部可滚动 frame，后面代码继续将控件添加到 `left_frame`
left_frame = tk.Frame(left_canvas)
left_canvas.create_window((0, 0), window=left_frame, anchor=tk.NW)

def _left_frame_configure(event):
    left_canvas.configure(scrollregion=left_canvas.bbox("all"))

left_frame.bind("<Configure>", _left_frame_configure)

def _on_mousewheel_left(event):
    # Windows: event.delta is multiple of 120
    try:
        left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    except Exception:
        pass

left_canvas.bind_all("<MouseWheel>", _on_mousewheel_left)

# 字体大小
size_label = tk.Label(left_frame, text="字体大小:")
size_label.pack()
size_entry = tk.Entry(left_frame)
size_entry.pack()

# 字体大小调整按钮
font_size_adjust_buttons_frame = tk.Frame(left_frame)
font_size_adjust_buttons_frame.pack()

btn_size_minus_1 = tk.Button(font_size_adjust_buttons_frame, text="-1", command=lambda: adjust_font_size(-1))
btn_size_minus_1.pack(side=tk.LEFT)

btn_size_plus_1 = tk.Button(font_size_adjust_buttons_frame, text="+1", command=lambda: adjust_font_size(1))
btn_size_plus_1.pack(side=tk.LEFT)

# 文字输入
text_label = tk.Label(left_frame, text="输入文字:")
text_label.pack()
text_entry = tk.Entry(left_frame)
text_entry.pack()
text_entry.bind("<KeyRelease>", update_preview_text)

# 随机文字生成
random_label = tk.Label(left_frame, text="随机文字:")
random_label.pack()

random_length_label = tk.Label(left_frame, text="长度:")
random_length_label.pack()
random_length_entry = tk.Entry(left_frame)
random_length_entry.pack()

random_type = tk.StringVar(value="单词")
random_word_radio = tk.Radiobutton(left_frame, text="单词", variable=random_type, value="单词")
random_word_radio.pack()
random_number_radio = tk.Radiobutton(left_frame, text="数字编码", variable=random_type, value="数字编码")
random_number_radio.pack()
random_digit_radio = tk.Radiobutton(left_frame, text="随机数字", variable=random_type, value="随机数字")
random_digit_radio.pack()

# 随机数字范围
random_digit_range_frame = tk.Frame(left_frame)
random_digit_range_frame.pack()

random_digit_min_label = tk.Label(random_digit_range_frame, text="最小值:")
random_digit_min_label.pack(side=tk.LEFT)
random_digit_min_entry = tk.Entry(random_digit_range_frame, width=5)
random_digit_min_entry.pack(side=tk.LEFT)
random_digit_min_entry.insert(0, "0")  # 默认最小值为 0

random_digit_max_label = tk.Label(random_digit_range_frame, text="最大值:")
random_digit_max_label.pack(side=tk.LEFT)
random_digit_max_entry = tk.Entry(random_digit_range_frame, width=5)
random_digit_max_entry.pack(side=tk.LEFT)
random_digit_max_entry.insert(0, "100")  # 默认最大值为 100

# 随机按钮
random_button = tk.Button(left_frame, text="随机", command=random_text)
random_button.pack()

# 坐标设置
x_label = tk.Label(left_frame, text="X 坐标:")
x_label.pack()
x_entry = tk.Entry(left_frame)
x_entry.pack()
x_entry.bind("<KeyRelease>", update_preview_text)
x_entry.insert(0, "0")

# X 坐标调整按钮
x_adjust_buttons_frame = tk.Frame(left_frame)
x_adjust_buttons_frame.pack()

btn_x_minus_10 = tk.Button(x_adjust_buttons_frame, text="-10", command=lambda: adjust_x(-10))
btn_x_minus_10.pack(side=tk.LEFT)

btn_x_minus_1 = tk.Button(x_adjust_buttons_frame, text="-1", command=lambda: adjust_x(-1))
btn_x_minus_1.pack(side=tk.LEFT)

btn_x_plus_1 = tk.Button(x_adjust_buttons_frame, text="+1", command=lambda: adjust_x(1))
btn_x_plus_1.pack(side=tk.LEFT)

btn_x_plus_10 = tk.Button(x_adjust_buttons_frame, text="+10", command=lambda: adjust_x(10))
btn_x_plus_10.pack(side=tk.LEFT)

y_label = tk.Label(left_frame, text="Y 坐标:")
y_label.pack()
y_entry = tk.Entry(left_frame)
y_entry.pack()
y_entry.bind("<KeyRelease>", update_preview_text)
y_entry.insert(0, "0")

# Y 坐标调整按钮
y_adjust_buttons_frame = tk.Frame(left_frame)
y_adjust_buttons_frame.pack()

btn_y_minus_10 = tk.Button(y_adjust_buttons_frame, text="-10", command=lambda: adjust_y(-10))
btn_y_minus_10.pack(side=tk.LEFT)

btn_y_minus_1 = tk.Button(y_adjust_buttons_frame, text="-1", command=lambda: adjust_y(-1))
btn_y_minus_1.pack(side=tk.LEFT)

btn_y_plus_1 = tk.Button(y_adjust_buttons_frame, text="+1", command=lambda: adjust_y(1))
btn_y_plus_1.pack(side=tk.LEFT)

btn_y_plus_10 = tk.Button(y_adjust_buttons_frame, text="+10", command=lambda: adjust_y(10))
btn_y_plus_10.pack(side=tk.LEFT)

# 颜色选择
color_label = tk.Label(left_frame, text="选择颜色:")
color_label.pack()
color_button = tk.Button(left_frame, text="选择颜色", command=choose_color)
color_button.pack()
color_display = tk.Label(left_frame, width=10, height=2, bg="black")
color_display.pack()

# 添加“使用随机”勾选框
use_random_var = tk.BooleanVar(value=False)
use_random_checkbox = tk.Checkbutton(left_frame, text="使用随机", variable=use_random_var)
use_random_checkbox.pack()

# 添加文字按钮
btn_text = tk.Button(left_frame, text="添加文字", command=add_text)
btn_text.pack()

# ---- Image layer controls (左侧) ----
img_layer_label = tk.Label(left_frame, text="图片图层:")
img_layer_label.pack(pady=(8,0))

image_path_entry = tk.Entry(left_frame, width=30)
image_path_entry.pack()

browse_img_btn = tk.Button(left_frame, text="选择图片文件", command=browse_image_file)
browse_img_btn.pack(pady=2)

size_frame_img = tk.Frame(left_frame)
size_frame_img.pack()
tk.Label(size_frame_img, text="宽: ").pack(side=tk.LEFT)
width_entry = tk.Entry(size_frame_img, width=6)
width_entry.pack(side=tk.LEFT)
tk.Label(size_frame_img, text="高: ").pack(side=tk.LEFT)
height_entry = tk.Entry(size_frame_img, width=6)
height_entry.pack(side=tk.LEFT)

pos_frame_img = tk.Frame(left_frame)
pos_frame_img.pack()
tk.Label(pos_frame_img, text="X: ").pack(side=tk.LEFT)
x_img_entry = tk.Entry(pos_frame_img, width=6)
x_img_entry.pack(side=tk.LEFT)
tk.Label(pos_frame_img, text="Y: ").pack(side=tk.LEFT)
y_img_entry = tk.Entry(pos_frame_img, width=6)
y_img_entry.pack(side=tk.LEFT)

img_preview_btn = tk.Button(left_frame, text="预览图片图层", command=open_image_layer)
img_preview_btn.pack(pady=4)

img_add_btn = tk.Button(left_frame, text="添加图片图层", command=add_image_layer)
img_add_btn.pack()

# 添加“随机化选中图层”按钮
btn_randomize_layers = tk.Button(right_frame, text="随机所有", command=randomize_selected_layers)
btn_randomize_layers.pack()

layer_label = tk.Label(right_frame, text="文字图层:")
layer_label.pack()
layer_listbox = Listbox(right_frame, height=5)
layer_listbox.pack()

btn_remove_text = tk.Button(right_frame, text="删除选中文字", command=remove_text)
btn_remove_text.pack()

image_layer_label = tk.Label(right_frame, text="图片图层:")
image_layer_label.pack()
image_layer_listbox = Listbox(right_frame, height=5)
image_layer_listbox.pack()

btn_remove_image = tk.Button(right_frame, text="删除选中图片", command=remove_image_layer)
btn_remove_image.pack()

save_label = tk.Label(right_frame, text="保存文件名:")
save_label.pack()
save_entry = tk.Entry(right_frame)
save_entry.pack()

# ---- Effects / composite options ----
effects_frame = tk.LabelFrame(right_frame, text="效果")
effects_frame.pack(pady=6, fill=tk.X)

# Stroke (描边)
use_stroke_var = tk.BooleanVar(value=False)
use_stroke_cb = tk.Checkbutton(effects_frame, text="描边", variable=use_stroke_var)
use_stroke_cb.pack(anchor=tk.W)

stroke_frame = tk.Frame(effects_frame)
stroke_frame.pack(fill=tk.X)
tk.Label(stroke_frame, text="宽度:").pack(side=tk.LEFT)
stroke_width_entry = tk.Entry(stroke_frame, width=4)
stroke_width_entry.insert(0, "2")
stroke_width_entry.pack(side=tk.LEFT, padx=4)

stroke_color_var = tk.StringVar(value="#000000")
def choose_stroke_color():
    col = colorchooser.askcolor(title="描边颜色")[1]
    if col:
        stroke_color_var.set(col)

stroke_color_btn = tk.Button(stroke_frame, text="描边颜色", command=choose_stroke_color)
stroke_color_btn.pack(side=tk.LEFT, padx=4)

# Shadow (投影)
use_shadow_var = tk.BooleanVar(value=False)
use_shadow_cb = tk.Checkbutton(effects_frame, text="投影", variable=use_shadow_var)
use_shadow_cb.pack(anchor=tk.W)

shadow_frame = tk.Frame(effects_frame)
shadow_frame.pack(fill=tk.X)
tk.Label(shadow_frame, text="偏移X:").pack(side=tk.LEFT)
shadow_offset_x = tk.Entry(shadow_frame, width=4)
shadow_offset_x.insert(0, "10")
shadow_offset_x.pack(side=tk.LEFT, padx=2)
tk.Label(shadow_frame, text="偏移Y:").pack(side=tk.LEFT)
shadow_offset_y = tk.Entry(shadow_frame, width=4)
shadow_offset_y.insert(0, "10")
shadow_offset_y.pack(side=tk.LEFT, padx=2)
tk.Label(shadow_frame, text="模糊:").pack(side=tk.LEFT)
shadow_blur_entry = tk.Entry(shadow_frame, width=4)
shadow_blur_entry.insert(0, "10")
shadow_blur_entry.pack(side=tk.LEFT, padx=2)

shadow_color_var = tk.StringVar(value="#000000")
def choose_shadow_color():
    col = colorchooser.askcolor(title="投影颜色")[1]
    if col:
        shadow_color_var.set(col)

shadow_color_btn = tk.Button(shadow_frame, text="投影颜色", command=choose_shadow_color)
shadow_color_btn.pack(side=tk.LEFT, padx=4)

# Background selection
bg_list = assets.load_backgrounds()
bg_var = tk.StringVar(value=bg_list[0] if bg_list else "")
tk.Label(effects_frame, text="背景:").pack(anchor=tk.W)
bg_dropdown = tk.OptionMenu(effects_frame, bg_var, *bg_list) if bg_list else tk.Label(effects_frame, text="(无)")
bg_dropdown.pack(fill=tk.X)

center_bg_var = tk.BooleanVar(value=True)
center_bg_cb = tk.Checkbutton(effects_frame, text="居中背景", variable=center_bg_var)
center_bg_cb.pack(anchor=tk.W)

def hex_to_rgba(hex_color, alpha=160):
    """Convert #RRGGBB to (r,g,b,a) tuple. If already color name (e.g., 'black'), PIL will handle it elsewhere; we try hex parsing only."""
    if not hex_color:
        return None
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return (r, g, b, alpha)
    except Exception:
        return None
    return None

# 添加批量生成功能
batch_frame = tk.Frame(right_frame)
batch_frame.pack()

batch_label = tk.Label(batch_frame, text="批量生成数量:")
batch_label.pack(side=tk.LEFT)

batch_count_entry = tk.Entry(batch_frame, width=5)
batch_count_entry.pack(side=tk.LEFT)
batch_count_entry.insert(0, "1")  # 默认生成 1 张

def batch_generate():
    try:
        batch_count = int(batch_count_entry.get())
        if batch_count <= 0:
            messagebox.showerror("错误", "请输入有效的数量")
            return
    except ValueError:
        messagebox.showerror("错误", "请输入有效的数量")
        return
    
    # 获取保存文件名
    save_name = save_entry.get()
    if not save_name:
        messagebox.showerror("错误", "请输入保存文件名")
        return
    
    for i in range(batch_count):
        # 执行一次随机化选中图层
        randomize_selected_layers()
        
        # 生成最终图片
        final_img = img.copy()
        # paste image layers
        for il in image_layers:
            try:
                pil = il.get("pil")
                if pil:
                    final_img.paste(pil, (int(il.get("x", 0)), int(il.get("y", 0))), pil)
            except Exception:
                continue

        final_draw = ImageDraw.Draw(final_img)
        # draw texts with optional stroke
        stroke_opts = None
        if use_stroke_var.get():
            try:
                sw = int(stroke_width_entry.get())
            except Exception:
                sw = 0
            stroke_fill = stroke_color_var.get()
            stroke_opts = {"stroke_width": sw, "stroke_fill": stroke_fill}

        for text_data in text_layers:
            font = ImageFont.truetype(text_data["font"], text_data["size"])
            if stroke_opts and stroke_opts.get("stroke_width", 0) > 0:
                final_draw.text((text_data["x"], text_data["y"]), text_data["text"], fill=text_data["color"], font=font, stroke_width=stroke_opts["stroke_width"], stroke_fill=stroke_opts.get("stroke_fill"))
            else:
                final_draw.text((text_data["x"], text_data["y"]), text_data["text"], fill=text_data["color"], font=font)
        
        # Build effects options (same as single save)
        effects_opts = {}
        if use_stroke_var.get():
            try:
                effects_opts["stroke_width"] = int(stroke_width_entry.get())
            except Exception:
                effects_opts["stroke_width"] = 0
            effects_opts["stroke_fill"] = stroke_color_var.get()

        if use_shadow_var.get():
            try:
                ox = int(shadow_offset_x.get())
            except Exception:
                ox = 10
            try:
                oy = int(shadow_offset_y.get())
            except Exception:
                oy = 10
            try:
                blur = int(shadow_blur_entry.get())
            except Exception:
                blur = 10
            sc = hex_to_rgba(shadow_color_var.get(), alpha=160)
            if sc is None:
                sc = (0, 0, 0, 160)
            effects_opts.update({"shadow": True, "shadow_offset": (ox, oy), "shadow_blur": blur, "shadow_color": sc})

        if bg_var.get():
            effects_opts["background_name"] = bg_var.get()
            effects_opts["center"] = center_bg_var.get()

        # 保存图片 via io_ops (effects_opts excludes stroke because stroke already applied)
        io_ops.save_image(final_img, f"{save_name}_{i + 1}", text_layers=None, base_image_path=None, effects_opts=effects_opts if effects_opts else None)
    
    messagebox.showinfo("成功", f"已生成 {batch_count} 张图片")


batch_button = tk.Button(batch_frame, text="批量生成", command=batch_generate)
batch_button.pack(side=tk.LEFT)

# 中央显示区域（带水平+垂直滚动条）
center_frame = tk.Frame(root)

# vertical and horizontal scrollbars for center canvas
center_vscroll = tk.Scrollbar(center_frame, orient=tk.VERTICAL)
center_hscroll = tk.Scrollbar(center_frame, orient=tk.HORIZONTAL)
canvas = tk.Canvas(center_frame, xscrollcommand=center_hscroll.set, yscrollcommand=center_vscroll.set, background="white")
center_vscroll.config(command=canvas.yview)
center_hscroll.config(command=canvas.xview)

center_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
center_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# pack center and right frames
left_container.update_idletasks()
center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
right_frame.pack(side=tk.RIGHT, fill=tk.Y)

# runtime state
img = None
img_tk = None
img_path = ""
draw = None
text_layers = []
image_layers = []
preview_image_data = {}

if image_list:
    open_image()

root.mainloop()
