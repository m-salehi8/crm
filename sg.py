from PIL import Image
import numpy as np

def process_signature_standard(
    input_path,
    output_path,
    canvas_size=(2000, 200),
    bg_threshold=240
    ):
    # باز کردن تصویر
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)

    # محاسبه روشنایی (luminance)
    r, g, b = data[..., 0], data[..., 1], data[..., 2]
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)

    # alpha mask
    alpha = np.where(luminance > bg_threshold, 0, 255)

    # اعمال alpha
    data[..., 3] = alpha
    img = Image.fromarray(data, "RGBA")

    # کراپ ناحیه غیر شفاف
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    # ساخت canvas شفاف با سایز ثابت
    canvas = Image.new("RGBA", canvas_size, (255, 255, 255, 0))

    # resize بدون کشیدگی
    scale = min(
        canvas_size[0] / img.width,
        canvas_size[1] / img.height
    )
    new_size = (
        int(img.width * scale),
        int(img.height * scale)
    )
    img = img.resize(new_size, Image.LANCZOS)

    # وسط‌چین
    x = (canvas_size[0] - img.width) // 2
    y = (canvas_size[1] - img.height) // 2
    canvas.paste(img, (x, y), img)

    # ذخیره خروجی
    canvas.save(output_path, "PNG")
    print("✅ امضا شفاف، کراپ و استاندارد شد")


from PIL import Image


def remove_background_by_color(input_path, output_path, bg_color=(163, 175, 255), threshold=30):
    """حذف بک‌گراند سفید یا رنگ‌های مشابه"""
    img = Image.open(input_path)
    img = img.convert("RGBA")

    data = img.getdata()
    #print(data)
    new_data = []

    for item in data:
       # print(item)
        # محاسبه فاصله رنگ از رنگ بک‌گراند
        diff = sum(abs(item[i] - bg_color[i]) for i in range(3))

        if diff < threshold:
            # شفاف کردن پیکسل‌های بک‌گراند
            new_data.append((255, 255, 255, 0))
        else:
            # حفظ پیکسل‌های اصلی
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    return img


# استفاده
from PIL import Image

def remove_bg_pillow(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # اگر تقریبا سفید بود، شفافش کن
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))  # transparent
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")

#remove_bg_pillow("s.jpg", "signature_no_bg.png")

from PIL import Image

def remove_bg_smart(input_path, output_path, threshold=230):
    img = Image.open(input_path).convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (255, 255, 255, 0)

    img.save(output_path, "PNG")

remove_bg_smart("m.jpg", "signature_no_bg.png")