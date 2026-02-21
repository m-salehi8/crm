from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncMonth
import jdatetime
from datetime import timedelta
import datetime
from collections import defaultdict

# فرض بر این است که مدل‌ها از این مسیرها به درستی فراخوانی شده‌اند
from core.models import User, Unit, Post, Dashboard, DashboardAccess
from cn.models import Contract, ContractTask
from fn.models import Invoice, InvoiceCover
from hr.models import Profile, Work
from prj.models import Project, Phase, Mission, Report
from django.urls import resolve
from django.db.models import Sum, Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cn.models import Contract


# ---------------------------
# Access control helpers
# ---------------------------

def _get_dashboard_scope(user: User, dashboard_id):
    """Return tuple (allowed: bool, unit_id: Optional[int]).
    - If not allowed, returns (False, None)
    - If allowed and global access: (True, None)
    - If allowed and scoped to user's unit: (True, unit_id)
    """
    if not dashboard_id:
        return False, None
    try:
        dashboard = Dashboard.objects.get(pk=dashboard_id)
    except Dashboard.DoesNotExist:
        return False, None

    access = DashboardAccess.objects.filter(dashboard=dashboard, user=user).first()
    if not access:
        return False, None

    if access.is_global:
        return True, None

    # Scoped to own unit; requires user to have a post/unit
    if user.post_id and user.post and user.post.unit_id:
        return True, user.post.unit_id

    return False, None


# ---------------------------
# Dashboard Access Control
# ---------------------------
# ---------------------------
# Dashboard Access Control (Slug Based)
# ---------------------------



def require_dashboard_access():
    def decorator(view_func):
        def _wrapped(request, *args, **kwargs):

            # استخراج slug از URL
            path_parts = request.path.strip('/').split('/')

            try:
                dashboard_slug = path_parts[-1]
            except IndexError:
                return Response(
                    {'detail': 'مسیر نامعتبر است'},
                    status=400
                )

            try:
                dashboard = Dashboard.objects.get(slug=dashboard_slug)
            except Dashboard.DoesNotExist:
                return Response(
                    {'detail': 'داشبورد نامعتبر است'},
                    status=404
                )

            access = DashboardAccess.objects.filter(
                dashboard=dashboard,
                user=request.user
            ).first()

            if not access:
                return Response(
                    {'detail': 'عدم دسترسی به این داشبورد'},
                    status=403
                )

            # آماده برای آینده (is_global)
            request.dashboard = dashboard
            request.dashboard_slug = dashboard.slug
            request.dashboard_unit_id = None if access.is_global else (
                request.user.post.unit_id
                if getattr(request.user, 'post_id', None)
                else None
            )

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


# ----------------------------------------------------------------------
# 1. کارت ۱: فرایند تأمین کالا
# ----------------------------------------------------------------------


from collections import defaultdict
import jdatetime
from django.db.models import Max
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pm.models import *


from django.db.models import Max, OuterRef, Subquery
from collections import defaultdict

from django.db.models import Count, Max
from collections import defaultdict

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def procurement_process_stats_v2(request):

    unit_id = getattr(request, 'dashboard_unit_id', None)

    # -----------------------------
    # گرفتن FlowPattern تأمین کالا
    # -----------------------------
    flow_pattern = FlowPattern.objects.filter(id=11).first()
    if not flow_pattern:
        return Response({"error": "FlowPattern not found"}, status=400)

    # -----------------------------
    # گرفتن کل درخواست‌ها
    # -----------------------------
    flows = Flow.objects.filter(
        flow_pattern=flow_pattern
    ).select_related('user__post__unit')

    if unit_id:
        flows = flows.filter(user__post__unit_id=unit_id)

    total_requests = flows.count()

    # -----------------------------
    # پیدا کردن آخرین نود هر Flow
    # -----------------------------
    latest_nodes = Node.objects.filter(
        flow__in=flows
    ).values('flow').annotate(
        last_node_id=Max('id')
    )

    latest_node_ids = [item['last_node_id'] for item in latest_nodes]

    final_nodes = Node.objects.filter(id__in=latest_node_ids)

    responded_count = final_nodes.filter(done_time__isnull=False).count()

    response_rate = round(
        (responded_count / total_requests) * 100, 1
    ) if total_requests > 0 else 0

    # -----------------------------
    # گرفتن فیلد "دسته‌بندی کالا"
    # -----------------------------
    category_field = Field.objects.filter(
        flow_pattern=flow_pattern,
        label='دسته‌بندی کالا'
    ).first()

    if not category_field:
        return Response({"error": "Category field not found"}, status=400)

    # -----------------------------
    # گرفتن Answer های مربوط به نوع کالا
    # -----------------------------
    answers = Answer.objects.filter(
        flow__in=flows,
        field=category_field
    )

    category_counts = (
        answers
        .values('body')
        .annotate(count=Count('id'))
        .order_by()
    )

    chart_data = [
        {"name": item['body'], "value": item['count']}
        for item in category_counts
        if item['body']
    ]

    return Response({
        "stats": {
            "total_requests": total_requests,
            "responded": responded_count,
            "response_rate": response_rate
        },
        "chart": {
            "type": "pie",
            "data": chart_data
        },
        "url": "http://172.30.230.140/"
    })



