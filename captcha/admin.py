from django.contrib import admin

import captcha
from captcha.models import Captcha
# Register your models here.
admin.site.register(Captcha)
