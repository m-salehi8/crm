import random
import subprocess
from rest_framework.views import APIView
from .gsm import send_sms
from .serializers import *
from weasyprint import HTML
from core.permissions import *
from django.conf import settings
from rest_framework import status
from django.http import HttpResponse, FileResponse
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.authtoken.models import Token
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, GenericAPIView, get_object_or_404, DestroyAPIView, RetrieveAPIView
from django.contrib.auth import authenticate
from django.db import models
from django.db.models import Q
from rest_framework import status
from django.db.models import OuterRef, Exists
from video.models import Video, VideoView

from django.db.models import Case, When, Value, IntegerField

class DashboardSliderAPIView(ListAPIView):
    serializer_class = SerProclamationList
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context


    def get_queryset(self):
        base_qs = Proclamation.objects.all().order_by('-id')

        final_ids = []

        # ---------- جایگاه اول ----------
        first = base_qs.filter(main_page_order=1).first()
        if not first:
            first = base_qs.first()

        if first:
            final_ids.append(first.pk)

        # ---------- جایگاه دوم ----------
        second = base_qs.filter(main_page_order=2).exclude(
            pk__in=final_ids
        ).first()

        if not second:
            second = base_qs.exclude(pk__in=final_ids).first()

        if second:
            final_ids.append(second.pk)

        # ---------- بقیه فقط order دارها (>=3) ----------
        ordered_rest = (
            Proclamation.objects
            .filter(main_page_order__gte=3)
            .exclude(pk__in=final_ids)
            .order_by('main_page_order')
        )

        final_ids.extend(list(ordered_rest.values_list('pk', flat=True)))

        # برگردوندن به ترتیب ساخته شده
        preserved = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(final_ids)],
            output_field=IntegerField()
        )

        return Proclamation.objects.filter(pk__in=final_ids).order_by(preserved)