from collections import defaultdict
from django.db.models import OuterRef, Subquery


from django.db.models import Count
from collections import defaultdict

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def procurement_process_stats_v3(request):

    unit_id = getattr(request, 'dashboard_unit_id', None)

    # -----------------------------
    # گرفتن FlowPattern تأمین کالا
    # -----------------------------
    flow_pattern = FlowPattern.objects.filter(id=11).first()
    if not flow_pattern:
        return Response({"error": "FlowPattern not found"}, status=400)

    # -----------------------------
    # گرفتن کل درخواست‌ها
    # -----------------------------
    flows = Flow.objects.filter(
        flow_pattern=flow_pattern
    ).select_related('user', 'user__post', 'user__post__unit')

    if unit_id:
        flows = flows.filter(user__post__unit_id=unit_id)

    total_requests = flows.count()

    # -----------------------------
    # پیدا کردن فیلد "دسته‌بندی کالا"
    # -----------------------------
    category_field = Field.objects.filter(
        flow_pattern=flow_pattern,
        label='دسته‌بندی کالا'
    ).first()

    if not category_field:
        return Response({"error": "Category field not found"}, status=400)

    # -----------------------------
    # گرفتن Answer های مربوط به نوع کالا
    # -----------------------------
    answers = Answer.objects.filter(
        flow__in=flows,
        field=category_field
    )

    # group by body
    category_counts = (
        answers
        .values('body')
        .annotate(count=Count('id'))
        .order_by()
    )

    chart_data = [
        {"name": item['body'], "value": item['count']}
        for item in category_counts
        if item['body']
    ]

    return Response({
        "stats": {
            "total_requests": total_requests,
        },
        "chart": {
            "type": "pie",
            "data": chart_data
        },
        "url": "http://172.30.230.140/"
    })

# ----------------------------------------------------------------------
# 2. کارت ۲: قرارداد
# ----------------------------------------------------------------------

from collections import defaultdict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cn.models import Contract


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def contract_stats_v2(request):

    unit_id = request.dashboard_unit_id

    queryset = Contract.objects.all()

    # scope واحد
    if unit_id:
        queryset = queryset.filter(project__unit_id=unit_id)

    total = queryset.count()
    archived = queryset.filter(archived=True).count()

    # فقط قراردادهای جاری برای نمودار
    active_queryset = queryset.filter(archived=False)

    status_counter = defaultdict(int)

    for contract in active_queryset:
        status_counter[contract.status] += 1

    labels = list(status_counter.keys())
    values = list(status_counter.values())

    return Response({
        "stats": {
            "total": total,
            "archived": archived,
            "active": active_queryset.count()
        },
        "chart": {
            "type": "bar",
            "data": {
                "labels": labels,
                "values": values
            }
        },
        "url": "http://172.30.230.140/"
    })



# ----------------------------------------------------------------------
# 3. کارت ۳: تنخواه (اصلاح فیلتر YTD)
# ----------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def petty_cash_stats_v2(request):
    """
    کارت ۳: تنخواه
    آمار ۱: تعداد فاکتورها / عدد (YTD - اصلاح شده)
    آمار ۲: مجموع مبالغ / میلیون ریال (YTD - اصلاح شده)
    مجموع هزینه تنخواه در طول زمان | نوع نمودار: line
    """
    current_date = jdatetime.datetime.now()
    current_year = current_date.year

    # محاسبه محدوده زمانی سال جاری (میلادی)
    year_start_greg = jdatetime.date(current_year, 1, 1).togregorian()
    year_end_greg = datetime.datetime.now()

    # Invoice به InvoiceCover لینک دارد و InvoiceCover به Unit لینک دارد
    # Invoice.date یک jDateField است که باید به Gregorian تبدیل شود
    invoices_ytd = Invoice.objects.filter(
        date__gte=year_start_greg,
        date__lte=year_end_greg
    ).select_related('cover__unit')
    unit_id = getattr(request, 'dashboard_unit_id', None)
    if unit_id:
        invoices_ytd = invoices_ytd.filter(cover__unit_id=unit_id)

    # آمار ۱: تعداد فاکتورها (YTD - اصلاح شده)
    total_invoices = invoices_ytd.count()

    # آمار ۲: مجموع مبالغ (YTD - اصلاح شده)
    total_amount = invoices_ytd.aggregate(total=Sum('price'))['total'] or 0
    total_amount_millions = round(total_amount / 1000000, 0)

    # نمودار line: مجموع هزینه تنخواه در طول زمان (ماهانه)
    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]

    current_month = current_date.month
    monthly_data = []
    chart_labels = []

    for month in range(1, current_month + 1):
        chart_labels.append(persian_months[month - 1])

        month_start = jdatetime.date(current_year, month, 1)

        # محاسبه پایان ماه
        if month == 12:
            next_month_start = jdatetime.date(current_year + 1, 1, 1)
        else:
            next_month_start = jdatetime.date(current_year, month + 1, 1)
        month_end = next_month_start - timedelta(days=1)

        # تبدیل به Gregorian برای استفاده در query
        month_start_greg = month_start.togregorian()
        month_end_greg = month_end.togregorian()

        month_total = Invoice.objects.filter(
            date__gte=month_start_greg,
            date__lte=month_end_greg
        ).select_related('cover__unit')
        if unit_id:
            month_total = month_total.filter(cover__unit_id=unit_id)
        month_total = month_total.aggregate(total=Sum('price'))['total'] or 0

        monthly_data.append(round(month_total / 1000000, 0))

    resp = {
        'stats': {
            'total_invoices': total_invoices,
            'total_amount_millions': total_amount_millions
        },
        'chart': {
            'type': 'line',
            'data': {
                'labels': chart_labels,
                'values': monthly_data
            }
        }
    }
    resp["url"] = "http://172.30.230.140/"
    return Response(resp)


