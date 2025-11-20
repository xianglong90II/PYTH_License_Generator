from PIL import Image, ImageFilter
import os

def add_drop_shadow(image, offset=(10, 10), blur_radius=10, shadow_color=(0, 0, 0, 160), background_color=(255,255,255,0)):
    """Return a new image with a drop shadow around the given RGBA `image`.

    - `offset`: (x, y) offset of the shadow relative to the image.
    - `blur_radius`: Gaussian blur radius for the shadow.
    - `shadow_color`: RGBA tuple for shadow color.
    - `background_color`: RGBA tuple for the resulting canvas background.
    """
    image = image.convert("RGBA")

    ox, oy = offset
    pad = blur_radius * 2
    total_w = image.width + abs(ox) + pad
    total_h = image.height + abs(oy) + pad

    # Prepare canvas
    canvas = Image.new("RGBA", (total_w, total_h), background_color)

    # Create shadow by using the alpha channel of the image
    if "A" in image.getbands():
        alpha = image.split()[3]
    else:
        # no alpha -> treat opaque
        alpha = Image.new("L", image.size, 255)

    shadow = Image.new("RGBA", image.size, shadow_color)
    shadow.putalpha(alpha)

    # Paste shadow and blur
    shadow_pos = (pad//2 + max(ox, 0), pad//2 + max(oy, 0))
    canvas.paste(shadow, shadow_pos, shadow)
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur_radius))

    # Paste original image on top
    img_pos = (pad//2 + max(-ox, 0), pad//2 + max(-oy, 0))
    canvas.paste(image, img_pos, image)
    return canvas

def composite_on_background(foreground, background_path, center=True):
    """Return a new image that pastes `foreground` onto the background image located at `background_path`.

    If `center` is True, the foreground is centered on the background; otherwise placed at (0,0).
    """
    if not os.path.exists(background_path):
        raise FileNotFoundError(f"Background not found: {background_path}")

    bg = Image.open(background_path).convert("RGBA")
    fg = foreground.convert("RGBA")

    if fg.width > bg.width or fg.height > bg.height:
        # if foreground bigger, scale it down to fit while preserving aspect
        ratio = min(bg.width / fg.width, bg.height / fg.height)
        new_size = (int(fg.width * ratio), int(fg.height * ratio))
        fg = fg.resize(new_size, Image.LANCZOS)

    if center:
        pos = ((bg.width - fg.width) // 2, (bg.height - fg.height) // 2)
    else:
        pos = (0, 0)

    out = bg.copy()
    out.paste(fg, pos, fg)
    return out
