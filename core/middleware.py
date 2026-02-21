from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.utils.timezone import now
from rest_framework.authtoken.models import Token
from core.models import UserActivityLog


class UserActivityLogMiddleware(MiddlewareMixin):
    """Middleware برای ثبت لاگ فقط در صورت وجود Token معتبر."""

    def process_response(self, request, response):
        token = self._get_token(request)
        if not token:
            # هیچ توکنی در هدر وجود ندارد → لاگی ثبت نمی‌شود
            return response

        # بررسی توکن
        token_obj = Token.objects.select_related('user').filter(key=token).first()
        if not token_obj:
            return response

        user = token_obj.user
        if not getattr(user, 'is_authenticated', False):
            return response

        # جزئیات درخواست
        path = request.path
        method = request.method
        status_code = getattr(response, 'status_code', 0)

        # اطلاعات view
        view_name, app_name = '', ''
        try:
            resolver_match = resolve(path)
            view_name = resolver_match.view_name or ''
            app_name = resolver_match.app_name or ''
        except Exception:
            pass

        ip_address = self.get_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        # ثبت در دیتابیس
        try:
            UserActivityLog.objects.create(
                user=user,
                path=path,
                method=method,
                session_key=token,
                status_code=status_code,
                view_name=view_name,
                app_name=app_name,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=now(),
            )
        except Exception as e:
            print(f"[UserActivityLogMiddleware] Log error: {e}")

        return response

    def _get_token(self, request):
        """استخراج Token از هدر Authorization."""
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()
        if len(auth) == 2 and auth[0].lower() == 'token':
            return auth[1]
        return None

    def get_ip(self, request):
        """گرفتن IP واقعی کاربر."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