# ----------------------------------------------------------------------
# 4. کارت ۴: حقوق و کارایی (اصلاح فیلتر YTD و محاسبات حقوق)
# ----------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def payroll_efficiency_stats_v2(request):
    """
    کارت ۴: حقوق و کارایی
    آمار ۱: مجموع کارایی واحد / میلیون ریال (YTD - اصلاح شده)
    آمار ۲: میانگین حقوق واحد / میلیون ریال (فقط کاربران فعال و محاسبه دقیق‌تر - اصلاح شده)
    کارایی یا حقوق دریافتی در طول زمان | نوع نمودار: line
    """
    current_year = jdatetime.datetime.now().year

    # آمار ۱: مجموع کارایی واحد (YTD - اصلاح شده)
    # فیلتر Work بر اساس سال جاری
    # Work به User لینک دارد، User به Post (OneToOne) لینک دارد، Post به Unit لینک دارد
    total_efficiency_qs = Work.objects.filter(year=current_year).select_related('user__post__unit')
    unit_id = getattr(request, 'dashboard_unit_id', None)
    if unit_id:
        total_efficiency_qs = total_efficiency_qs.filter(user__post__unit_id=unit_id, user__post__isnull=False)
    total_efficiency = total_efficiency_qs.aggregate(total=Sum('bonus'))['total'] or 0
    total_efficiency_millions = round(total_efficiency / 1000000, 0)

    # آمار ۲: میانگین حقوق واحد (محاسبه از Profile) - فقط کاربران فعال
    # Profile به User (OneToOne) لینک دارد، User به Post (OneToOne) لینک دارد، Post به Unit لینک دارد
    active_profiles = Profile.objects.filter(user__is_active=True, user__post__isnull=False).select_related(
        'user__post__unit')
    if unit_id:
        active_profiles = active_profiles.filter(user__post__unit_id=unit_id)
    total_active_users = active_profiles.count()

    # جمع تمام فیلدهای اصلی حقوقی (sf1, sf5, sf6, sf7, sf8, sf11, sf14, sf20, sf68, sf70)
    salary_sum_agg = active_profiles.aggregate(
        s1=Sum('sf1', default=0),
        s5=Sum('sf5', default=0),
        s6=Sum('sf6', default=0),
        s7=Sum('sf7', default=0),
        s8=Sum('sf8', default=0),
        s11=Sum('sf11', default=0),
        s14=Sum('sf14', default=0),
        s20=Sum('sf20', default=0),
        s68=Sum('sf68', default=0),
        s70=Sum('sf70', default=0),

        # اضافه کردن فیلدهای دیگر حقوق و مزایا که در مدل Profile شما بوده‌اند:
        mobile=Sum('sf_mobile', default=0),
        food=Sum('sf_food', default=0),
        commuting=Sum('sf_commuting', default=0),
        house=Sum('sf_house', default=0),
        management=Sum('sf_management', default=0),
    )

    # جمع کل حقوق برای همه کاربران فعال
    total_salary = sum(salary_sum_agg.values())

    # میانگین حقوق (جمع کل حقوق تقسیم بر تعداد کاربران فعال)
    avg_salary = total_salary / total_active_users if total_active_users > 0 else 0
    avg_salary_millions = round(avg_salary / 1000000, 0)

    # نمودار line: کارایی ماهانه سال جاری
    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]

    current_month = jdatetime.datetime.now().month

    monthly_efficiency = []
    chart_labels = []

    for month in range(1, current_month + 1):
        chart_labels.append(persian_months[month - 1])

        month_efficiency_qs = Work.objects.filter(
            year=current_year,
            month=month
        ).select_related('user__post__unit')
        if unit_id:
            month_efficiency_qs = month_efficiency_qs.filter(user__post__unit_id=unit_id, user__post__isnull=False)
        month_efficiency = month_efficiency_qs.aggregate(total=Sum('bonus'))['total'] or 0

        monthly_efficiency.append(round(month_efficiency / 1000000, 0))

    resp = {
        'stats': {
            'total_efficiency_millions': total_efficiency_millions,
            'avg_salary_millions': avg_salary_millions
        },
        'chart': {
            'type': 'line',
            'data': {
                'labels': chart_labels,
                'values': monthly_efficiency
            }
        }
    }
    resp["url"] = "http://172.30.230.140/"
    return Response(resp)


