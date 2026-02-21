from django.contrib import admin
from django.urls import path
from .views import CaptchaGenerate, CaptchaVerify
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('captcha/', CaptchaGenerate.as_view()),
    path('captcha/verify/', CaptchaVerify.as_view()),
    path("about/", TemplateView.as_view(template_name="about.html")),
]