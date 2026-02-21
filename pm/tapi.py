from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q
from pm.views import *

class ColumnPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"



class TaskListV4(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_base_queryset(self, user, archive, team):
        user_job_ids = set(Task.objects.filter(user=user, job__archive=archive)
                           .values_list('job_id', flat=True).distinct())
        informee_job_ids = set(Job.objects.filter(informees=user, archive=archive)
                               .values_list('id', flat=True).distinct())
        team_job_ids = set()
        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_job_ids = set(Task.objects.filter(user__in=team_users, job__archive=archive)
                                   .values_list('job_id', flat=True))

        all_job_ids = user_job_ids | informee_job_ids | team_job_ids
        return Task.objects.filter(job_id__in=all_job_ids).select_related('job', 'tag').distinct()

    def get_paginated_tasks(self, qs, request):
        """صفحه‌بندی روی Task بدون تکرار job"""
        # distinct job_ids برای جلوگیری از تکرار
        job_ids = qs.order_by('job_id').values_list('job_id', flat=True).distinct()
        paginator = ColumnPagination()
        page_job_ids = paginator.paginate_queryset(list(job_ids), request)

        page_qs = qs.filter(job_id__in=page_job_ids).order_by('job_id').distinct()
        serializer = SerTaskList(page_qs, many=True)
        return paginator, serializer

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'
        tag_id = request.GET.get('tag')
        if tag_id in ("None", "null"):
            tag_id = None
        status_param = request.GET.get('status')

        base_qs = self.get_base_queryset(user, archive, team)

        # حالت pagination یک ستون
        if status_param is not None:
            if tag_id is None:
                qs = base_qs.filter(Q(tag__isnull=True) | ~Q(tag_id__in=user.tag_set.values_list('id', flat=True)),
                                     job__status=status_param).distinct()
            else:
                qs = base_qs.filter(job__status=status_param, tag_id=tag_id).distinct()

            paginator, serializer = self.get_paginated_tasks(qs, request)
            return paginator.get_paginated_response(serializer.data)

        # حالت لود کل board
        statuses = ["todo", "doing", "done"]
        columns = []
        user_tags = list(user.tag_set.all())
        user_tag_ids = set(user.tag_set.values_list('id', flat=True))

        columns_data = [{"id": None, "title": "کارهای من"}] + [
            {"id": tag.id, "title": tag.title} for tag in user_tags
        ]

        total_board_count = 0

        for column in columns_data:
            column_statuses = {}
            column_total_count = 0

            for st in statuses:
                if column["id"] is None:
                    qs = base_qs.filter(job__status=st).filter(
                        Q(tag__isnull=True) | ~Q(tag_id__in=user_tag_ids)
                    ).distinct()
                else:
                    qs = base_qs.filter(job__status=st, tag_id=column["id"]).distinct()

                paginator, serializer = self.get_paginated_tasks(qs, request)
                count = qs.values_list('job_id', flat=True).distinct().count()
                column_total_count += count

                column_statuses[st] = {
                    "count": count,
                    "next": (
                        f"/pm/task-list/v2/?tag={column['id']}&status={st}&page=2"
                        if count > paginator.page_size else None
                    ),
                    "previous": None,
                    "results": serializer.data
                }

            total_board_count += column_total_count

            columns.append({
                "id": column["id"],
                "title": column["title"],
                "total_count": column_total_count,
                "statuses": column_statuses
            })

        return Response({
            "meta": {
                "archive": archive,
                "team": team,
                "page_size": ColumnPagination.page_size,
                "generated_at": timezone.now(),
                "total_board_count": total_board_count
            },
            "columns": columns
        })


from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count, Prefetch, Exists, OuterRef
from django.db import connection
from collections import defaultdict
from pm.models import Job, Task, Tag
from pm.views import SerTaskList
import logging

logger = logging.getLogger(__name__)


class OptimizedColumnPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class TaskListV5(GenericAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = OptimizedColumnPagination

    def get_base_queryset(self, user, archive, team):
        """
        دریافت Taskهای مجاز برای کاربر
        بر اساس مدل‌های دقیق:
        - Task.user = کاربر (وظایف مستقیم)
        - Job.informees = کاربر (مطلعین)
        - از طریق تیم (زیردستان)
        """

        # ================ روش بهینه با Q objects ================

        # شرط اصلی: job باید archive مناسب داشته باشد
        base_condition = Q(job__archive=archive)

        # 1. تسک‌های مستقیم کاربر
        direct_condition = Q(user=user)

        # 2. jobهایی که کاربر در informees است
        # با استفاده از Exists برای بهینه‌تر شدن
        informee_condition = Q(
            job__informees=user
        )

        # 3. تسک‌های تیم (زیردستان)
        team_condition = Q()
        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_condition = Q(user__in=team_users)

        # ترکیب همه شرایط
        final_condition = (direct_condition | informee_condition | team_condition)

        # کوئری نهایی با select_related بهینه
        return Task.objects.filter(
            final_condition,
            job__archive=archive
        ).select_related(
            'job', 'tag'
        ).only(
            'id', 'job_id', 'tag_id', 'user_id', 'is_owner', 'is_committed', 'order',
            'job__id', 'job__title', 'job__status', 'job__archive',
            'job__deadline', 'job__urgency', 'job__create_time',
            'job__done_time', 'job__confirm', 'job__session_id',
            'tag__id', 'tag__title', 'tag__user_id', 'tag__order'
        ).distinct()

    def get_job_ids_for_pagination(self, base_qs, tag_id, status, user_tag_ids):
        """
        دریافت job_idهای منحصربفرد برای صفحه‌بندی
        با در نظر گرفتن فیلتر تگ و وضعیت
        """
        if tag_id is None or tag_id == 'None' or tag_id == 'null':
            # کارهای من: تسک‌هایی که تگ ندارند یا تگ آنها متعلق به کاربر نیست
            # با استفاده از Subquery برای بهینه‌سازی
            user_tags_subquery = Tag.objects.filter(
                user=user,
                id=OuterRef('tag_id')
            )

            qs = base_qs.filter(
                job__status=status
            ).filter(
                # یا تگ ندارند
                Q(tag__isnull=True) |
                # یا تگ آنها متعلق به کاربر نیست
                Q(~Exists(user_tags_subquery))
            )
        else:
            # کارهای یک تگ خاص
            qs = base_qs.filter(
                tag_id=tag_id,
                job__status=status
            )

        # دریافت job_idهای یکتا
        return qs.values_list('job_id', flat=True).distinct().order_by('job_id')

    def get_column_statistics(self, base_qs, user, user_tag_ids):
        """
        محاسبه آمار تمام ستون‌ها با یک کوئری
        با استفاده از aggregation پیشرفته
        """

        # ایجاد annotation برای دسته‌بندی وضعیت‌ها
        status_counts = base_qs.values(
            'tag_id', 'job__status'
        ).annotate(
            count=Count('job_id', distinct=True)
        ).order_by()

        # ساختار خروجی
        stats = defaultdict(lambda: defaultdict(int))

        for item in status_counts:
            tag_id = item['tag_id'] if item['tag_id'] is not None else 'null'
            status = item['job__status']
            stats[tag_id][status] = item['count']

        return stats

    def get_paginated_response_for_column(self, request, base_qs, tag_id, status, user_tag_ids):
        """
        ایجاد پاسخ صفحه‌بندی شده برای یک ستون خاص
        """
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', self.pagination_class.page_size))

        # دریافت job_idهای این ستون و وضعیت
        job_ids_qs = self.get_job_ids_for_pagination(base_qs, tag_id, status, user_tag_ids)

        # صفحه‌بندی در سطح job_id
        from django.core.paginator import Paginator
        paginator = Paginator(list(job_ids_qs), page_size)

        try:
            page_obj = paginator.page(page)
            page_job_ids = page_obj.object_list
        except Exception:
            page_obj = paginator.page(1)
            page_job_ids = page_obj.object_list

        # دریافت Taskهای مربوط به job_idهای این صفحه
        # فقط یک Task از هر Job (با distinct)
        tasks = base_qs.filter(
            job_id__in=page_job_ids
        ).order_by('job_id').distinct('job_id')

        # سریالایز کردن
        serializer = SerTaskList(tasks, many=True)

        # ساخت لینک‌های next/previous
        base_url = request.build_absolute_uri().split('?')[0]
        params = []
        if request.GET.get('archive') == 'true':
            params.append('archive=true')
        if request.GET.get('team') == 'true':
            params.append('team=true')
        if tag_id is not None and tag_id != 'None':
            params.append(f'tag={tag_id}')
        if status:
            params.append(f'status={status}')
        params.append(f'page_size={page_size}')

        base_param_str = '&'.join(params)

        next_page = None
        previous_page = None

        if page_obj.has_next():
            next_page = f"{base_url}?{base_param_str}&page={page + 1}"

        if page_obj.has_previous():
            previous_page = f"{base_url}?{base_param_str}&page={page - 1}"

        return {
            'meta': {
                'page': page_obj.number,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
            },
            'results': serializer.data,
            'next': next_page,
            'previous': previous_page,
        }

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        # دریافت پارامترها
        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'
        tag_id = request.GET.get('tag')
        if tag_id in ("None", "null", ""):
            tag_id = None

        status_param = request.GET.get('status')

        # دریافت base queryset
        base_qs = self.get_base_queryset(user, archive, team)

        # دریافت تگ‌های کاربر
        user_tags = list(user.tag_set.all().order_by('order', 'id'))
        user_tag_ids = [tag.id for tag in user_tags]

        # ================ حالت 1: صفحه‌بندی یک ستون خاص ================
        if status_param and status_param in ['todo', 'doing', 'done']:
            result = self.get_paginated_response_for_column(
                request, base_qs, tag_id, status_param, user_tag_ids
            )

            return Response({
                'meta': {
                    'archive': archive,
                    'team': team,
                    'tag': tag_id,
                    'status': status_param,
                    'generated_at': timezone.now(),
                    'query_count': len(connection.queries),
                    **result['meta']
                },
                'results': result['results'],
                'next': result['next'],
                'previous': result['previous'],
            })

        # ================ حالت 2: لود کامل board ================

        # محاسبه آمار با یک کوئری
        stats = self.get_column_statistics(base_qs, user, user_tag_ids)

        columns = []

        # ستون "کارهای من" (بدون تگ یا تگ خارج از تگ‌های کاربر)
        my_tasks_counts = defaultdict(int)
        for status in ['todo', 'doing', 'done']:
            # کارهای بدون تگ
            my_tasks_counts[status] += stats['null'].get(status, 0)

        my_tasks_total = sum(my_tasks_counts.values())

        my_tasks_column = {
            'id': None,
            'title': 'کارهای من',
            'total_count': my_tasks_total,
            'statuses': {
                status: {
                    'count': my_tasks_counts[status],
                    'next': f"/pm/task-list/v5/?status={status}&page=2" if my_tasks_counts[status] > 0 else None
                }
                for status in ['todo', 'doing', 'done']
            }
        }
        columns.append(my_tasks_column)

        # ستون‌های تگ‌ها
        for tag in user_tags:
            tag_counts = defaultdict(int)
            for status in ['todo', 'doing', 'done']:
                tag_counts[status] = stats.get(tag.id, {}).get(status, 0)

            tag_total = sum(tag_counts.values())

            tag_column = {
                'id': tag.id,
                'title': tag.title,
                'total_count': tag_total,
                'statuses': {
                    status: {
                        'count': tag_counts[status],
                        'next': f"/pm/task-list/v5/?tag={tag.id}&status={status}&page=2" if tag_counts[
                                                                                                status] > 0 else None
                    }
                    for status in ['todo', 'doing', 'done']
                }
            }
            columns.append(tag_column)

        # محاسبه کل آیتم‌های board
        total_board_count = sum(col['total_count'] for col in columns)

        # لاگ performance
        logger.info(
            f"TaskListV5 - User: {user.id}, Archive: {archive}, Team: {team}, "
            f"Total: {total_board_count}, Queries: {len(connection.queries)}"
        )

        return Response({
            'meta': {
                'archive': archive,
                'team': team,
                'page_size': self.pagination_class.page_size,
                'generated_at': timezone.now(),
                'total_board_count': total_board_count,
                'query_count': len(connection.queries),
            },
            'columns': columns
        })


# ================ نسخه با کش برای performance بهتر ================
from django.core.cache import cache
import hashlib
import json


class CachedTaskListV5(TaskListV5):
    """
    نسخه کش شده برای کاهش بار دیتابیس
    """
    CACHE_TIMEOUT = 300  # 5 دقیقه

    def get_cache_key(self, user_id, archive, team, tag_id, status, page, page_size):
        """ساخت کلید کش یکتا"""
        key_parts = [
            f"tasklist_v5",
            f"user:{user_id}",
            f"archive:{archive}",
            f"team:{team}",
            f"tag:{tag_id}",
            f"status:{status}",
            f"page:{page}",
            f"size:{page_size}"
        ]
        key_string = "_".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        # استخراج پارامترها
        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'
        tag_id = request.GET.get('tag')
        status = request.GET.get('status')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', self.pagination_class.page_size))

        # ساخت کلید کش
        cache_key = self.get_cache_key(user.id, archive, team, tag_id, status, page, page_size)

        # تلاش برای دریافت از کش
        cached_response = cache.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for {cache_key}")
            return Response(cached_response)

        logger.debug(f"Cache miss for {cache_key}")

        # اگر در کش نبود، محاسبه کن
        response = super().get(request)

        # ذخیره در کش (فقط برای درخواست‌های صفحه‌بندی شده)
        if status is not None:  # فقط درخواست‌های تکی را کش کن
            cache.set(cache_key, response.data, self.CACHE_TIMEOUT)

        return response