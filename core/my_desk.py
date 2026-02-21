from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import jdatetime
from datetime import timedelta, datetime, date as gdate
from django.db.models import Q
from rest_framework.views import APIView
from core.models import User

def to_jalali_str(dt, has_time=False):
    if not dt:
        return None
    try:
        # اگر از نوع jdatetime باشد، مستقیماً استفاده کن
        if isinstance(dt, jdatetime.datetime):
            if has_time:
                return dt.strftime('%Y-%m-%d %H:%M')
            else:
                return dt.date().strftime('%Y-%m-%d')
        if isinstance(dt, jdatetime.date):
            return dt.strftime('%Y-%m-%d')

        if isinstance(dt, str):
            # Try parsing iso format
            if 'T' in dt:
                dt = datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S')
            else:
                dt = datetime.strptime(dt, '%Y-%m-%d')
        if has_time:
            jdt = jdatetime.datetime.fromgregorian(datetime=dt)
            return jdt.strftime('%Y-%m-%d %H:%M')
        else:
            jdt = jdatetime.date.fromgregorian(date=dt.date() if hasattr(dt, 'date') else dt)
            return jdt.strftime('%Y-%m-%d')
    except Exception:
        return str(dt)


def to_datetime_obj(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, jdatetime.datetime):
        return value.togregorian()
    if isinstance(value, jdatetime.date):
        return value.togregorian()
    if isinstance(value, gdate):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None


def is_working_day(jdate):
    # پنجشنبه (4) و جمعه (5) جلالی تعطیل هستند
    weekday = jdate.weekday()  # 0..6
    return weekday not in [4, 5]


def count_working_days(start, end):
    # inclusive start, exclusive end
    days = 0
    d = start
    while d < end:
        if is_working_day(d):
            days += 1
        d += jdatetime.timedelta(days=1)
    return days


def add_working_days(start, extra_days):
    # اضافه کردن n روزکاری
    d = start
    added = 0
    while added < extra_days:
        d += jdatetime.timedelta(days=1)
        if is_working_day(d):
            added += 1
    return d


