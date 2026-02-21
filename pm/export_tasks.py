from core.models import User, Notification
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from openpyxl.worksheet.table import Table, TableStyleInfo
from django.contrib.auth.mixins import UserPassesTestMixin
from pm.models import Task, Job, JobAppendix, JobChat, Approval, Session, Tag, FlowPatternType
from rest_framework.generics import GenericAPIView, ListAPIView, get_object_or_404, RetrieveAPIView, UpdateAPIView, \
    DestroyAPIView, CreateAPIView

from django.db import DataError
from django.core.exceptions import ValidationError
from core.serializers import SerUser
import jdatetime


def get_today(request):
    return HttpResponse(str(jdatetime.datetime.now().date()))


def is_senior_manager(manager_user, target_user):
    """
    بررسی می‌کند که آیا کاربر manager_user مدیر ارشد کاربر target_user است یا نه
    این تابع سلسله مراتب را تا 3 سطح بالا بررسی می‌کند
    """
    if not manager_user.post or not target_user.post:
        print("00000000000000000000000000000")
        return False

    # چک می‌کنیم که آیا target_user در زیرمجموعه manager_user است
    # بررسی سطح 1: مدیر مستقیم
    if target_user.post.parent == manager_user.post:
        print("44444444444444444444444444444444444")
        return True

    # بررسی سطح 2: مدیر غیرمستقیم (2 سطح بالا)
    if target_user.post.parent and target_user.post.parent.parent == manager_user.post:
        print("5555555555555555555555555555")
        return True

    # بررسی سطح 3: مدیر غیرمستقیم (3 سطح بالا)
    if (target_user.post.parent and
        target_user.post.parent.parent and
        target_user.post.parent.parent.parent == manager_user.post):
        print("666666666666666666666666666666")
        return True

    return False



ahadi = User.objects.get(pk=1)
javdani = User.objects.get(pk=9)
mazy = User.objects.get(pk=9)


def get_manager(user):
    post = user.post
    while post.parent:
        if post.parent.title == 'رئیس مرکز':
            break
        post = post.parent

    manager = User.objects.get(post=post)
    return manager

