from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAllowedIP(BasePermission):
    """فقط درخواست‌هایی که از IPهای مجاز (مثلاً برای API دانلود مدیا) باشند قبول می‌شوند."""
    def has_permission(self, request, view):
        allowed = getattr(settings, 'MEDIA_DOWNLOAD_ALLOWED_IPS', ())
        if not allowed:
            return True  # اگر تنظیم نشده، محدودیت اعمال نشود
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            client_ip = x_forwarded.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR', '')
        return client_ip in allowed


class IsFlowAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='flow').exists()


class IsProclamationAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='proclamation').exists()


class IsInvoiceCollector(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['invoice-registrar', 'invoice-confirm1', 'invoice-confirm3', 'invoice-accept', 'invoice-deposit']).exists() or request.user.is_head_of_unit


class IsPmUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='pm').exists()


class IsHrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='hr').exists()


class IsRoomCateringAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='room_catering').exists()


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.post.is_manager


class HasPost(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.post)
