#!/usr/bin/env python
"""
اسکریپت ایمپورت ویدیوها از فایل pings.json به مدل Video
این اسکریپت داده‌های ویدیو را از فایل JSON خوانده و در دیتابیس ذخیره می‌کند
"""

import os
import sys
import json
import django
from pathlib import Path

# تنظیم Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from video.models import Video, VideoCategory, VideoTag, VideoCategoryRelation, VideoTagRelation
from django.core.files import File
from django.core.files.storage import default_storage
from django.utils import timezone
import logging

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()


class VideoImporter:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.default_user_id = 15  # کاربر پیش‌فرض از JSON
        self.default_category = None
        self.default_tag = None

    def load_json_data(self):
        """بارگذاری داده‌های JSON"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"تعداد {len(data)} ویدیو از فایل JSON بارگذاری شد")
            return data
        except FileNotFoundError:
            logger.error(f"فایل {self.json_file_path} یافت نشد")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"خطا در خواندن فایل JSON: {e}")
            return None

    def get_or_create_default_user(self):
        """دریافت یا ایجاد کاربر پیش‌فرض"""
        try:
            user = User.objects.get(id=self.default_user_id)
            logger.info(f"کاربر با ID {self.default_user_id} یافت شد: {user.username}")
            return user
        except User.DoesNotExist:
            logger.warning(f"کاربر با ID {self.default_user_id} یافت نشد. ایجاد کاربر جدید...")
            user = User.objects.create_user(
                username=f'user_{self.default_user_id}',
                email=f'user{self.default_user_id}@example.com',
                first_name='کاربر',
                last_name='پیش‌فرض'
            )
            logger.info(f"کاربر جدید ایجاد شد: {user.username}")
            return user

    def get_or_create_default_category(self):
        """دریافت یا ایجاد دسته‌بندی پیش‌فرض"""
        if not self.default_category:
            category_name = "ویدیوهای ایمپورت شده"
            self.default_category, created = VideoCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': 'دسته‌بندی پیش‌فرض برای ویدیوهای ایمپورت شده از JSON'}
            )
            if created:
                logger.info(f"دسته‌بندی جدید ایجاد شد: {category_name}")
            else:
                logger.info(f"دسته‌بندی موجود استفاده شد: {category_name}")
        return self.default_category

    def get_or_create_default_tag(self):
        """دریافت یا ایجاد تگ پیش‌فرض"""
        if not self.default_tag:
            tag_name = "ایمپورت شده"
            self.default_tag, created = VideoTag.objects.get_or_create(name=tag_name)
            if created:
                logger.info(f"تگ جدید ایجاد شد: {tag_name}")
            else:
                logger.info(f"تگ موجود استفاده شد: {tag_name}")
        return self.default_tag

    def clean_html_content(self, html_content):
        """پاک کردن تگ‌های HTML از محتوا"""
        import re
        if not html_content:
            return ""

        # حذف تگ‌های HTML
        clean_text = re.sub(r'<[^>]+>', '', html_content)
        # حذف کاراکترهای اضافی
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text

    def handle_video_file(self, video_data):
        """مدیریت فایل ویدیو - فقط مسیر را برمی‌گرداند"""
        video_file_path = video_data.get('file')
        if not video_file_path:
            logger.warning("فایل ویدیو یافت نشد")
            return None

        # فقط مسیر فایل را برمی‌گردانیم بدون بررسی وجود فایل
        logger.info(f"مسیر فایل ویدیو: {video_file_path}")
        return video_file_path

    def handle_poster_image(self, video_data):
        """مدیریت تصویر پوستر - فقط مسیر را برمی‌گرداند"""
        poster_path = video_data.get('poster')
        thumbnail = video_data.get('thumbnail')

        # اولویت با poster، اگر نبود از thumbnail استفاده کن
        image_path = poster_path or thumbnail

        if not image_path:
            logger.warning("تصویر پوستر یافت نشد")
            return None

        # اگر thumbnail است، مسیر کامل بساز
        if image_path == thumbnail and not image_path.startswith('/'):
            image_path = f"/media/{image_path}"

        # فقط مسیر تصویر را برمی‌گردانیم بدون بررسی وجود فایل
        logger.info(f"مسیر تصویر پوستر: {image_path}")
        return image_path

    def import_video(self, video_data):
        """ایمپورت یک ویدیو"""
        try:
            # بررسی وجود ویدیو با همین عنوان
            title = video_data.get('title', 'بدون عنوان')
            if Video.objects.filter(title=title).exists():
                logger.warning(f"ویدیو با عنوان '{title}' قبلاً وجود دارد. رد شد.")
                return False

            # ایجاد ویدیو
            video = Video()
            video.title = title
            video.description = self.clean_html_content(video_data.get('body', ''))
            video.uploader = self.get_or_create_default_user()
            video.is_published = True
            video.view_count = 0
            video.like_count = 0
            video.comment_count = 0

            # مدیریت فایل ویدیو
            video_file_path = self.handle_video_file(video_data)
            if video_file_path:
                # فقط مسیر فایل را ذخیره می‌کنیم
                video.video_file = video_file_path
            else:
                logger.warning(f"فایل ویدیو برای '{title}' یافت نشد")
                return False

            # مدیریت تصویر پوستر
            poster_path = self.handle_poster_image(video_data)
            if poster_path:
                # فقط مسیر تصویر را ذخیره می‌کنیم
                video.poster = poster_path
            else:
                logger.warning(f"تصویر پوستر برای '{title}' یافت نشد")
                return False

            # ذخیره ویدیو
            video.save()
            logger.info(f"ویدیو '{title}' با موفقیت ایجاد شد (ID: {video.id})")

            # اضافه کردن به دسته‌بندی پیش‌فرض
            category = self.get_or_create_default_category()
            VideoCategoryRelation.objects.get_or_create(
                video=video,
                category=category
            )

            # اضافه کردن تگ پیش‌فرض
            tag = self.get_or_create_default_tag()
            VideoTagRelation.objects.get_or_create(
                video=video,
                tag=tag
            )

            return True

        except Exception as e:
            logger.error(f"خطا در ایمپورت ویدیو '{title}': {e}")
            return False

    def import_all_videos(self):
        """ایمپورت تمام ویدیوها"""
        data = self.load_json_data()
        if not data:
            return False

        success_count = 0
        error_count = 0

        logger.info("شروع فرآیند ایمپورت ویدیوها...")

        for i, video_data in enumerate(data, 1):
            logger.info(f"پردازش ویدیو {i}/{len(data)}: {video_data.get('title', 'بدون عنوان')}")

            if self.import_video(video_data):
                success_count += 1
            else:
                error_count += 1

        logger.info(f"فرآیند ایمپورت تکمیل شد. موفق: {success_count}, خطا: {error_count}")
        return success_count > 0


def main():
    """تابع اصلی"""
    json_file_path = BASE_DIR / 'pings.json'

    if not os.path.exists(json_file_path):
        logger.error(f"فایل {json_file_path} یافت نشد")
        return

    importer = VideoImporter(json_file_path)
    success = importer.import_all_videos()

    if success:
        logger.info("ایمپورت ویدیوها با موفقیت انجام شد")
    else:
        logger.error("ایمپورت ویدیوها با خطا مواجه شد")


if __name__ == '__main__':
    main()