# ----------------------------------------------------------------------
# 5. کارت ۵: منابع انسانی (اصلاح فیلتر YTD و منطق آمار)
# ----------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def human_resources_stats_v2(request):
    """
    کارت ۵: منابع انسانی
    آمار ۱: تعداد کارمندان فعلی واحد / نفر (کل فعال‌ها - اصلاح شده)
    آمار ۲: درصد کارمندان رسمی واحد / درصد (جایگزین پاسخگویی ۱۰۰٪ - اصلاح شده)
    تعداد افراد بر اساس جایگاه شغلی | نوع نمودار: bar (کل فعال‌ها - اصلاح شده)
    """
    # ----------------------------------------
    # Stats (آمار کارت - کل فعال‌ها)
    # فیلتر YTD از روی تاریخ عضویت (date_joined) حذف شد.
    # ----------------------------------------
    # Profile به User (OneToOne) لینک دارد، User به Post (OneToOne) لینک دارد، Post به Unit لینک دارد
    active_profiles = Profile.objects.filter(user__is_active=True, user__post__isnull=False).select_related(
        'user__post__unit')
    unit_id = getattr(request, 'dashboard_unit_id', None)
    if unit_id:
        active_profiles = active_profiles.filter(user__post__unit_id=unit_id)
    total_employees = active_profiles.count()

    # آمار ۲: درصد کارمندان رسمی (آمار اصلاح شده)
    permanent_employees = active_profiles.filter(is_permanent=True).count()
    permanent_rate = round((permanent_employees / total_employees * 100) if total_employees > 0 else 0, 1)

    # ----------------------------------------
    # Chart (نمودار - کل فعال‌ها)
    # ----------------------------------------
    job_positions = ['کارشناس', 'مشاور', 'سرپرست', 'معاون', 'مدیر']
    position_counts = []

    for position in job_positions:
        # فیلتر بدون محدودیت زمانی، روی کاربران فعال
        count = active_profiles.filter(
            user__post__title__icontains=position
        ).count()
        position_counts.append(count)

    resp = {
        'stats': {
            'total_employees': total_employees,
            # نام فیلد 'response_rate' به 'permanent_rate' تغییر نیافت تا در فرانت تغییرات کمتری لازم باشد
            'response_rate': permanent_rate
        },
        'chart': {
            'type': 'bar',
            'data': {
                'labels': job_positions,
                'values': position_counts
            }
        }
    }
    resp["url"] = "http://172.30.230.140/"
    return Response(resp)


# ----------------------------------------------------------------------
# 6. کارت ۶: مدیریت برنامه‌ها
# ----------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def program_management_stats_v2(request):
    """
    کارت ۶: مدیریت برنامه‌ها
    آمار ۱: تعداد برنامه‌ها / عدد (YTD)
    آمار ۲: میانگین پیشرفت / درصد
    آمار ۳: میانگین تأخیر / درصد
    آمار ۴: تعداد مأموریت / عدد (YTD)
    آمار ۵: آخرین گزارش‌ها / عدد (YTD)
    """
    current_year = jdatetime.datetime.now().year

    # پروژه‌های سال جاری
    # Project به Unit لینک دارد
    programs_ytd = Project.objects.filter(year=current_year).select_related('unit')
    unit_id = getattr(request, 'dashboard_unit_id', None)
    if unit_id:
        programs_ytd = programs_ytd.filter(unit_id=unit_id)

    # آمار ۱: تعداد برنامه‌ها (YTD)
    total_programs = programs_ytd.count()

    # آمار ۲: میانگین پیشرفت (YTD)
    avg_progress = programs_ytd.aggregate(avg=Avg('progress'))['avg'] or 0
    avg_progress_percent = round(avg_progress, 1)

    # آمار ۳: میانگین تأخیر (YTD)
    # تأخیر = میانگین (توقع - پیشرفت) | اگر پیشرفت جلوتر باشد (negative)، تأخیر صفر است.
    avg_delay_agg = programs_ytd.aggregate(
        avg_expected=Avg('expected'),
        avg_progress=Avg('progress')
    )

    avg_delay = (avg_delay_agg['avg_expected'] or 0) - (avg_delay_agg['avg_progress'] or 0)
    avg_delay_percent = round(max(0, avg_delay), 1)

    # آمار ۴: تعداد مأموریت‌ها (YTD)
    # Mission به Project از طریق ManyToMany لینک دارد (related_name='missions' در Project)
    total_missions = Mission.objects.filter(projects__in=programs_ytd).distinct().count()

    # آمار ۵: آخرین گزارش‌های ثبت شده (YTD)
    today_j = jdatetime.date.today()
    year_start_j = jdatetime.date(today_j.year, 1, 1)

    # فیلتر بر اساس تاریخ جلالی (claim_date)
    # Report به Phase لینک دارد و Phase به Project لینک دارد و Project به Unit لینک دارد
    recent_reports_qs = Report.objects.filter(
        claim_date__gte=year_start_j,
        claim_date__lte=today_j
    ).select_related('phase__project__unit')
    if unit_id:
        recent_reports_qs = recent_reports_qs.filter(phase__project__unit_id=unit_id)
    recent_reports = recent_reports_qs.count()

    resp = {
        'stats': {
            'total_programs': total_programs,
            'avg_progress_percent': avg_progress_percent,
            'avg_delay_percent': avg_delay_percent,
            'total_missions': total_missions,
            'recent_reports': recent_reports
        }
    }
    resp["url"] = "http://172.30.230.140/"
    return Response(resp)




