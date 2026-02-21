from PIL import Image, ImageDraw, ImageFont
import random, string, base64, io, uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Captcha
import os

class CaptchaGenerate(APIView):
    def get(self, request):
        # 1) متن کپچا
        text = ''.join(random.choices( string.digits, k=4))
        captcha_id = str(uuid.uuid4())

        # 2) ویژگی های تصویر
        width, height = 180, 70
        img = Image.new('RGB', (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        # 3) فونت بزرگ‌تر (اگر فونت داری مسیر بده، وگرنه از default استفاده می‌کنیم)
        try:
            font = ImageFont.truetype("arial.ttf", 40)  # نیازمند وجود فونت روی سیستم
        except:
            font = ImageFont.load_default()

        # 4) محاسبه موقعیت متن برای وسط چین
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # 5) اضافه‌کردن متن
        draw.text((x, y), text, fill=(0, 0, 0), font=font)

        # 6) اضافه کردن نویز خطی
        for _ in range(5):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line((x1, y1, x2, y2), fill=(120, 120, 120), width=1)

        # 7) تبدیل به Base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        # 8) ذخیره در DB
        Captcha.objects.create(captcha_id=captcha_id, answer=text)

        return Response({
            "captcha_id": captcha_id,
            "image_base64": "data:image/png;base64," + image_base64
        })


class CaptchaVerify(APIView):
    def post(self, request):
        captcha_id = request.data.get("captcha_id")
        answer = request.data.get("answer", "").strip().upper()

        try:
            c = Captcha.objects.get(captcha_id=captcha_id)
        except Captcha.DoesNotExist:
            return Response({"detail": "کپچا معتبر نیست"}, status=400)

        if c.is_expired():
            c.delete()
            return Response({"detail": "کپچا منقضی شده است"}, status=400)

        if c.answer == answer:
            c.delete()
            return Response({"detail": "کپچا صحیح است"})
        else:
            return Response({"detail": "کپچا اشتباه وارد شده است"}, status=400)
