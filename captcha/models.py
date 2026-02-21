from django.db import models
from django.utils import timezone
from datetime import timedelta


class Captcha(models.Model):
    captcha_id = models.CharField(max_length=64, unique=True)
    answer = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)  # اعتبار 2 دقیقه