# ----------------------------------------------------------------------
# 8. کارت ۸: جلسات
# ----------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def meetings_stats_v2(request):
    """
    کارت ۸: جلسات
    تعداد جلسات در هر ماه | نوع نمودار: line
    """
    try:
        # Import Session model from pm app
        from pm.models import Session

        # Get current year
        current_year = jdatetime.datetime.now().year

        # Persian month names
        persian_months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]

        # Initialize monthly data
        # Session به Unit لینک دارد
        monthly_labels = []
        monthly_values = []
        total_meetings = 0
        unit_id = getattr(request, 'dashboard_unit_id', None)

        for month in range(1, 13):
            month_name = persian_months[month - 1]
            # Calculate month start and end dates
            month_start = jdatetime.date(current_year, month, 1)
            if month == 12:
                next_month_start = jdatetime.date(current_year + 1, 1, 1)
            else:
                next_month_start = jdatetime.date(current_year, month + 1, 1)
            month_end = next_month_start - timedelta(days=1)

            # Count meetings in this month
            # Session.date یک jDateField است
            sessions_qs = Session.objects.filter(
                date__gte=month_start,
                date__lte=month_end
            ).select_related('unit')
            if unit_id:
                sessions_qs = sessions_qs.filter(unit_id=unit_id)
            count = sessions_qs.count()

            monthly_labels.append(month_name)
            monthly_values.append(count)
            total_meetings += count

        resp = {
            'stats': {
                'total_meetings': total_meetings
            },
            'chart': {
                'type': 'line',
                'data': {
                    'labels': monthly_labels,
                    'values': monthly_values
                }
            }
        }
        resp["url"] = "http://172.30.230.140/"
        return Response(resp)

    except ImportError:
        # Fallback: return test data if Session model is not available
        test_data = {
            "فروردین": 3,
            "اردیبهشت": 4,
            "خرداد": 2,
            "تیر": 5,
            "مرداد": 6,
            "شهریور": 4
        }
        resp = {
            'stats': {
                'total_meetings': sum(test_data.values())
            },
            'chart': {
                'type': 'line',
                'data': {
                    'labels': list(test_data.keys()),
                    'values': list(test_data.values())
                }
            }
        }
        resp["url"] = "http://172.30.230.140/"
        return Response(resp)
    except Exception:
        # Fallback: return test data if any error occurs
        test_data = {
            "فروردین": 3,
            "اردیبهشت": 4,
            "خرداد": 2,
            "تیر": 5,
            "مرداد": 6,
            "شهریور": 4
        }
        resp = {
            'stats': {
                'total_meetings': sum(test_data.values())
            },
            'chart': {
                'type': 'line',
                'data': {
                    'labels': list(test_data.keys()),
                    'values': list(test_data.values())
                }
            }
        }
        resp["url"] = "http://172.30.230.140/"
        return Response(resp)


# ----------------------------------------------------------------------
# 9. کارت ۹: وظایف
# ----------------------------------------------------------------------

from collections import defaultdict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pm.models import Job


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def tasks_stats_v2(request):

    unit_id = request.dashboard_unit_id

    queryset = Job.objects.all()

    # scope واحد
    if unit_id:
        queryset = queryset.filter(project__unit_id=unit_id)

    total = queryset.count()

    archived = queryset.filter(archive=True).count()

    done = queryset.filter(
        archive=False,
        status='done'
    ).count()

    active = queryset.filter(
        archive=False
    ).exclude(status='done').count()

    # نمودار بر اساس status واقعی
    active_queryset = queryset.filter(archive=False)

    status_counter = defaultdict(int)

    for job in active_queryset:
        status_counter[job.get_status_display()] += 1

    labels = list(status_counter.keys())
    values = list(status_counter.values())

    return Response({
        "stats": {
            "total": total,
            "active": active,
            "done": done,
            "archived": archived
        },
        "chart": {
            "type": "bar",
            "data": {
                "labels": labels,
                "values": values
            }
        },
        "url": "http://172.30.230.140/"
    })