def next_working_day(date):
    d = date
    while not is_working_day(d):
        d += jdatetime.timedelta(days=1)
    return d


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mydesk_task_stats(request):
    """
    API برای کارت وظایف میزکار با فرمت خروجی دقیق موردنظر و recent_records
    """
    try:
        from pm.models import Task, Job
        try:
            from pm.models import TaskDowntime
            downtime_model_available = True
        except Exception:
            downtime_model_available = False
        user = request.user
        today = jdatetime.datetime.now().date()
        user_tasks = Task.objects.filter(user=user, job__archive=False).select_related('job')

        # ---- Near due: job deadline در 7 روزکاری آینده و در حالت todo/doing ----
        near_due = 0
        for t in user_tasks.filter(job__status__in=['todo', 'doing'], job__deadline__gte=today):
            jdl = t.job.deadline
            if jdl:
                work_days = 0
                d = today
                while d <= jdl and work_days < 8:  # تا 7 روزکاری آینده
                    if is_working_day(d):
                        work_days += 1
                    d += jdatetime.timedelta(days=1)
                if work_days <= 7:  # یعنی جزو 7 روزکاری آینده است
                    near_due += 1

        # ---- Delayed: مهلت گذشته (deadline<today) و هنوز todo/doing اما فقط اگر تاخیر واقعی وجود دارد ----
        delayed = 0
        for t in user_tasks.filter(job__status__in=['todo', 'doing'], job__deadline__lt=today):
            jdl = t.job.deadline
            if jdl:
                # محاسبه تعداد روزکاری بین deadline تا today
                missed = count_working_days(jdl + jdatetime.timedelta(days=1), today + jdatetime.timedelta(days=1))
                if missed > 0:
                    delayed += 1

        # ---- Done + نرخ انجام صحیح ----
        done_jobs = Job.objects.filter(tasks__user=user, status='done', archive=False, done_time__isnull=False,
                                       create_time__isnull=False).distinct()
        done_count = done_jobs.count()
        durations = []
        on_time_count = 0
        for job in done_jobs:
            if job.done_time and job.create_time:
                try:
                    done_d = jdatetime.datetime.fromgregorian(datetime=job.done_time).date()
                    created_d = jdatetime.datetime.fromgregorian(datetime=job.create_time).date()
                except Exception:
                    done_d = job.done_time.date()
                    created_d = job.create_time.date()
                # محاسبه مدت واقعی
                base_days = count_working_days(created_d, done_d) + (1 if is_working_day(done_d) else 0)
                durations.append(base_days)
                # مهلت گرفته و اولین روز کاری بعد
                if job.deadline:
                    try:
                        deadline_d = job.deadline
                        if not isinstance(deadline_d, jdatetime.date):
                            deadline_d = jdatetime.datetime.fromgregorian(datetime=job.deadline).date()
                    except Exception:
                        deadline_d = None
                    # اولین روزکاری >= deadline (ممکنه خود deadline تعطیل باشه):
                    limit = deadline_d if is_working_day(deadline_d) else next_working_day(deadline_d)
                    if done_d <= limit:
                        on_time_count += 1
        avg_completion_time_days = round(sum(durations) / len(durations), 1) if durations else 0.0
        on_time_completion_rate = round((on_time_count / done_count) * 100, 1) if done_count else 0.0

        # ---- Recent Records: آخرین وظایف کاربر ----
        # گرفتن آخرین Jobهای کاربر (بدون تکرار) بر اساس create_time
        recent_jobs = Job.objects.filter(
            tasks__user=user,
            archive=False
        ).distinct().order_by('-create_time', '-id')[:10]

        recent_records = []
        for job in recent_jobs:
            # تعیین progress بر اساس status
            if job.status == 'done':
                progress = 100
            elif job.status == 'doing':
                progress = 50  # مقدار پیش‌فرض برای doing
            else:  # todo
                progress = 0

            # تبدیل deadline
            deadline_str = to_jalali_str(job.deadline) if job.deadline else None

            # تبدیل done_time (بدون زمان)
            done_time_str = None
            if job.done_time:
                try:
                    # اگر jdatetime.datetime باشد، فقط تاریخ را بگیر
                    if isinstance(job.done_time, jdatetime.datetime):
                        done_time_str = to_jalali_str(job.done_time.date(), has_time=False)
                    elif isinstance(job.done_time, jdatetime.date):
                        done_time_str = to_jalali_str(job.done_time, has_time=False)
                    else:
                        # برای انواع دیگر، سعی کن تبدیل کن
                        done_time_str = to_jalali_str(job.done_time, has_time=False)
                except Exception:
                    done_time_str = None

            recent_records.append({
                "title": job.title,
                "status": job.status,
                "deadline": deadline_str,
                "done_time": done_time_str,
                "progress": progress
            })

        data = {
            "stats": {
                "near_due": near_due,
                "delayed": delayed,
                "avg_completion_time_days": avg_completion_time_days,
                "on_time_completion_rate": on_time_completion_rate
            },
            "chart": {
                "type": "progress",
                "data": {
                    "label": "نرخ انجام در موعد مقرر",
                    "value": on_time_completion_rate
                }
            },
            "recent_records": recent_records
        }
        data["url"] = "http://172.30.230.140/"
        return Response(data)
    except Exception as e:
        return Response({"error": str(e)})


class AttendanceCardViewV2(APIView):
    def get(self, request):
        # Convert attendance dates to jalali string
        sample_records = [
            {"date": to_jalali_str("2025-11-08"), "checkin": "08:10", "checkout": "16:20", "duration": 8.17},
            {"date": to_jalali_str("2025-11-07"), "checkin": "07:55", "checkout": "16:10", "duration": 8.25},
            {"date": to_jalali_str("2025-11-06"), "checkin": "08:05", "checkout": "16:30", "duration": 8.41},
            {"date": to_jalali_str("2025-11-05"), "checkin": "07:45", "checkout": "16:00", "duration": 8.25},
            {"date": to_jalali_str("2025-11-04"), "checkin": "08:12", "checkout": "16:20", "duration": 8.13},
            {"date": to_jalali_str("2025-11-03"), "checkin": "08:00", "checkout": "16:10", "duration": 8.17},
            {"date": to_jalali_str("2025-11-02"), "checkin": "07:55", "checkout": "16:00", "duration": 8.08},
            {"date": to_jalali_str("2025-11-01"), "checkin": "08:10", "checkout": "16:30", "duration": 8.33},
            {"date": to_jalali_str("2025-10-31"), "checkin": "07:58", "checkout": "16:05", "duration": 8.12},
            {"date": to_jalali_str("2025-10-30"), "checkin": "08:03", "checkout": "16:15", "duration": 8.20}
        ]
        data = {
            "stats": {
                "avg_checkin": "08:21",
                "avg_checkout": "16:45",
                "avg_presence_hours": 8.2,
                "incomplete_records": 2
            },
            "chart": {
                "type": "line",
                "data": {
                    "labels": [
                        "شنبه",
                        "یک‌شنبه",
                        "دوشنبه",
                        "سه‌شنبه",
                        "چهارشنبه",
                        "پنج‌شنبه",
                        "جمعه"
                    ],
                    "values": [7.5, 8.0, 7.8, 8.1, 8.3, 7.9, 8.2]
                }
            },
            "recent_records": sample_records
        }
        data["url"] = "http://172.30.230.140/"
        return Response(data)


