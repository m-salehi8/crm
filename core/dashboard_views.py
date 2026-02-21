from django.db.models import Avg
import jdatetime
from datetime import timedelta
import datetime
from core.models import User, Dashboard, DashboardAccess
from fn.models import Invoice
from hr.models import Profile, Work
from django.db.models import Sum, Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from pm.models import  FlowPattern, Node, Answer, Field, Flow, Job
from cn.models import Contract
from django.db.models import Max
from collections import defaultdict
from prj.models import Project, Allocation
from django.db.models.functions import ExtractMonth

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def procurement_process_stats(request):

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def petty_cash_stats(request):
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def human_resources_stats(request):
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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def program_dashboard_card(request):

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def contract_stats(request):

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meetings_stats(request):
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def tasks_stats(request):

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_dashboard_access()
def payroll_efficiency_stats(request):

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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def available_dashboards(request):
    """
    Returns dashboards that the current user can access, with order and chart relative URLs.
    { 'dashboards': [ { 'id', 'title', 'is_global', 'order', 'url' } ] }
    """
    # POST → آپدیت ترتیب بر اساس slug
    # ---------------------------

    if request.method == 'POST':

        slugs = request.data.get('slugs', [])

        if not isinstance(slugs, list) or not all(isinstance(s, str) for s in slugs):
            return Response(
                {'detail': 'آرایه‌ای از slugها ارسال کنید.'},
                status=400
            )

        if not slugs:
            return Response(
                {'detail': 'لیست slugها خالی است.'},
                status=400
            )

        accesses_qs = (
            DashboardAccess.objects
            .filter(user=request.user, dashboard__slug__in=slugs)
            .select_related('dashboard')
        )

        # ساخت map ترتیب جدید
        index_map = {slug: idx for idx, slug in enumerate(slugs)}

        to_update = []

        for acc in accesses_qs:
            new_order = index_map.get(acc.dashboard.slug)
            if new_order is not None and acc.order != new_order:
                acc.order = new_order
                to_update.append(acc)

        if to_update:
            DashboardAccess.objects.bulk_update(to_update, ['order'])

    # Map dashboard titles to relative URLs (adapt as your routes are defined)
    title_to_url = {
        'فرایند تأمین کالا': 'procurement',
        'قرارداد': 'contract',
        'تنخواه': 'petty-cash',
        'حقوق و کارایی': 'payroll',
        'منابع انسانی': 'hr',
        'مدیریت برنامه‌ها': 'program',
    }
    accesses = (
        DashboardAccess.objects
        .filter(user=request.user)
        .select_related('dashboard')
        .order_by('order', 'dashboard__id')
    )
    dashboards = [
        {
            'id': acc.dashboard.id,
            'title': acc.dashboard.title,
            'is_global': acc.is_global,
            'order': acc.order,
            'slug': acc.dashboard.slug,
            'url': f"/core/dashboard/charts/{acc.dashboard.slug}/"
        }
        for acc in accesses
    ]
    resp = {'dashboards': dashboards}
    resp["url"] = "http://172.30.230.140/"
    return Response(resp)