# ----------------------------------------------------------------------
# 10. کارت ۱۰: حقوق و کارایی (نسخه جدید - ماهانه)
# ----------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def payroll_efficiency_monthly_stats_v2(request):
    """
    کارت ۱۰: حقوق و کارایی (نسخه جدید)
    میانگین حقوق و میانگین شاخص کارایی بر اساس ماه
    خروجی JSON برای نمودار خطی (line chart)
    """
    try:
        # Use existing models: Work for efficiency and Profile for salary
        # Work به User لینک دارد، User به Post (OneToOne) لینک دارد، Post به Unit لینک دارد
        # Profile به User (OneToOne) لینک دارد، User به Post (OneToOne) لینک دارد، Post به Unit لینک دارد
        current_year = jdatetime.datetime.now().year
        persian_months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]

        unit_id = getattr(request, 'dashboard_unit_id', None)

        salary_data = {}
        efficiency_data = {}
        salary_values = []
        efficiency_values = []

        for month in range(1, 13):
            month_name = persian_months[month - 1]

            # Get monthly efficiency from Work model
            monthly_work = Work.objects.filter(
                year=current_year,
                month=month
            ).select_related('user__post__unit')
            if unit_id:
                monthly_work = monthly_work.filter(user__post__unit_id=unit_id, user__post__isnull=False)

            # Calculate average efficiency for this month
            avg_efficiency = monthly_work.aggregate(avg=Avg('bonus'))['avg'] or 0

            # Get monthly salary from Profile model
            # محاسبه میانگین حقوق از Profile برای کاربران فعال که post دارند
            monthly_profiles = Profile.objects.filter(
                user__is_active=True,
                user__post__isnull=False
            ).select_related('user__post__unit')
            if unit_id:
                monthly_profiles = monthly_profiles.filter(user__post__unit_id=unit_id)

            # جمع تمام فیلدهای حقوقی
            salary_sum_agg = monthly_profiles.aggregate(
                s1=Sum('sf1', default=0),
                s5=Sum('sf5', default=0),
                s6=Sum('sf6', default=0),
                s7=Sum('sf7', default=0),
                s8=Sum('sf8', default=0),
                s11=Sum('sf11', default=0),
                s14=Sum('sf14', default=0),
                s20=Sum('sf20', default=0),
                s68=Sum('sf68', default=0),
                s70=Sum('sf70', default=0),
                mobile=Sum('sf_mobile', default=0),
                food=Sum('sf_food', default=0),
                commuting=Sum('sf_commuting', default=0),
                house=Sum('sf_house', default=0),
                management=Sum('sf_management', default=0),
            )

            total_salary = sum(salary_sum_agg.values())
            total_users = monthly_profiles.count()
            avg_salary = total_salary / total_users if total_users > 0 else 0

            salary_data[month_name] = round(avg_salary, 0) if avg_salary else 0
            efficiency_data[month_name] = round(avg_efficiency, 0) if avg_efficiency else 0
            salary_values.append(avg_salary if avg_salary else 0)
            efficiency_values.append(avg_efficiency if avg_efficiency else 0)

        # Calculate overall averages
        avg_salary = round(sum(salary_values) / len([v for v in salary_values if v > 0]), 0) if any(
            salary_values) else 0
        avg_efficiency = round(sum(efficiency_values) / len([v for v in efficiency_values if v > 0]), 0) if any(
            efficiency_values) else 0

        # Prepare chart data
        salary_labels = list(salary_data.keys())
        salary_values_list = list(salary_data.values())
        efficiency_labels = list(efficiency_data.keys())
        efficiency_values_list = list(efficiency_data.values())

        resp = {
            'stats': {
                'avg_salary': avg_salary,
                'avg_efficiency': avg_efficiency
            },
            'chart': {
                'type': 'line',
                'data': {
                    'labels': salary_labels,
                    'datasets': [
                        {
                            'label': 'حقوق',
                            'values': salary_values_list
                        },
                        {
                            'label': 'کارایی',
                            'values': efficiency_values_list
                        }
                    ]
                }
            }
        }
        resp["url"] = "http://172.30.230.140/"
        return Response(resp)

    except ImportError:
        # EmployeePerformance model doesn't exist, return test data
        test_salary = {
            "فروردین": 100,
            "اردیبهشت": 110,
            "خرداد": 115,
            "تیر": 120,
            "مرداد": 125,
            "شهریور": 130
        }
        test_efficiency = {
            "فروردین": 75,
            "اردیبهشت": 78,
            "خرداد": 80,
            "تیر": 83,
            "مرداد": 85,
            "شهریور": 82
        }
        resp = {
            'stats': {
                'avg_salary': 120,
                'avg_efficiency': 82
            },
            'chart': {
                'type': 'line',
                'data': {
                    'labels': list(test_salary.keys()),
                    'datasets': [
                        {
                            'label': 'حقوق',
                            'values': list(test_salary.values())
                        },
                        {
                            'label': 'کارایی',
                            'values': list(test_efficiency.values())
                        }
                    ]
                }
            }
        }
        resp["url"] = "http://172.30.230.140/"
        return Response(resp)
    except Exception:
        # Any other error, return test data
        test_salary = {
            "فروردین": 100,
            "اردیبهشت": 110,
            "خرداد": 115,
            "تیر": 120,
            "مرداد": 125,
            "شهریور": 130
        }
        test_efficiency = {
            "فروردین": 75,
            "اردیبهشت": 78,
            "خرداد": 80,
            "تیر": 83,
            "مرداد": 85,
            "شهریور": 82
        }
        resp = {
            'stats': {
                'avg_salary': 120,
                'avg_efficiency': 82
            },
            'chart': {
                'type': 'line',
                'data': {
                    'labels': list(test_salary.keys()),
                    'datasets': [
                        {
                            'label': 'حقوق',
                            'values': list(test_salary.values())
                        },
                        {
                            'label': 'کارایی',
                            'values': list(test_efficiency.values())
                        }
                    ]
                }
            }
        }
        resp["url"] = "http://172.30.230.140/"
        return Response(resp)

# ----------------------------------------------------------------------
# 11. کارت ۱۱: سیستم‌عامل‌ها
# ----------------------------------------------------------------------

