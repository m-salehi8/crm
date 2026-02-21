import os
import jdatetime
from django.conf import settings
from core.models import User
from django.db import models
from django.contrib import admin
from core.choices import RoomType
from django.dispatch import receiver
from django_jalali.db import models as jmodels
from django.db.models.signals import pre_delete
from django.core.files.storage import default_storage
from rest_framework.exceptions import ValidationError


class Room(models.Model):
    class Meta:
        verbose_name = 'اتاق گفتگو'
        verbose_name_plural = 'اتاق گفتگو'
        ordering = ['id']

    title = models.CharField(max_length=50, null=True, blank=True, verbose_name='عنوان')
    logo = models.ImageField(null=True, blank=True, upload_to='room_logo', verbose_name='لوگو')
    type = models.CharField(max_length=7, choices=RoomType, verbose_name='نوع')
    bio = models.TextField(null=True, blank=True, verbose_name='معرفی')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    def __str__(self):
        return self.title or f'Room {self.id}'

    @property
    @admin.display(description='تعداد عضو')
    def member_count(self):
        return self.members.count()

    @property
    def logo_url(self):
        return self.logo.name if hasattr(self, 'logo') else None

    def clean(self):
        if self.type != 'chat' and self.title is None:
            raise ValidationError('گروه و کانال باید نام داشته باشند')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Member(models.Model):
    class Meta:
        verbose_name = 'اتاق گفتگو - اعضا'
        verbose_name_plural = 'اتاق گفتگو - اعضا'
        ordering = ['-is_pinned', '-is_owner', '-is_manager', 'id']
        unique_together = ['room', 'user']

    user = models.ForeignKey(to=User, on_delete=models.PROTECT, verbose_name='کاربر')
    room = models.ForeignKey(to=Room, on_delete=models.CASCADE, related_name='members', verbose_name='اتاق گفتگو')
    is_owner = models.BooleanField(default=False, verbose_name='مالک گروه است')
    is_manager = models.BooleanField(default=False, verbose_name='مدیر گروه است')
    is_mute = models.BooleanField(default=False, verbose_name='یادآور خاموش است')
    is_pinned = models.BooleanField(default=False, verbose_name='سنجاق شده')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    my_last_seen_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان آخرین مشاهده من')

    def __str__(self):
        return self.user.get_full_name()

    @property
    def others_last_seen_time(self):
        last_member = self.room.members.exclude(user=self.user).order_by('my_last_seen_time').last()
        return str(last_member.my_last_seen_time) if last_member else None

    @property
    def last_chat_time(self):
        last_chat = self.room.chats.first()
        return str(last_chat.create_time) if last_chat else str(self.create_time)

    @property
    def unseen_count(self):
        return self.room.chats.filter(create_time__gt=self.my_last_seen_time).count()


class Chat(models.Model):
    class Meta:
        verbose_name = 'گفتگو'
        verbose_name_plural = 'گفتگو'
        ordering = ['-id']

    room = models.ForeignKey(to=Room, on_delete=models.CASCADE, related_name='chats', verbose_name='اتاق گفتگو')
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='chats', verbose_name='فرستنده')
    ff = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ff_chat_set', verbose_name='بازارسال شده از ')
    body = models.TextField(null=True, blank=True, verbose_name='متن پیام')
    file = models.FileField(upload_to='chat_files', null=True, blank=True, verbose_name='فایل')
    parent = models.ForeignKey(to='self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='والد', help_text='برای چتهایی که پاسخ به چت دیگری هستند')
    create_time = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ارسال')
    modify_time = jmodels.jDateTimeField(auto_now=True, verbose_name='زمان ویرایش')

    def __str__(self):
        return self.body

    @property
    def file_url(self):
        return self.file.name if self.file else None

    @property
    def human_readable_time(self):
        if self.create_time.date() == jdatetime.datetime.now().date():
            return str(self.create_time)[11:16]
        if self.create_time.date() == jdatetime.datetime.now().date() - jdatetime.timedelta(days=1):
            return 'دیروز'
        if self.create_time.date() < jdatetime.datetime.now().date() - jdatetime.timedelta(days=6):
            return self.create_time.strftime('%d %B')
        return self.create_time.strftime('%A')

    @property
    def updated(self):
        return (self.modify_time - self.create_time).seconds > 1


@receiver(signal=pre_delete, sender=Chat)
def skip_cleanup_for_chat(sender, instance, **kwargs):
    if instance.file:
        if Chat.objects.exclude(id=instance.id).filter(file=instance.file).exists():
            instance.file.storage.delete = lambda *args, **kwargs: None
        else:
            file_path = os.path.join(settings.MEDIA_ROOT, instance.file.name)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    pass