class LoginActivityCardView(APIView):
    def get(self, request):
        from core.models import UserAuthLog, UserActivityLog
        from django.db.models import Count
        from collections import defaultdict

        user = request.user

        def fmt_rec(dt):
            return to_jalali_str(dt, has_time=True)

        def parse_user_agent(user_agent_str):
            """Parse user agent string to extract browser and OS info"""
            if not user_agent_str:
                return "Unknown / Unknown"

            ua_lower = user_agent_str.lower()

            # Detect browser
            browser = "Unknown"
            if "edg/" in ua_lower or "edge/" in ua_lower:
                browser = "Edge"
            elif "chrome" in ua_lower and "edg" not in ua_lower:
                browser = "Chrome"
            elif "firefox" in ua_lower:
                browser = "Firefox"
            elif "safari" in ua_lower and "chrome" not in ua_lower:
                browser = "Safari"
            elif "opera" in ua_lower or "opr/" in ua_lower:
                browser = "Opera"

            # Detect OS/Platform
            os_platform = "Unknown"
            if "android" in ua_lower:
                os_platform = "Android"
                if browser == "Unknown":
                    browser = "Mobile"
            elif "iphone" in ua_lower or "ipad" in ua_lower or "ipod" in ua_lower:
                os_platform = "iOS"
                if browser == "Unknown":
                    browser = "Mobile"
            elif "windows" in ua_lower:
                os_platform = "Windows"
            elif "mac" in ua_lower and "iphone" not in ua_lower and "ipad" not in ua_lower:
                os_platform = "Mac"
            elif "linux" in ua_lower and "android" not in ua_lower:
                os_platform = "Linux"

            return f"{browser} / {os_platform}"

        # Build last-10-days labels as "MonthName DD" in Jalali without year
        month_names_fa = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن',
                          'اسفند']
        today_j = jdatetime.datetime.now().date()
        labels_last_10_days = [
            f"{month_names_fa[(d.month - 1) % 12]} {d.day:02d}"
            for d in [today_j - jdatetime.timedelta(days=delta) for delta in range(9, -1, -1)]
        ]

        # Stats: last successful login
        last_login = UserAuthLog.objects.filter(user=user).order_by('-login_at').first()
        last_successful_login = fmt_rec(last_login.login_at) if last_login else None

        # Stats: total logins this week (from start of Jalali week)
        # Jalali week starts on Saturday (weekday 0)
        today_weekday = today_j.weekday()  # 0=Saturday, 1=Sunday, ..., 6=Friday
        week_start = today_j - jdatetime.timedelta(days=today_weekday)
        week_start_gregorian = week_start.togregorian()

        total_logins_this_week = UserAuthLog.objects.filter(
            user=user,
            login_at__gte=week_start_gregorian
        ).count()

        # Recent Records: last 10 logins
        recent_login_records = UserAuthLog.objects.filter(
            user=user
        ).order_by('-login_at')[:10]

        recent_logins = []
        for log in recent_login_records:
            device_info = parse_user_agent(log.user_agent)
            recent_logins.append({
                "datetime": fmt_rec(log.login_at),
                "ip": log.ip,
                "device": 'win'
            })

        # Chart Data: Activity by module for last 10 days
        # Initialize data structure for 10 days
        last_10_days_gregorian = [
            (today_j - jdatetime.timedelta(days=delta)).togregorian()
            for delta in range(9, -1, -1)
        ]

        # Module activity counters: {day_index: {module: count}}
        activity_by_day = defaultdict(lambda: defaultdict(int))

        # Query UserActivityLog for the last 10 days
        start_date = last_10_days_gregorian[0]
        end_date = last_10_days_gregorian[-1]

        activities = UserActivityLog.objects.filter(
            user=user,
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date,
            status_code__lt=400  # Only successful requests
        ).values('timestamp__date', 'app_name', 'view_name', 'path')

        # Map activities to modules
        for activity in activities:
            activity_date = activity['timestamp__date']
            app_name = activity.get('app_name', '')
            view_name = activity.get('view_name', '')
            path = activity.get('path', '')

            # Find which day this belongs to
            day_index = None
            for idx, greg_date in enumerate(last_10_days_gregorian):
                if activity_date == greg_date:
                    day_index = idx
                    break

            if day_index is None:
                continue

            # Map to module
            module = None
            if app_name == 'pm':
                # Check if it's task/job related or flow/node related
                if any(keyword in view_name.lower() for keyword in ['task', 'job']) or \
                        any(keyword in path.lower() for keyword in ['/task', '/job']):
                    module = 'وظایف'
                elif any(keyword in view_name.lower() for keyword in ['flow', 'node']) or \
                        any(keyword in path.lower() for keyword in ['/flow', '/node']):
                    module = 'فرایندها'
                elif any(keyword in view_name.lower() for keyword in ['session', 'calendar']) or \
                        any(keyword in path.lower() for keyword in ['/session', '/calendar']):
                    module = 'تقویم'
            elif app_name == 'chat':
                module = 'گفتگوها'
            elif app_name == 'cn':
                module = 'قراردادها'

            if module:
                activity_by_day[day_index][module] += 1

        # Build chart datasets
        modules = ['وظایف', 'فرایندها', 'گفتگوها', 'تقویم', 'قراردادها']
        datasets = []
        for module in modules:
            values = [activity_by_day[day_idx][module] for day_idx in range(10)]
            datasets.append({
                "label": module,
                "values": values
            })

        data = {
            "stats": {
                "last_successful_login": last_successful_login,
                "total_logins_this_week": total_logins_this_week
            },
            "chart": {
                "type": "Bar Race",
                "data": {
                    "labels": labels_last_10_days,
                    "datasets": datasets
                }
            },
            "recent_records": recent_logins,
            "actions": {
                "change_password": "/api/account/change-password/",
                "weekly_module_tasks": "/api/modules/weekly-tasks/"
            }
        }
        data["url"] = "http://172.30.230.140/"
        return Response(data)


class ApprovalsCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from pm.models import Approval, Job

        user = request.user
        today = jdatetime.datetime.now().date()

        approvals_qs = Approval.objects.filter(
            Q(members=user) | Q(session__user=user)
        ).select_related('session').distinct()
        approvals = list(approvals_qs)

        def to_jdate(value):
            if value is None:
                return None
            if isinstance(value, jdatetime.datetime):
                return value.date()
            if isinstance(value, jdatetime.date):
                return value
            if isinstance(value, datetime):
                return jdatetime.datetime.fromgregorian(datetime=value).date()
            if isinstance(value, gdate):
                return jdatetime.date.fromgregorian(date=value)
            return None

        delayed_count = sum(
            1 for approval in approvals
            if approval.deadline and approval.deadline < today and not approval.is_done
        )
        with_deadline_count = sum(
            1 for approval in approvals
            if approval.deadline and approval.deadline >= today and not approval.is_done
        )

        done_approvals = [approval for approval in approvals if approval.is_done and approval.deadline]
        job_map = {}
        if done_approvals:
            job_map = {
                job.approval_id: job
                for job in Job.objects.filter(approval__in=done_approvals, done_time__isnull=False)
            }

        on_time_total = 0
        on_time_done = 0
        for approval in done_approvals:
            job = job_map.get(approval.id)
            if not job or not job.done_time:
                continue
            done_date = to_jdate(job.done_time)
            deadline_date = to_jdate(approval.deadline)
            if not done_date or not deadline_date:
                continue
            on_time_total += 1
            if done_date <= deadline_date:
                on_time_done += 1

        completed_on_time_percent = round((on_time_done / on_time_total) * 100, 1) if on_time_total else 0.0

        recent_items = approvals_qs.order_by('-session__date', '-id')[:10]

        def determine_status(approval):
            if approval.is_done:
                return 'اقدام شده'
            if approval.deadline:
                if approval.deadline < today:
                    return 'دارای تأخیر'
                return 'دارای مهلت'
            return 'بدون مهلت'

        recent_records = []
        for approval in recent_items:
            session_date = to_jalali_str(approval.session.date) if approval.session and approval.session.date else None
            recent_records.append({
                "title": approval.title,
                "code": f"APP-{approval.id}",
                "date": session_date,
                "status": determine_status(approval)
            })

        data = {
            "title": "مصوبات",
            "stats": {
                "delayed_count": delayed_count,
                "with_deadline_count": with_deadline_count,
                "completed_on_time_percent": completed_on_time_percent
            },
            "chart": {
                "type": "pie",
                "data": {
                    "labels": ["دارای تأخیر", "دارای مهلت", "اقدام شده در موعد مقرر"],
                    "values": [delayed_count, with_deadline_count, completed_on_time_percent],
                    "show_percent": True,
                    "colors": ["#F56565", "#ECC94B", "#48BB78"]
                }
            },
            "recent_records_title": "تازه‌ترین مصوبات",
            "recent_records": list(recent_records)
        }
        data["url"] = "http://172.30.230.140/"
        return Response(data)


class ProcessCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from pm.models import Flow, Node

        user = request.user

        flows_qs = Flow.objects.filter(
            Q(user=user) | Q(nodes__user=user)
        ).distinct()

        finished_processes = flows_qs.exclude(nodes__done_time__isnull=True).distinct().count()
        in_progress_processes = flows_qs.filter(nodes__done_time__isnull=True).distinct().count()

        user_nodes = Node.objects.filter(user=user).select_related('flow', 'flow__flow_pattern')
        actions_done = user_nodes.filter(done_time__isnull=False).count()
        actions_pending = user_nodes.filter(done_time__isnull=True).count()

        durations = []
        for node in user_nodes.filter(done_time__isnull=False):
            start = to_datetime_obj(node.create_time)
            end = to_datetime_obj(node.done_time)
            if start and end:
                delta = end - start
                durations.append(delta.total_seconds() / 3600)
        avg_action_hours = round(sum(durations) / len(durations), 1) if durations else 0.0

        recent_flows = flows_qs.select_related('flow_pattern').order_by('-create_time')[:5]
        pending_flow_ids = set(
            Flow.objects.filter(id__in=[flow.id for flow in recent_flows], nodes__done_time__isnull=True).values_list(
                'id', flat=True)
        )

        recent_records = []
        for flow in recent_flows:
            status = 'در جریان' if flow.id in pending_flow_ids else 'پایان یافته'
            if status == 'پایان یافته':
                latest_done = flow.nodes.filter(done_time__isnull=False).order_by('-done_time').values_list('done_time',
                                                                                                            flat=True).first()
                date_val = latest_done or flow.create_time
            else:
                date_val = flow.create_time
            recent_records.append({
                "title": flow.flow_pattern.title,
                "type": flow.flow_pattern.type,
                "status": status,
                "date": to_jalali_str(date_val)
            })

        chart_type = "pie"

        data = {
            "title": "فرایند",
            "stats": {
                "finished_processes": finished_processes,
                "in_progress_processes": in_progress_processes,
                "actions_done": actions_done,
                "actions_pending": actions_pending,
                "avg_action_hours": avg_action_hours
            },
            "chart": {
                "type": chart_type,
                "data": {
                    "labels": ["پایان یافته", "در جریان", "اقدام شده", "منتظر اقدام"],
                    "values": [finished_processes, in_progress_processes, actions_done, actions_pending],
                    "colors": ["#2F855A", "#3182CE", "#805AD5", "#DD6B20"]
                }
            },
            "recent_records_title": "جدیدترین فرایندها",
            "recent_records": recent_records
        }
        data["url"] = "http://172.30.230.140/"
        return Response(data)