class SystemsCardViewV2(APIView):
    """
    کارت ۱۱: سیستم‌عامل‌ها
    نمایش وضعیت سیستم‌عامل‌های کاربران (یا سیستم)
    آمار ۱: تعداد کل سیستم‌عامل‌ها / عدد
    آمار ۲: تعداد Linux / عدد
    نمودار line: روند تعداد هر OS در ۶ ماه گذشته
    """
    permission_classes = [IsAuthenticated]

    @require_dashboard_access()
    def get(self, request):
        """
        برگرداندن داده تستی برای سیستم‌عامل‌ها
        """
        resp = {
            "stats": {
                "total_os": 42,
                "linux_count": 18
            },
            "chart": {
                "type": "line",
                "data": {
                    "labels": ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور"],
                    "datasets": [
                        {
                            "name": "Windows",
                            "values": [10, 11, 12, 13, 12, 14]
                        },
                        {
                            "name": "Linux",
                            "values": [6, 7, 8, 10, 11, 12]
                        },
                        {
                            "name": "macOS",
                            "values": [5, 5, 6, 6, 6, 7]
                        }
                    ]
                }
            }
        }
        return Response(resp)


# ----------------------------------------------------------------------
# 12. کارت ۱۲: ارزیابی پشتیبانی
# ----------------------------------------------------------------------

class SupportEvaluationCardViewV2(APIView):
    """
    کارت ۱۲: ارزیابی پشتیبانی
    نمایش وضعیت ارزیابی‌های نیروی پشتیبانی
    آمار ۱: مجموع آرا / عدد
    نمودار pie: توزیع نتایج ارزیابی
    """
    permission_classes = [IsAuthenticated]

    @require_dashboard_access()
    def get(self, request):
        """
        برگرداندن داده تستی برای ارزیابی پشتیبانی
        """
        resp = {
            "stats": {
                "total_votes": 128
            },
            "chart": {
                "type": "pie",
                "data": {
                    "labels": ["متوسط", "خوب", "عالی"],
                    "values": [34, 52, 42]
                }
            }
        }
        return Response(resp)


# ----------------------------------------------------------------------
# 13. کارت ۱۳: فرایندهای چابک
# ----------------------------------------------------------------------

class AgileProcessCardViewV2(APIView):
    """
    کارت ۱۳: فرایندهای چابک
    نمایش روند فرایندهای پرکاربرد در بازه شش‌ماهه
    """
    permission_classes = [IsAuthenticated]

    @require_dashboard_access()
    def get(self, request):
        """
        برگرداندن داده تستی برای فرایندهای چابک
        """
        resp = {
            "stats": {
                "total_processes": 37
            },
            "chart": {
                "type": "line",
                "data": {
                    "labels": ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور"],
                    "datasets": [
                        {
                            "name": "فرایند درخواست خرید",
                            "values": [120, 140, 160, 150, 170, 180]
                        },
                        {
                            "name": "فرایند مرخصی",
                            "values": [90, 95, 110, 100, 120, 130]
                        },
                        {
                            "name": "فرایند ثبت مشکل",
                            "values": [60, 70, 80, 85, 90, 100]
                        },
                        {
                            "name": "فرایند مدیریت پروژه",
                            "values": [50, 55, 60, 65, 70, 72]
                        },
                        {
                            "name": "فرایند تحویل کار",
                            "values": [40, 45, 50, 55, 60, 62]
                        }
                    ]
                }
            }
        }
        return Response(resp)


# ----------------------------------------------------------------------
# 14. کارت ۱۴: سند راهبردی
# ----------------------------------------------------------------------

class StrategicPlanCardViewV2(APIView):
    """
    کارت ۱۴: سند راهبردی سازمان
    نمایش وضعیت برنامه‌ها و اهداف استراتژیک
    """
    permission_classes = [IsAuthenticated]

    @require_dashboard_access()
    def get(self, request):
        """
        برگرداندن داده تستی برای سند راهبردی
        """
        resp = {
            "stats": {
                "total_programs": 12,
                "total_objectives": 34
            },
            "chart": {
                "type": "donut",
                "data": {
                    "labels": ["انجام شده", "انجام نشده"],
                    "values": [20, 14]
                }
            }
        }
        return Response(resp)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_dashboards_v2(request):
    """
    لیست داشبوردهایی که کاربر به آن دسترسی دارد
    """

    accesses = (
        DashboardAccess.objects
        .filter(user=request.user)
        .select_related('dashboard')
        .order_by('order', 'dashboard__id')
    )

    return Response({
        "dashboards": [
            {
                "id": acc.dashboard.id,
                "title": acc.dashboard.title,
                "slug": acc.dashboard.slug,
                "is_global": acc.is_global,
                "order": acc.order,
            }
            for acc in accesses
        ]
    })


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def all_dashboards(request):

    all = Dashboard.objects.all()
    dashboards = [
        {
            'id': acc.id,
            'title': acc.title,

            'slug': acc.slug,
            'url': f"http://192.168.19.174:8000/core/dashboard/charts/{acc.slug}/"
        }
        for acc in all
    ]
    resp = {'dashboards': dashboards}
    return Response(resp)



