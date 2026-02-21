import numpy as np
from PIL import Image


def rgb_to_hls(r, g, b):
    """تبدیل RGB به HLS (بدون وابستگی به colorsys)"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    h = l = s = 0.0

    l = (max_val + min_val) / 2.0

    if max_val != min_val:
        s = (max_val - min_val) / (2.0 - max_val - min_val) if l > 0.5 else (max_val - min_val) / (max_val + min_val)
        if max_val == r:
            h = (g - b) / (max_val - min_val)
        elif max_val == g:
            h = 2.0 + (b - r) / (max_val - min_val)
        else:
            h = 4.0 + (r - g) / (max_val - min_val)
        h *= 60.0
        if h < 0:
            h += 360.0

    return h, l, s


def hls_to_rgb(h, l, s):
    """تبدیل HLS به RGB (بدون وابستگی به colorsys)"""
    if s == 0:
        r = g = b = int(l * 255)
    else:
        def hue_to_rgb(p, q, t):
            t += 1.0 if t < 0 else (-1.0 if t > 1 else 0.0)
            if t < 1 / 6:
                return p + (q - p) * 6.0 * t
            if t < 0.5:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6.0
            return p

        h /= 360.0
        q = l * (1 + s) if l < 0.5 else l + s - (l * s)
        p = 2.0 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)

    return r, g, b


def get_dominant_color(image_path):
    """استخراج رنگ غالب از تصویر"""
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB').resize((100, 100))
            pixels = np.array(img).reshape(-1, 3)
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            return unique_colors[counts.argmax()]
    except Exception as e:
        print(f"Error processing image: {e}")
        return 90, 20, 20  # رنگ پیش‌فرض (قرمز تیره)


def generate_theme_colors(dominant_rgb):
    """تولید پالت رنگ از رنگ اصلی"""
    h, l, s = rgb_to_hls(*dominant_rgb)

    derivatives = [
        {"s": s * 0.1, "l": 0.96},  # رنگ روشن
        {"s": s * 0.4, "l": 0.85},  # رنگ متوسط
        {"s": s * 0.05, "l": 0.99}  # نزدیک به سفید
    ]

    return [
        "#{:02x}{:02x}{:02x}".format(*hls_to_rgb(h, derive["l"], derive["s"]))
        for derive in derivatives
    ]
