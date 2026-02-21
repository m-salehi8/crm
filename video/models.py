from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_jalali.db import models as jmodels
from django_cleanup.signals import cleanup_pre_delete
from django.dispatch import receiver
from django_ckeditor_5.fields import CKEditor5Field
import os

User = get_user_model()


class Video(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان')
    description = CKEditor5Field(null=True, blank=True, verbose_name='توضیحات', config_name='extends')
    poster = models.ImageField(upload_to='video_posters/', verbose_name='پوستر', max_length=512, null=True, blank=True)
    video_file = models.FileField(upload_to='videos/', verbose_name='فایل ویدیو', max_length=512, null=True, blank=True)
    preview_file = models.FileField(upload_to='videos/previews/', verbose_name='پیش نمایش', max_length=512, null=True, blank=True)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='آپلود کننده')
    created_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_published = models.BooleanField(default=True, verbose_name='منتشر شده')
    view_count = models.PositiveIntegerField(default=0, verbose_name='تعداد بازدید')
    like_count = models.PositiveIntegerField(default=0, verbose_name='تعداد لایک')
    comment_count = models.PositiveIntegerField(default=0, verbose_name='تعداد کامنت')

    class Meta:
        verbose_name = 'ویدیو'
        verbose_name_plural = 'ویدیوها'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def increment_view_count(self, user):
        """افزایش تعداد بازدید برای کاربر مشخص (فقط یکبار برای هر کاربر)"""
        # بررسی اینکه آیا کاربر قبلاً این ویدیو را دیده است یا نه
        view, created = VideoView.objects.get_or_create(
            user=user,
            video=self,
            defaults={'viewed_at': timezone.now()}
        )

        # اگر بازدید جدید است، تعداد بازدید را افزایش بده
        if created:
            self.view_count += 1
            self.save(update_fields=['view_count'])

        return created

    def has_user_viewed(self, user):
        """بررسی اینکه آیا کاربر این ویدیو را دیده است یا نه"""
        return VideoView.objects.filter(user=user, video=self).exists()

    def get_viewed_users(self):
        """دریافت لیست کاربرانی که این ویدیو را دیده‌اند"""
        return VideoView.objects.filter(video=self).select_related('user')


    def update_like_count(self):
        """بروزرسانی تعداد لایک"""
        self.like_count = self.likes.count()
        self.save(update_fields=['like_count'])

    def update_comment_count(self):
        """بروزرسانی تعداد کامنت"""
        self.comment_count = self.comments.count()
        self.save(update_fields=['comment_count'])

    def video_file_url(self):
        return self.video_file.name if self.video_file else None


class VideoLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes', verbose_name='ویدیو')
    created_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ لایک')

    class Meta:
        verbose_name = 'لایک ویدیو'
        verbose_name_plural = 'لایک‌های ویدیو'
        unique_together = ['user', 'video']

    def __str__(self):
        return f'{self.user.username} liked {self.video.title}'


class VideoComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments', verbose_name='ویدیو')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies',
                               verbose_name='پاسخ به')
    content = models.TextField(verbose_name='متن کامنت')
    created_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ کامنت')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    is_approved = models.BooleanField(default=True, verbose_name='تایید شده')

    class Meta:
        verbose_name = 'کامنت ویدیو'
        verbose_name_plural = 'کامنت‌های ویدیو'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} commented on {self.video.title}'


class VideoCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام دسته‌بندی')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    created_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'دسته‌بندی ویدیو'
        verbose_name_plural = 'دسته‌بندی‌های ویدیو'

    def __str__(self):
        return self.name


class VideoTag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='نام تگ')
    created_at =jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'تگ ویدیو'
        verbose_name_plural = 'تگ‌های ویدیو'

    def __str__(self):
        return self.name


class VideoCategoryRelation(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, verbose_name='ویدیو')
    category = models.ForeignKey(VideoCategory, on_delete=models.CASCADE, verbose_name='دسته‌بندی')

    class Meta:
        unique_together = ['video', 'category']
        verbose_name = 'رابطه ویدیو و دسته‌بندی'
        verbose_name_plural = 'رابطه‌های ویدیو و دسته‌بندی'


class VideoTagRelation(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, verbose_name='ویدیو')
    tag = models.ForeignKey(VideoTag, on_delete=models.CASCADE, verbose_name='تگ')

    class Meta:
        unique_together = ['video', 'tag']
        verbose_name = 'رابطه ویدیو و تگ'
        verbose_name_plural = 'رابطه‌های ویدیو و تگ'


class VideoView(models.Model):
    """مدل برای ثبت بازدیدهای یکتا هر کاربر از ویدیو"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='views', verbose_name='ویدیو')
    viewed_at = jmodels.jDateTimeField(default=timezone.now, verbose_name='تاریخ بازدید')

    class Meta:
        verbose_name = 'بازدید ویدیو'
        verbose_name_plural = 'بازدیدهای ویدیو'
        unique_together = ['user', 'video']
        ordering = ['-viewed_at']

    def __str__(self):
        return f'{self.user.username} viewed {self.video.title}'


class VideoFileAppendix(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='files', verbose_name='ویدیو')
    title = models.CharField(max_length=200, verbose_name='عنوان')
    file = models.FileField(upload_to='videos/appendix/', verbose_name='فایل پیوست', max_length=512, null=True, blank=True)

    class Meta:
        verbose_name = 'فایل پیوست ویدیو'
        verbose_name_plural = 'فایل پیوست ویدیو'

    def __str__(self):
        return f"{self.title} for {self.video.title}"
