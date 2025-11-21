import os
from config import IMAGE_DIR, FONTS_DIR

def load_images():
    """Return list of image filenames in IMAGE_DIR."""
    try:
        return [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
    except FileNotFoundError:
        return []

def load_fonts():
    """Return list of font filenames in FONTS_DIR."""
    try:
        return [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(".ttf")]
    except FileNotFoundError:
        return []

def load_backgrounds():
    """Return list of background image filenames in `backgroundImages` folder."""
    bg_dir = "backgroundImages"
    try:
        return [f for f in os.listdir(bg_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
    except FileNotFoundError:
        return []

def load_backgrounds():
    """Return list of background image filenames in backgroundImages directory."""
    bg_dir = "backgroundImages"
    try:
        return [f for f in os.listdir(bg_dir) if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))]
    except FileNotFoundError:
        return []
