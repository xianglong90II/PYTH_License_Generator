import tkinter as tk 
from tkinter import colorchooser, Listbox
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import random
import string
import json
from tkinter import filedialog

def save_project():
    if img is None:
        messagebox.showerror("错误", "没有打开的图片")
        return
    
    # 构建工程数据
    project_data = {
        "image_path": img_path,  # 当前图片路径
        "text_layers": text_layers  # 所有文字图层信息
    }
    
    # 弹出文件保存对话框
    save_path = tk.filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON 文件", "*.json")]
    )
    
    if save_path:
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(project_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", "工程已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存工程失败: {e}")

def load_project():
    global img, img_path, img_tk, draw, text_layers
    
    # 弹出文件选择对话框
    load_path = tk.filedialog.askopenfilename(
        filetypes=[("JSON 文件", "*.json")]
    )
    
    if load_path:
        try:
            with open(load_path, "r", encoding="utf-8") as f:
                project_data = json.load(f)
            
            # 加载图片
            img_path = project_data["image_path"]
            img = Image.open(img_path)
            draw = ImageDraw.Draw(img)
            img_tk = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            canvas.config(width=img.width, height=img.height)
            
            # 恢复文字图层
            text_layers = project_data["text_layers"]
            update_layer_list()
            preview_text()
            
            messagebox.showinfo("成功", "工程已加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载工程失败: {e}")

def load_images():
    return [f for f in os.listdir("licenseImages") if f.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]

def load_fonts():
    return [f for f in os.listdir("fonts") if f.endswith(".ttf")]

def open_image(*args):
    global img, img_tk, img_path, draw, text_layers, preview_text_data
    img_path = "licenseImages/" + image_var.get()
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    img_tk = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
    canvas.config(width=img.width, height=img.height)
    size_entry.delete(0, tk.END)
    size_entry.insert(0, str(min(img.width, img.height) // 10))
    x_entry.delete(0, tk.END)
    x_entry.insert(0, "0")
    y_entry.delete(0, tk.END)
    y_entry.insert(0, "0")
    text_layers.clear()
    preview_text_data = {}
    update_layer_list()
    preview_text()

def validate_coordinates(value, max_value):
    return value.isdigit() and 0 <= int(value) <= max_value

def preview_text(*args):
    if img is None:
        return
    preview_img = img.copy()
    preview_draw = ImageDraw.Draw(preview_img)

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
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

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

def save_image():
    if img is None:
        return
    
    # 创建 output_images 文件夹（如果不存在）
    os.makedirs("output_images", exist_ok=True)
    
    # 生成最终图片
    final_img = img.copy()
    final_draw = ImageDraw.Draw(final_img)
    for text_data in text_layers:
        font = ImageFont.truetype(text_data["font"], text_data["size"])
        final_draw.text((text_data["x"], text_data["y"]), text_data["text"], fill=text_data["color"], font=font)
    
    # 获取保存路径
    save_path = save_entry.get()
    if save_path:
        final_img.save(f"output_images/{save_path}.png")

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
    if random_mode == "单词":
        try:
            with open("dictionary.txt", "r", encoding="utf-8") as file:
                words = file.readlines()
                random_words = random.sample(words, random_length)
                return " ".join([word.strip() for word in random_words])
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到字典文件")
            return None
    elif random_mode == "数字编码":
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=random_length))
    elif random_mode == "随机数字":
        try:
            min_value = int(random_digit_min_entry.get())
            max_value = int(random_digit_max_entry.get())
            if min_value > max_value:
                messagebox.showerror("错误", "最小值不能大于最大值")
                return None
            # 生成随机数字并补零
            random_number = random.randint(min_value, max_value)
            random_string = str(random_number).zfill(random_length)
            return random_string
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字范围")
            return None
    return None

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
            if min_value > max_value:
                messagebox.showerror("错误", "最小值不能大于最大值")
                return
            # 生成随机数字并补零
            random_number = random.randint(min_value, max_value)
            random_string = str(random_number).zfill(length)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字范围")
            return
    else:
        random_string = generate_random_text(text_type, length)
    
    if random_string is not None:
        text_entry.delete(0, tk.END)
        text_entry.insert(0, random_string)
        update_preview_text()

def randomize_selected_layers():
    for i, text_data in enumerate(text_layers):
        if text_data.get("use_random", False):  # 仅对勾选了“使用随机”的图层进行随机化
            # 使用图层的随机模式和长度生成随机文字
            random_mode = text_data.get("random_mode", "数字编码")
            random_length = text_data.get("random_length", 1)
            
            # 如果是“随机数字”模式，使用图层存储的值
            if random_mode == "随机数字":
                random_min = text_data.get("random_min")
                random_max = text_data.get("random_max")
                if random_min is None or random_max is None:
                    messagebox.showerror("错误", "未找到数字范围")
                    return
                if random_min > random_max:
                    messagebox.showerror("错误", "最小值不能大于最大值")
                    return
                # 生成随机数字并补零
                random_number = random.randint(random_min, random_max)
                random_string = str(random_number).zfill(random_length)
            else:
                random_string = generate_random_text(random_mode, random_length)
            
            if random_string is not None:
                text_data["text"] = random_string
    
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

#右侧栏
right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

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

# 字体选择
font_label = tk.Label(top_frame, text="选择字体:")
font_label.pack(side=tk.LEFT)
font_dropdown = tk.OptionMenu(top_frame, font_var, *font_list)
font_dropdown.pack(side=tk.LEFT, padx=10)

# 左侧栏（字体相关设置）
left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, padx=10, pady=10)

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

# 添加“随机化选中图层”按钮
btn_randomize_layers = tk.Button(right_frame, text="随机化选中图层", command=randomize_selected_layers)
btn_randomize_layers.pack()

layer_label = tk.Label(right_frame, text="文字图层:")
layer_label.pack()
layer_listbox = Listbox(right_frame, height=5)
layer_listbox.pack()

btn_remove_text = tk.Button(right_frame, text="删除选中文字", command=remove_text)
btn_remove_text.pack()

save_label = tk.Label(right_frame, text="保存文件名:")
save_label.pack()
save_entry = tk.Entry(right_frame)
save_entry.pack()

btn_save = tk.Button(right_frame, text="保存图片", command=save_image)
btn_save.pack()

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
    
    # 创建 output_images 文件夹（如果不存在）
    os.makedirs("output_images", exist_ok=True)
    
    for i in range(batch_count):
        # 执行一次随机化选中图层
        randomize_selected_layers()
        
        # 生成最终图片
        final_img = img.copy()
        final_draw = ImageDraw.Draw(final_img)
        for text_data in text_layers:
            font = ImageFont.truetype(text_data["font"], text_data["size"])
            final_draw.text((text_data["x"], text_data["y"]), text_data["text"], fill=text_data["color"], font=font)
        
        # 保存图片
        save_path = f"output_images/{save_name}_{i + 1}.png"
        final_img.save(save_path)
    
    messagebox.showinfo("成功", f"已生成 {batch_count} 张图片")

batch_button = tk.Button(batch_frame, text="批量生成", command=batch_generate)
batch_button.pack(side=tk.LEFT)

canvas = tk.Canvas(root)
canvas.pack(side=tk.RIGHT)

img = None
img_tk = None
img_path = ""
draw = None
text_layers = []

if image_list:
    open_image()

root.mainloop()