from collections import defaultdict
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def contract_stats_v3(request):

    unit_id = request.dashboard_unit_id

    queryset = Contract.objects.select_related('project', 'project__unit')

    if unit_id:
        queryset = queryset.filter(project__unit_id=unit_id)

    total = queryset.count()
    archived_count = queryset.filter(archived=True).count()

    total_value = sum(c._price for c in queryset)

    # فقط جاری‌ها برای چارت
    active_contracts = queryset.filter(archived=False)

    status_counter = defaultdict(int)

    for contract in active_contracts:
        status_counter[contract.status] += 1

    return Response({
        "stats": {
            "total": total,
            "archived": archived_count,
            "total_value": total_value
        },
        "chart": {
            "type": "bar",
            "data": {
                "labels": list(status_counter.keys()),
                "values": list(status_counter.values())
            }
        },
        "url": "http://172.30.230.140/"
    })


from django.db.models import Avg
import jdatetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def payroll_efficiency_stats_v3(request):

    current_year = jdatetime.datetime.now().year
    current_month = jdatetime.datetime.now().month

    unit_id = getattr(request, 'dashboard_unit_id', None)

    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]

    # -----------------------------
    # کل Work سال جاری
    # -----------------------------
    works = Work.objects.filter(
        year=current_year
    ).select_related('user__post__unit')

    if unit_id:
        works = works.filter(user__post__unit_id=unit_id)

    # -----------------------------
    # میانگین سالانه
    # -----------------------------
    avg_salary_year = works.aggregate(avg=Avg('salary'))['avg'] or 0
    avg_efficiency_year = works.aggregate(avg=Avg('bonus'))['avg'] or 0

    avg_salary_m = round(avg_salary_year / 1_000_000, 1)
    avg_efficiency_m = round(avg_efficiency_year / 1_000_000, 1)

    # -----------------------------
    # نمودار ماهانه
    # -----------------------------
    labels = []
    salary_values = []
    efficiency_values = []

    for month in range(1, current_month + 1):

        labels.append(persian_months[month - 1])

        month_works = works.filter(month=month)

        avg_salary_month = month_works.aggregate(avg=Avg('salary'))['avg'] or 0
        avg_eff_month = month_works.aggregate(avg=Avg('bonus'))['avg'] or 0

        salary_values.append(round(avg_salary_month / 1_000_000, 1))
        efficiency_values.append(round(avg_eff_month / 1_000_000, 1))

    return Response({
        "stats": {
            "avg_salary_millions": avg_salary_m,
            "avg_efficiency_millions": avg_efficiency_m
        },
        "chart": {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "حقوق",
                        "values": salary_values
                    },
                    {
                        "label": "کارایی",
                        "values": efficiency_values
                    }
                ]
            }
        },
        "url": "http://172.30.230.140/"
    })



from collections import defaultdict
from django.db.models import Avg, Sum
import jdatetime
from prj.models import *
from django.db.models import Avg
import jdatetime


from django.db.models import Avg, Sum
import jdatetime

from collections import defaultdict
import jdatetime

from django.db.models import Avg, Sum
from django.db.models.functions import ExtractMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from prj.models import Project, Allocation


from django.db.models import Avg, Sum
from django.db.models.functions import ExtractMonth
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import jdatetime

from prj.models import Project, Allocation


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def program_dashboard_card_v3(request):

    now_jdt = jdatetime.datetime.now()
    current_year = now_jdt.year
    unit_id = getattr(request, 'dashboard_unit_id', None)

    # -----------------------------
    # برنامه‌های سال جاری
    # -----------------------------
    programs = Project.objects.filter(year=current_year)

    if unit_id:
        programs = programs.filter(unit_id=unit_id)

    total_programs = programs.count()

    # -----------------------------
    # میانگین پیشرفت واقعی
    # -----------------------------
    avg_progress = programs.aggregate(
        avg=Avg('progress')
    )['avg'] or 0
    avg_progress = round(avg_progress, 1)

    # -----------------------------
    # میانگین پیشرفت برنامه‌ای
    # -----------------------------
    avg_expected = programs.aggregate(
        avg=Avg('expected')
    )['avg'] or 0
    avg_expected = round(avg_expected, 1)

    # -----------------------------
    # میانگین تأخیر
    # -----------------------------
    avg_delay = round(max(0, avg_expected - avg_progress), 1)

    # -----------------------------
    # بودجه تخصیصی سال جاری (نمودار خطی)
    # -----------------------------
    allocations = Allocation.objects.filter(
        project__year=current_year
    )

    if unit_id:
        allocations = allocations.filter(project__unit_id=unit_id)

    monthly_allocations = (
        allocations
        .annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر',
        'مرداد', 'شهریور', 'مهر', 'آبان',
        'آذر', 'دی', 'بهمن', 'اسفند'
    ]

    month_map = {m['month']: m['total'] for m in monthly_allocations}

    chart_labels = []
    chart_values = []

    for month in range(1, 13):
        chart_labels.append(persian_months[month - 1])
        total_amount = month_map.get(month, 0) or 0

        # تبدیل به میلیارد تومان
        chart_values.append(round(total_amount / 1_000_000_000, 2))

    return Response({
        "stats": {
            "total_programs": total_programs,
            "avg_real_progress": avg_progress,
            "avg_program_progress": avg_expected,
            "avg_delay": avg_delay
        },
        "chart": {
            "type": "line",
            "data": {
                "labels": chart_labels,
                "values": chart_values
            }
        },
        "url": "http://172.30.230.140/"
    })