class DashboardAPI(GenericAPIView):
    """API برای دریافت اطلاعات داشبورد"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = jdatetime.datetime.now().date()

        # Import models
        from pm.models import Task, Job, Session, Flow, Node
        from chat.models import Member, Chat, Room
        from prj.models import Project, Phase

        # آخرین وظایف
        latest_tasks = Task.objects.filter(user=user, job__archive=False).select_related('job').order_by(
            '-create_time')[:5]
        latest_tasks_data = []
        for task in latest_tasks:
            latest_tasks_data.append({
                'id': task.id,
                'title': task.job.title,
                'date': task.job.create_time.strftime('%Y-%m-%d'),
                'is_urgent': task.job.urgency == 3,
                'status': task.job.status,
                'deadline': task.job.deadline.strftime('%Y-%m-%d') if task.job.deadline else None
            })

        # آمار وظایف
        user_tasks = Task.objects.filter(user=user, job__archive=False)
        total_tasks = user_tasks.count()
        open_tasks = user_tasks.filter(job__status__in=['todo', 'doing']).count()
        done_tasks = user_tasks.filter(job__status='done').count()

        # محاسبه درصد پیشرفت
        progress_percentage = 0
        if total_tasks > 0:
            progress_percentage = round((done_tasks / total_tasks) * 100)

        # وظایف نزدیک ددلاین (3 روز آینده)
        near_deadline_tasks = user_tasks.filter(
            job__deadline__lte=today + jdatetime.timedelta(days=3),
            job__deadline__gte=today,
            job__status__in=['todo', 'doing']
        ).count()

        # وظایف گذشته
        overdue_tasks = user_tasks.filter(
            job__deadline__lt=today,
            job__status__in=['todo', 'doing']
        ).count()

        # آخرین گفتگوها - فقط پیام‌هایی که برای کاربر ارسال شده
        user_members = Member.objects.filter(user=user).select_related('room')
        latest_chats = []
        total_unread = 0

        # دریافت آخرین پیام از هر اتاق گفتگو که برای کاربر ارسال شده (نه توسط خودش)
        room_ids = list(Member.objects.filter(user=user).values_list('room_id', flat=True))
        chats_qs = (Chat.objects
                    .filter(room_id__in=room_ids)
                    .exclude(user=user)
                    .select_related('user', 'room')
                    .order_by('-create_time'))
        latest_by_room = {}
        for chat in chats_qs:
            rid = chat.room_id
            if rid not in latest_by_room:
                latest_by_room[rid] = chat
            if len(latest_by_room) >= 3:
                break
        latest_messages = list(latest_by_room.values())

        for chat in latest_messages:
            latest_chats.append({
                'room_title': chat.room.title or f'گفتگو {chat.room.id}',
                'last_message': chat.body[:100] + '...' if chat.body and len(chat.body) > 100 else chat.body,
                'time': chat.create_time.strftime('%Y-%m-%d %H:%M'),
                'sender': chat.user.get_full_name(),
                'sender_photo': chat.user.photo_url
            })

        # محاسبه تعداد پیام‌های خوانده نشده
        for member in user_members:
            total_unread += member.unseen_count

        # تعداد کل گفتگوها
        total_chats = user_members.count()

        # تعداد کاربران آنلاین (لاگین های اخیر - 30 دقیقه گذشته)
        import datetime
        recent_login_time = datetime.datetime.now() - datetime.timedelta(minutes=30)
        online_users = Token.objects.filter(
            created__gte=recent_login_time
        ).values_list('user_id', flat=True).distinct().count()

        # رویدادهای آینده
        # جلسات امروز
        today_sessions = Session.objects.filter(
            Q(members__in=[user]) | Q(user=user),
            date=today
        ).distinct().count()

        # جلسات هفته
        week_start = today - jdatetime.timedelta(days=today.weekday())
        week_end = week_start + jdatetime.timedelta(days=6)
        week_sessions = Session.objects.filter(
            Q(members__in=[user]) | Q(user=user),
            date__gte=week_start,
            date__lte=week_end
        ).distinct().count()

        # جلسات ماه
        month_start = today.replace(day=1)
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - jdatetime.timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - jdatetime.timedelta(days=1)

        month_sessions = Session.objects.filter(
            Q(members__in=[user]) | Q(user=user),
            date__gte=month_start,
            date__lte=month_end
        ).distinct().count()

        # سه جلسه آینده
        upcoming_sessions = Session.objects.filter(
            Q(members__in=[user]) | Q(user=user),
            date__gte=today
        ).distinct().order_by('date', 'start')[:3]

        upcoming_sessions_data = []
        for session in upcoming_sessions:
            upcoming_sessions_data.append({
                'id': session.id,
                'title': session.title,
                'date': session.date.strftime('%Y-%m-%d'),
                'time': str(session.start)[:5] if session.start else None,
                'room': session.room.title if session.room else None
            })

        # فرایندهای اخیر
        user_flows = Flow.objects.filter(user=user)
        unseen_processes = Node.objects.filter(
            user=user,
            seen_time__isnull=True
        ).count()

        pending_processes = Node.objects.filter(
            user=user,
            seen_time__isnull=False,
            done_time__isnull=True
        ).count()

        completed_processes = Node.objects.filter(
            user=user,
            done_time__isnull=False
        ).count()

        # سه فرایند آینده - مرتب شده از جدیدترین به قدیمی‌ترین
        upcoming_processes = Node.objects.filter(
            user=user,
            done_time__isnull=True
        ).select_related('flow', 'flow__flow_pattern').order_by('-create_time')[:3]

        upcoming_processes_data = []
        for process in upcoming_processes:
            upcoming_processes_data.append({
                'id': process.id,
                'title': process.flow.flow_pattern.title,
                'date': process.create_time.strftime('%Y-%m-%d'),
                'department': process.flow.user.post.unit.title if process.flow.user.post else 'نامشخص'
            })

        # جمع‌آوری تمام داده‌ها
        dashboard_data = {
            'latest_tasks': {
                'list': latest_tasks_data,
                'progress_percentage': progress_percentage,
                'open_tasks': open_tasks,
                'done_tasks': done_tasks,
                'near_deadline_tasks': near_deadline_tasks,
                'overdue_tasks': overdue_tasks
            },
            'latest_conversations': {
                'list': latest_chats,
                'unread_count': total_unread,
                'total_chats': total_chats,
                'online_users': online_users
            },
            'upcoming_events': {
                'today_sessions': today_sessions,
                'week_sessions': week_sessions,
                'month_sessions': month_sessions,
                'upcoming_sessions': upcoming_sessions_data
            },
            'recent_processes': {
                'unseen_count': unseen_processes,
                'pending_count': pending_processes,
                'completed_count': completed_processes,
                'upcoming_processes': upcoming_processes_data
            }
        }

        return Response(data=dashboard_data)


class GetUser(RetrieveAPIView):
    serializer_class = SerUser

    def get_object(self):
        return self.request.user


class ChangePassword(GenericAPIView):
    def post(self, request):
        if request.user.check_password(request.data['old']):
            request.user.set_password(request.data['new'])
            request.user.save()
            return Response(data='رمز عبور شما تغییر کرد')
        return Response(data='رمز وارد شده صحیح نیست', status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordV2(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(ser.validated_data['new_password'])
        request.user.save()
        return Response(data='رمز عبور شما تغییر کرد')

class ResetPassword(GenericAPIView):
    def post(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        profile = user.profile
        if request.data['step'] == '1':
            profile.sms = random.randint(1001, 9999)
            profile.sms_sent_time = jdatetime.datetime.now()
            profile.save()
            send_sms(mobile=user.mobile, text=f'کد احراز هویت پرتال:\n{profile.sms}', user_id=user.id)
            return Response(data={'mobile': f'{user.mobile[0:4]}*****{user.mobile[-2:]}'})
        if request.data['step'] == '2':
            if profile.sms == request.data['code'] and not profile.sms_expired:
                return Response(data=user.get_full_name())
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        if request.data['step'] == '3':
            user.set_password(request.data['password'])
            user.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(data={'token': token.key})
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserPhotoUpdate(GenericAPIView):
    # noinspection PyMethodMayBeStatic
    def post(self, request):
        user = request.user
        user.photo = request.data['photo']
        user.save()
        return Response(data={'photo_url': user.photo_url, 'thumbnail_url': user.thumbnail_url})


class DepartmentList(ListAPIView):
    queryset = Unit.objects.filter(models.Q(parent_id=1) | models.Q(parent=None))
    serializer_class = SerDepartmentList


class ProclamationList(ListAPIView):
    serializer_class = SerProclamationList
    #queryset = Proclamation.objects.filter(Q(expire_date=None) | Q(expire_date__gte=jdatetime.datetime.now().date()))#.order_by('main_page_order')
    def get_queryset(self):
        # اطلاعیه‌های با تاریخ انقضا
        base_queryset = Proclamation.objects.filter(
            Q(expire_date=None) | Q(expire_date__gte=jdatetime.datetime.now().date()))

        # پنج اطلاعیه اول که نوع "اطلاعیه" دارند و عکس دارند
        first_five_with_image = base_queryset.filter(type='اطلاعیه', poster__isnull=False).order_by('-id')[:5]

        # بقیه اطلاعیه‌ها (بدون محدودیت عکس)
        remaining = base_queryset.exclude(id__in=first_five_with_image.values_list('id', flat=True))

        # ترکیب کردن و مرتب کردن
        return (first_five_with_image | remaining).order_by('-id')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user'] = self.request.user
        return context


class ProclamationDetail(RetrieveAPIView):
    serializer_class = SerProclamationDetail

    def get_object(self):
        proclamation = Proclamation.objects.get(pk=self.kwargs['pk'])
        proclamation.increment_view_count(self.request.user)
        return proclamation


class ProclamationTypeList(GenericAPIView):
    def get(self, request):
        if not request.user.groups.filter(name='proclamation').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        data = ['اطلاعیه']
        if request.user.groups.filter(name='proclamation-type-rule').exists():
            data.append('آیین‌نامه')
        if request.user.groups.filter(name='proclamation-type-hr').exists():
            data.append('سرمایه انسانی')
        if request.user.groups.filter(name='proclamation-type-news').exists():
            data.append('اخبار فضای مجازی')
            data.append('درنگی نورانی')
        if request.user.groups.filter(name='proclamation-type-security').exists():
            data.append('ضوابط حراست')
        if request.user.groups.filter(name='proclamation-type-session').exists():
            data.append('محفل تخصصی')
        if request.user.groups.filter(name='proclamation-type-ping').exists():
            data.append('پینگ')
        if request.user.groups.filter(name='proclamation-type-media').exists():
            data.append('فرانما')
        if request.user.groups.filter(name='proclamation-type-it').exists():
            data.append('فناوری اطلاعات')
        return Response(data=data)


class ProclamationManageList(ListAPIView):
    permission_classes = [IsProclamationAdmin]
    serializer_class = SerProclamationManage
    pagination_class = HdPagination
    filter_backends = [SearchFilter]
    search_fields = ['title']

    def get_queryset(self):
        # حضرت جاودانی می‌خواهند همه اطلاعیه‌ها را ببینند!
        if self.request.user.username == 'javdani':
            return Proclamation.objects.all()
        return Proclamation.objects.filter(unit=self.request.user.post.unit)


class ProclamationRemove(DestroyAPIView):
    permission_classes = [IsProclamationAdmin]

    def get_queryset(self):
        return Proclamation.objects.filter(unit=self.request.user.post.unit)


class ProclamationAddOrUpdate(GenericAPIView):
    permission_classes = [IsProclamationAdmin]

    def post(self, request):
        if int(request.data['id']):
            # حضرت جاودانی می‌خواهند همه  اطلاعیه‌ها را ویرایش کنند!
            if self.request.user.username == 'javdani':
                proclamation = get_object_or_404(Proclamation, pk=request.data['id'])
            else:
                proclamation = get_object_or_404(Proclamation, pk=request.data['id'], unit=request.user.post.unit)
            proclamation.title = request.data['title']
            proclamation.type = request.data['type']
            proclamation.body = request.data['body']
            proclamation.save()
        else:
            proclamation = Proclamation.objects.create(user=request.user, unit=request.user.post.unit, type=request.data['type'], title=request.data['title'], body=request.data['body'])
        if 'display_duration' in request.data and request.data['display_duration']:
            proclamation.display_duration = int(request.data['display_duration']) or 30
            proclamation.expire_date = proclamation.create_time.date() + jdatetime.timedelta(days=int(request.data['display_duration']) or 30)
        else:
            proclamation.expire_date = None
            proclamation.display_duration = None
        proclamation.save()
        proclamation.gallery.exclude(id__in=request.data.getlist('gallery', [])).delete()
        for file in request.data.getlist('new_gallery', []):
            proclamation.gallery.create(file=file)
        proclamation.appendices.exclude(id__in=request.data.getlist('appendices', [])).delete()
        for item in zip(request.data.getlist('new_title', []), request.data.getlist('new_appendices', [])):
            proclamation.appendices.create(title=item[0], file=item[1])
        return Response(data=SerProclamationManage(proclamation).data)


class TellList(ListAPIView):
    serializer_class = SerTellList
    queryset = User.objects.select_related('post', 'post__unit', 'post__unit__parent').filter(Q(post__tell__isnull=False) | Q(post__tell_local__isnull=False)).order_by('last_name')


def backup_db():
    backup_path = os.path.join(settings.BACKUP_DIR, f'DB_{jdatetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.sql')
    env = {'PGPASSWORD': settings.DATABASES['default']['PASSWORD']}
    command = f'pg_dump -U {settings.DATABASES["default"]["USER"]} -d {settings.DATABASES["default"]["NAME"]} -f {backup_path}'
    subprocess.run(command, shell=True, env=env, check=True)


class MyColleagueList(ListAPIView):
    serializer_class = SerUserList

    def get_queryset(self):
        return User.objects.filter(Q(post__unit=self.request.user.post.unit) | Q(post__unit__parent=self.request.user.post.unit))


class AllUserList(ListAPIView):
    serializer_class = SerUserList
    queryset = User.objects.filter(post__isnull=False)


class MyRelatedUserList(ListAPIView):
    serializer_class = SerUserList

    def get_queryset(self):
        if self.request.user.groups.filter(name='can-refer-to-all').exists():
            return User.objects.filter(post__isnull=False)
        return User.objects.filter(post__unit=self.request.user.post.unit)


class AllUnitList(ListAPIView):
    serializer_class = SerUnitList

    def get_queryset(self):
        if self.request.user.groups.filter(name='supervisor').exists():
            return Unit.objects.all()
        if self.request.user.post.is_deputy:
            return Unit.objects.filter(Q(parent_id=self.request.user.post.unit_id) | Q(id=self.request.user.post.unit_id))
        if self.request.user.post.is_manager:
            return Unit.objects.filter(id=self.request.user.post.unit_id)
        return Unit.objects.filter(id=0)


class TreeChart(RetrieveAPIView):
    serializer_class = SerTreeChart

    def get_object(self):
        return Post.objects.filter(unit_id=self.kwargs['unit'], parent__unit_id__lt=self.kwargs['unit']).first()


class SetPageSize(GenericAPIView):
    def post(self, request):
        request.user.profile.page_size = int(request.data['size'])
        request.user.profile.save()
        return Response()


class SetNotificationSeen(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notification_item = get_object_or_404(Notification, id=request.data['id'], user=request.user)
        notification_item.seen_time = jdatetime.datetime.now()
        notification_item.save()
        return Response()


class RemoveAllNotifications(GenericAPIView):
    def post(self, request):
        request.user.notifications.filter(seen_time=None).update(seen_time=jdatetime.datetime.now())
        return Response()


class MyNotificationList(ListAPIView):
    serializer_class = SerNotification

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, seen_time=None)


class ThemeList(ListAPIView):
    serializer_class = SerThemeList
    queryset = Theme.objects.all()


class SetTheme(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if 'theme' in request.data:
            user.theme_id = request.data['theme']
            user.bg = None
            user.save()
            data = {'bg': user.theme.bg_url, 'main': user.theme.main, 'tint1': user.theme.tint1, 'tint2': user.theme.tint2, 'tint3': user.theme.tint3}
        else:
            user.theme = None
            user.bg = request.data['bg']
            user.save()
            data = {'bg': user.bg_url, 'main': user.main, 'tint1': user.tint1, 'tint2': user.tint2, 'tint3': user.tint3}
        return Response(data)


class SetMenuOrder(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.menu_order = request.data['menu_order']
        user.save()

        return Response('OK')


class SeenCountAPIView(APIView):
    def get(self, request):
        er = request.GET.get('er')
        if er:
            return Response({'error': er}, status=500)

        user = request.user
        today = jdatetime.datetime.now().date()

        # ---------- Proclamations ----------
        base_procs = Proclamation.objects.filter(
            Q(expire_date=None) | Q(expire_date__gte=today)
        )

        seen_subquery = ProclamationSeen.objects.filter(
            user=user,
            proclamation=OuterRef('pk')
        )

        procs = base_procs.annotate(
            seen=Exists(seen_subquery)
        ).filter(seen=False)

        counts = {
            "اطلاعیه": procs.filter(type="اطلاعیه").count(),
            "سرمایه انسانی": procs.filter(type="سرمایه انسانی").count(),
            "فناوری اطلاعات": procs.filter(type="فناوری اطلاعات").count(),
            "اخبار فضای مجازی": procs.filter(type="اخبار فضای مجازی").count(),
            "ضوابط حراست": procs.filter(type="ضوابط حراست").count(),
            "فرانما": procs.filter(type="فرانما").count(),
            "درنگی نورانی": procs.filter(type="درنگی نورانی").count(),
            "آیین‌نامه": procs.filter(type="آیین‌نامه").count(),
            "محفل تخصصی": procs.filter(type="محفل تخصصی").count(),
        }

        # ---------- Videos ----------
        video_seen_subquery = VideoView.objects.filter(
            user=user,
            video=OuterRef('pk')
        )

        unseen_videos_count = Video.objects.annotate(
            seen=Exists(video_seen_subquery)
        ).filter(seen=False).count()

        # ---------- Response (دقیقاً مثل قبل) ----------
        res = {
            "اطلاعیه": counts["اطلاعیه"],
            "سرمایه انسانی": counts["سرمایه انسانی"],
            "فناوری اطلاعات": counts["فناوری اطلاعات"],
            "اخبار فضای مجازی": counts["اخبار فضای مجازی"],
            "پینگ": unseen_videos_count,
            "ضوابط حراست": counts["ضوابط حراست"],
            "فرانما": counts["فرانما"],
            "محفل تخصصی": counts["محفل تخصصی"],
            "درنگی نورانی": counts["درنگی نورانی"],
            "آیین‌نامه": counts["آیین‌نامه"],
        }

        return Response(res)


class SmsVerifyWebhookApi(APIView):
    def post(self, request):
        sms_id = request.data.get('sms_id', None)
        sms = SMS.objects.filter(token=sms_id).first()
        if sms:
            sms.status = 'sent'
            sms.save()
        return Response({'status': 'ok'})


class LoginThemeApi(APIView):
    def get(self, request):
        login_bg = Theme.objects.filter(id=5).first()
        if login_bg and login_bg.bg:
            return Response({'login_bg': login_bg.bg_url,})
        return Response({'login_bg': 'theme_bg/blue.png'})

    def post(self, request):
        login_bg = Theme.objects.filter(id=5).first()
        login_bg.bg = request.data['login_bg']
        login_bg.save()
        return Response({'login_bg': login_bg.bg_url,})


class MediaDownloadView(GenericAPIView):
    """
    API دانلود مدیا: فرانت آدرس فایل (نسبت به media) را می‌فرستد، پاسخ = فایل برای دانلود.
    GET: ?path=uploads/file.pdf
    POST: {"path": "uploads/file.pdf"}
    مسیر می‌تواند نسبی باشد (مثلاً uploads/doc.pdf) یا با پیشوند /media/ (خود /media/ حذف می‌شود).
    """
    permission_classes = [IsAuthenticated]

    def _get_path_param(self, request):
        if request.method == 'GET':
            return request.query_params.get('path') or request.GET.get('path')
        return (request.data.get('path') if hasattr(request.data, 'get') else None) or request.query_params.get('path')

    def get(self, request):
        return self._serve_file(request)

    def post(self, request):
        return self._serve_file(request)

    def _serve_file(self, request):
        import os
        path_param = self._get_path_param(request)
        if not path_param or not path_param.strip():
            return Response(
                {'detail': 'پارامتر path الزامی است.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        path_param = path_param.strip()
        # حذف پیشوند MEDIA_URL اگر کاربر آدرس کامل فرستاده
        if path_param.startswith(settings.MEDIA_URL):
            path_param = path_param[len(settings.MEDIA_URL):].lstrip('/')
        elif path_param.startswith('/'):
            path_param = path_param.lstrip('/')
        # محدود کردن به داخل MEDIA_ROOT و جلوگیری از path traversal
        media_root = os.path.abspath(settings.MEDIA_ROOT)
        full_path = os.path.normpath(os.path.join(media_root, path_param))
        if not full_path.startswith(media_root) or not os.path.isfile(full_path):
            return Response(
                {'detail': 'فایل یافت نشد یا دسترسی مجاز نیست.'},
                status=status.HTTP_404_NOT_FOUND
            )
        filename = os.path.basename(full_path)
        try:
            f = open(full_path, 'rb')
            return FileResponse(f, as_attachment=True, filename=filename)
        except OSError:
            return Response(
                {'detail': 'خطا در خواندن فایل.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