class MessagesCardView(APIView):
    def get(self, request):
        try:
            from chat.models import Chat, Member, Room

            user = request.user

            def fmt(dt):
                return to_jalali_str(dt, has_time=True)

            # دریافت Memberهای کاربر و محاسبه تعداد پیام‌های خوانده نشده
            # فقط اتاق‌های شخصی (type='chat')
            user_members = Member.objects.filter(
                user=user,
                room__type='chat'
            ).select_related('room')

            total_unread = 0
            # ایجاد dictionary برای دسترسی سریع به Member بر اساس room_id
            members_by_room = {}
            for member in user_members:
                total_unread += member.unseen_count
                members_by_room[member.room_id] = member

            # تعداد کل گفتگوها
            total_conversations = user_members.count()

            # محاسبه تعداد کاربران آنلاین
            # کاربران آنلاین: کاربرانی که در حال حاضر به سوکت متصل هستند
            from chat.events import get_online_users
            current_online_user_ids = get_online_users()

            # دریافت تمام Memberهای اتاق‌های گفتگوی کاربر (شامل کاربران دیگر)
            all_members_in_user_rooms = Member.objects.filter(
                room_id__in=list(members_by_room.keys()),
                room__type='chat'
            ).exclude(user=user).select_related('user')

            # شمارش کاربران آنلاین (بر اساس اتصال سوکت)
            distinct_user_ids_in_rooms = set(member.user_id for member in all_members_in_user_rooms)
            online_users_count = len(distinct_user_ids_in_rooms.intersection(current_online_user_ids))

            # دریافت چت‌هایی با پیام‌های خوانده نشده
            unread_chats = []
            for member in user_members:
                if member.unseen_count > 0:
                    # پیدا کردن کاربر دیگر در این اتاق (فرستنده)
                    other_member = Member.objects.filter(
                        room=member.room,
                        room__type='chat'
                    ).exclude(user=user).select_related('user').first()

                    if other_member:
                        unread_chats.append({
                            "name": other_member.user.get_full_name(),
                            "avatar": other_member.user.photo_url if hasattr(other_member.user, 'photo_url') else None,
                            "unread_count": member.unseen_count
                        })

            # دریافت room_ids برای پیام‌های شخصی
            room_ids = list(members_by_room.keys())

            if not room_ids:
                # اگر کاربر در هیچ اتاق شخصی عضو نیست
                data = {
                    "stats": {
                        "unread_messages": 0,
                        "online_users_count": 0,
                        "total_conversations": 0
                    },
                    "chart": None,
                    "recent_records": [],
                    "unread_chats": []
                }
                data["url"] = "http://172.30.230.140/"
                return Response(data)

            # دریافت آخرین پیام از هر فرستنده در اتاق‌های شخصی
            latest_chats = Chat.objects.filter(
                room_id__in=room_ids,
                room__type='chat'
            ).exclude(user=user).select_related('user', 'room').order_by('-create_time')

            # گروه‌بندی بر اساس فرستنده و گرفتن آخرین پیام هر فرستنده
            latest_by_sender = {}
            for chat in latest_chats:
                sender_id = chat.user_id
                # اگر این فرستنده را قبلاً ندیده‌ایم یا این پیام جدیدتر است
                if sender_id not in latest_by_sender or chat.create_time > latest_by_sender[sender_id].create_time:
                    latest_by_sender[sender_id] = chat

            # تبدیل به لیست و مرتب‌سازی بر اساس زمان (جدیدترین اول)
            recent_chats_list = sorted(latest_by_sender.values(), key=lambda x: x.create_time, reverse=True)[:10]

            recent_records = []
            for chat in recent_chats_list:
                # بررسی اینکه آیا پیام خوانده شده یا نه
                member = members_by_room.get(chat.room_id)
                if member:
                    is_unread = chat.create_time > member.my_last_seen_time
                else:
                    is_unread = True  # اگر Member وجود نداشت، به عنوان unread در نظر بگیر

                # پیش‌نمایش پیام (حداکثر 100 کاراکتر)
                message_preview = None
                if chat.body:
                    message_preview = chat.body[:100] + '...' if len(chat.body) > 100 else chat.body
                elif chat.file:
                    message_preview = 'فایل ارسال شده'
                else:
                    message_preview = ''

                # متن کامل پیام
                message_body = chat.body if chat.body else None

                # اطلاعات فایل در صورت وجود
                file_url = chat.file_url if chat.file else None

                recent_records.append({
                    "sender_name": chat.user.get_full_name(),
                    "sender_avatar": chat.user.photo_url if hasattr(chat.user, 'photo_url') else None,
                    "message_preview": message_preview,
                    "message": message_body,
                    "file_url": file_url,
                    "datetime": fmt(chat.create_time),
                    "is_unread": is_unread
                })

            data = {
                "stats": {
                    "unread_messages": total_unread,
                    "online_users_count": online_users_count,
                    "total_conversations": total_conversations
                },
                "chart": None,
                "recent_records": recent_records,
                "unread_chats": unread_chats
            }
            data["url"] = "http://172.30.230.140/"
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)})


