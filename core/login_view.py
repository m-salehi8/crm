from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from core.models import UserAuthLog, User
import jdatetime


def get_ip(request):
    """گرفتن IP واقعی کاربر."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class LoginAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'detail': 'نام کاربری یا رمز اشتباه است'}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)

        ip = get_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        log = UserAuthLog()
        log.ip = ip
        log.user = user
        log.token = token.key
        log.user_agent = user_agent
        computer_ip = user.computer_ip()
        if computer_ip and ip != computer_ip:
            log.is_suspicious = True
        log.save()

        return Response({'token': token.key})


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # دریافت کلید توکن
        token_key = None
        if hasattr(request.auth, 'key'):
            token_key = request.auth.key
        else:
            try:
                token_key = request.user.auth_token.key
            except:
                pass

        # ثبت زمان خروج در لاگ
        if token_key:
            auth_log = UserAuthLog.objects.filter(
                user=request.user,
                token=token_key,
                is_login=True
            ).order_by('-login_at').first()

            if auth_log:
                auth_log.logout_at = jdatetime.datetime.now()
                auth_log.save()

        # حذف توکن
        try:
            request.user.auth_token.delete()
        except:
            pass

        return Response({'detail': 'با موفقیت خارج شدید'}, status=status.HTTP_200_OK)


class RecentLoginsAPIView(APIView):
    """API برای دریافت لیست لاگین‌های اخیر کاربر"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # دریافت لاگین‌های اخیر کاربر
        logs = UserAuthLog.objects.filter(user=request.user).order_by('-login_at')[:20]

        log_list = []
        for log in logs:
            log_list.append({
                'id': log.id,
                'login_at': log.login_at.strftime('%Y-%m-%d %H:%M:%S') if log.login_at else None,
                'logout_at': log.logout_at.strftime('%Y-%m-%d %H:%M:%S') if log.logout_at else None,
                'ip': log.ip,
                'user_agent': log.user_agent,
                'is_suspicious': log.is_suspicious,
                'is_active': log.logout_at ,  # هنوز لاگین است یا نه
            })

        return Response({
            'logs': log_list,
            'count': len(log_list)
        }, status=status.HTTP_200_OK)


class LogoutFromSystemAPIView(APIView):
    """API برای خروج از یک سیستم خاص (با استفاده از token یا log_id)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        log_id = request.data.get('log_id')
        token_key = request.data.get('token')

        if not log_id and not token_key:
            return Response(
                {'detail': 'لطفاً log_id یا token را ارسال کنید'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # پیدا کردن لاگ مربوطه
        if log_id:
            try:
                auth_log = UserAuthLog.objects.get(id=log_id, user=request.user)
                token_key = auth_log.token
            except UserAuthLog.DoesNotExist:
                return Response(
                    {'detail': 'لاگ مورد نظر یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            auth_log = UserAuthLog.objects.filter(
                user=request.user,
                token=token_key,
            ).order_by('-login_at').first()

            if not auth_log:
                return Response(
                    {'detail': 'لاگ مورد نظر یافت نشد'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # ثبت زمان خروج
        auth_log.logout_at = jdatetime.datetime.now()

        auth_log.save()

        # حذف توکن مربوطه
        try:
            token = Token.objects.get(key=token_key, user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass

        return Response({
            'detail': 'با موفقیت از سیستم خارج شدید',
            'log_id': auth_log.id
        }, status=status.HTTP_200_OK)