class AvailableDashboardsView(APIView):
    def get(self, request):
        data = {

            "dashboards": [
                {
                    "id": 1,
                    "title": "وظایف",
                    "is_global": True,
                    "order": 0,
                    "slug": "tasks"
                },
                {
                    "id": 2,
                    "title": "تردد",
                    "is_global": True,
                    "order": 0,
                    "slug": "attendance"
                },
                {
                    "id": 3,
                    "title": "اطلاعات ورود",
                    "is_global": True,
                    "order": 0,
                    "slug": "login-activity"
                },
                {
                    "id": 5,
                    "title": "گفت‌وگوها",
                    "is_global": False,
                    "order": 0,
                    "slug": "messages"
                },
                {
                    "id": 8,
                    "title": "وظایف",
                    "is_global": False,
                    "order": 0,
                    "slug": ""
                }
            ],
        }
        return Response(data)

class UpcomingSessionsCardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        from pm.models import Session

        user = request.user
        #user = User.objects.get(id=)
        today = jdatetime.date.today()

        # ---------------------------
        # 📅 شروع از فردا (امروز حذف)
        # ---------------------------
        working_days = []
        current_day = today + jdatetime.timedelta(days=1)

        while len(working_days) < 5:
            # شنبه(0) تا چهارشنبه(4) روز کاری
            if current_day.weekday() <= 4:
                working_days.append(current_day)
            current_day += jdatetime.timedelta(days=1)

        # ---------------------------
        # 📂 جلسات این ۵ روز کاری
        # ---------------------------
        sessions_qs = Session.objects.filter(
            date__in=working_days
        ).filter(
            Q(user=user) | Q(members=user)
        ).distinct()

        sessions = list(sessions_qs)

        # -----------------------
        # 📊 آمار
        # -----------------------
        total_sessions = len(sessions)

        durations = []
        members_counts = []
        approvals_counts = []

        for s in sessions:
            if s.start and s.end:
                duration_hours = (s.end - s.start).total_seconds() / 3600
                durations.append(duration_hours)

            members_counts.append(s.member_count)
            approvals_counts.append(s.approval_count)

        avg_duration = round(sum(durations) / len(durations), 1) if durations else 0
        avg_members = round(sum(members_counts) / len(members_counts), 1) if members_counts else 0
        avg_approvals = round(sum(approvals_counts) / len(approvals_counts), 1) if approvals_counts else 0

        # -----------------------
        # 📈 چارت
        # -----------------------
        labels = []
        values = []

        for d in working_days:
            labels.append(d.j_weekdays_fa[d.weekday()])
            count = sum(1 for s in sessions if s.date == d)
            values.append(count)

        # -----------------------
        # 📝 لیست جلسات
        # -----------------------
        recent_records = []

        for s in sorted(sessions, key=lambda x: x.date):
            recent_records.append({
                "title": s.title,
                "date": to_jalali_str(s.date),
                "weekday": s.weekday,
                "time": s.time,
                "members": s.member_count,
                "approvals": s.approval_count,
                "status": "تأیید شده" if s.is_fully_approved else "در انتظار تأیید"
            })

        data = {
            "title": "۵ روز کاری آینده",
            "stats": {
                "total_sessions": total_sessions,
                "avg_duration_hours": avg_duration,
                "avg_members": avg_members,
                "avg_approvals": avg_approvals
            },
            "chart": {
                "type": "table",
                "data": {
                    "labels": labels,
                    "values": values
                }
            },
            "recent_records_title": "جلسات ۵ روز کاری آینده",
            "recent_records": recent_records
        }

        data["url"] = "http://172.30.230.140/"
        return Response(data)




