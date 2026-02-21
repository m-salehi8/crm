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

    def get_base_queryset(self, user, archive, team):

        user_job_ids = set(
            Task.objects.filter(
                user=user,
                job__archive=archive
            ).values_list('job_id', flat=True)
        )

        informee_job_ids = set(
            Job.objects.filter(
                informees=user,
                archive=archive
            ).values_list('id', flat=True)
        )

        team_job_ids = set()

        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_job_ids = set(
                    Task.objects.filter(
                        user__in=team_users,
                        job__archive=archive
                    ).values_list('job_id', flat=True)
                )

        all_job_ids = user_job_ids | informee_job_ids | team_job_ids

        return Task.objects.filter(
            job_id__in=all_job_ids
        ).select_related('job', 'tag')


    def get(self, request):

        user = request.user
        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'
        tag_id = request.GET.get('tag')
        status_param = request.GET.get('status')

        base_qs = self.get_base_queryset(user, archive, team)

        # ------------------------------------------------
        # حالت pagination یک ستون
        # ------------------------------------------------
        if tag_id is not None and status_param is not None:

            if tag_id == "None":
                qs = base_qs.filter(
                    job__status=status_param,
                    tag__isnull=True
                )
            else:
                qs = base_qs.filter(
                    job__status=status_param,
                    tag_id=tag_id
                )

            qs = qs.order_by("job_id").distinct("job_id")

            paginator = ColumnPagination()
            page = paginator.paginate_queryset(qs, request)
            serializer = SerTaskList(page, many=True)

            return paginator.get_paginated_response(serializer.data)

        # ------------------------------------------------
        # حالت لود کل board
        # ------------------------------------------------
        statuses = ["todo", "doing", "done"]
        columns = []

        user_tags = list(user.tag_set.all())

        # ستون کارهای من
        user_tag_ids = set(user.tag_set.values_list('id', flat=True))

        columns_data = [
            {"id": None, "title": "کارهای من"},
            *[{"id": tag.id, "title": tag.title} for tag in user_tags]
        ]
        for column in columns_data:

            column_statuses = {}

            for st in statuses:
                print(column['id'])
                print("fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")

                if column["id"] is None:
                    qs = base_qs.filter(
                        job__status=st
                    ).filter(
                        Q(tag__isnull=True) | ~Q(tag_id__in=user_tag_ids)
                    )
                else:
                    qs = base_qs.filter(
                        job__status=st,
                        tag_id=column["id"]
                    )

                qs = qs.order_by("job_id").distinct("job_id")

                paginator = ColumnPagination()
                page = paginator.paginate_queryset(qs, request)
                serializer = SerTaskList(page, many=True)

                column_statuses[st] = {
                    "count": qs.count(),
                    "next": (
                        f"/pm/task-list/v2/?tag={column['id']}&status={st}&page=2"
                        if qs.count() > paginator.page_size else None
                    ),
                    "previous": None,
                    "results": serializer.data
                }

            columns.append({
                "id": column["id"],
                "title": column["title"],
                "statuses": column_statuses
            })

        return Response({
            "meta": {
                "archive": archive,
                "team": team,
                "page_size": 20,
                "generated_at": timezone.now()
            },
            "columns": columns
        })



class TaskListV4(GenericAPIView):
    """API نمایش تسک‌ها به تفکیک ستون‌ها و وضعیت‌ها"""
    permission_classes = [IsAuthenticated]

    def get_base_queryset(self, user, archive, team):
        """برگرداندن queryset پایه شامل کارهای کاربر، تیم و اطلاع‌رسانی"""
        user_job_ids = set(
            Task.objects.filter(user=user, job__archive=archive)
            .values_list('job_id', flat=True)
        )

        informee_job_ids = set(
            Job.objects.filter(informees=user, archive=archive)
            .values_list('id', flat=True)
        )

        team_job_ids = set()
        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_job_ids = set(
                    Task.objects.filter(user__in=team_users, job__archive=archive)
                    .values_list('job_id', flat=True)
                )

        all_job_ids = user_job_ids | informee_job_ids | team_job_ids

        return Task.objects.filter(job_id__in=all_job_ids).select_related('job', 'tag')

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'

        # اصلاح tag_id: تبدیل 'None' یا 'null' به None واقعی
        tag_id = request.GET.get('tag')
        if tag_id in ("None", "null"):
            tag_id = None

        status_param = request.GET.get('status')

        base_qs = self.get_base_queryset(user, archive, team)

        # -------------------------------
        # حالت pagination برای یک ستون
        # -------------------------------
        if status_param is not None:
            if tag_id is None:
                qs = base_qs.filter(job__status=status_param, tag__isnull=True)
            else:
                qs = base_qs.filter(job__status=status_param, tag_id=tag_id)

            qs = qs.order_by("job_id").distinct("job_id")
            paginator = ColumnPagination()
            page = paginator.paginate_queryset(qs, request)
            serializer = SerTaskList(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # -------------------------------
        # حالت لود کل board
        # -------------------------------
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
                    # ستون کارهای من: تسک‌های بدون تگ یا تگ‌های غیر از تگ‌های کاربر
                    qs = base_qs.filter(job__status=st).filter(
                        Q(tag__isnull=True) | ~Q(tag_id__in=user_tag_ids)
                    )

                    # Pagination روی queryset اصلی
                    paginator = ColumnPagination()
                    page_qs = paginator.paginate_queryset(qs.order_by("job_id"), request)

                    # distinct فقط روی صفحه
                    unique_page = {task.job_id: task for task in page_qs}.values()
                    serializer = SerTaskList(list(unique_page), many=True)

                    # تعداد کل distinct تسک‌ها برای ستون
                    count = qs.values("job_id").distinct().count()
                    column_total_count += count

                else:
                    # ستون تگ خاص
                    qs = base_qs.filter(job__status=st, tag_id=column["id"])
                    count = qs.count()
                    column_total_count += count

                    paginator = ColumnPagination()
                    page_qs = paginator.paginate_queryset(qs.order_by("job_id").distinct("job_id"), request)
                    serializer = SerTaskList(page_qs, many=True)

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





class TaskListV6(GenericAPIView):
    """API نمایش تسک‌ها به تفکیک ستون‌ها و وضعیت‌ها"""
    permission_classes = [IsAuthenticated]

    def get_base_queryset(self, user, archive, team):
        """برگرداندن queryset پایه شامل کارهای کاربر، تیم و اطلاع‌رسانی"""
        user_job_ids = set(
            Task.objects.filter(user=user, job__archive=archive)
            .values_list('job_id', flat=True)
        )

        informee_job_ids = set(
            Job.objects.filter(informees=user, archive=archive)
            .values_list('id', flat=True)
        )

        team_job_ids = set()
        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_job_ids = set(
                    Task.objects.filter(user__in=team_users, job__archive=archive)
                    .values_list('job_id', flat=True)
                )

        all_job_ids = user_job_ids | informee_job_ids | team_job_ids

        return Task.objects.filter(job_id__in=all_job_ids).select_related('job', 'tag')

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'

        # اصلاح tag_id: تبدیل 'None' یا 'null' به None واقعی
        tag_id = request.GET.get('tag')
        if tag_id in ("None", "null"):
            tag_id = None

        status_param = request.GET.get('status')

        base_qs = self.get_base_queryset(user, archive, team)

        # -------------------------------
        # حالت pagination برای یک ستون
        # -------------------------------
        if status_param is not None:
            if tag_id is None:
                # ستون بدون تگ → گرفتن job_idهای distinct
                qs_job_ids = base_qs.filter(job__status=status_param).filter(
                    Q(tag__isnull=True) | ~Q(tag_id__in=user.tag_set.values_list('id', flat=True))
                ).order_by("job_id").values_list("job_id", flat=True).distinct()

                paginator = ColumnPagination()
                page_job_ids = paginator.paginate_queryset(list(qs_job_ids), request)

                page_qs = base_qs.filter(job_id__in=page_job_ids).select_related('job', 'tag').order_by('job_id')
                serializer = SerTaskList(page_qs, many=True)

                count = qs_job_ids.count()

                return paginator.get_paginated_response(serializer.data)
            else:
                # ستون تگ خاص
                qs = base_qs.filter(job__status=status_param, tag_id=tag_id).order_by("job_id").distinct("job_id")
                paginator = ColumnPagination()
                page_qs = paginator.paginate_queryset(qs, request)
                serializer = SerTaskList(page_qs, many=True)
                return paginator.get_paginated_response(serializer.data)

        # -------------------------------
        # حالت لود کل board
        # -------------------------------
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
                    # ستون کارهای من: تسک‌های بدون تگ یا تگ‌های غیر از تگ‌های کاربر
                    qs_job_ids = base_qs.filter(job__status=st).filter(
                        Q(tag__isnull=True) | ~Q(tag_id__in=user_tag_ids)
                    ).order_by("job_id").values_list("job_id", flat=True).distinct()

                    paginator = ColumnPagination()
                    page_job_ids = paginator.paginate_queryset(list(qs_job_ids), request)

                    page_qs = base_qs.filter(job_id__in=page_job_ids).select_related('job', 'tag').order_by('job_id')
                    serializer = SerTaskList(page_qs, many=True)

                    count = qs_job_ids.count()
                    column_total_count += count
                else:
                    # ستون تگ خاص
                    qs = base_qs.filter(job__status=st, tag_id=column["id"])
                    count = qs.count()
                    column_total_count += count

                    paginator = ColumnPagination()
                    page_qs = paginator.paginate_queryset(qs.order_by("job_id").distinct("job_id"), request)
                    serializer = SerTaskList(page_qs, many=True)

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




class TaskListV8(GenericAPIView):

    def get_base_queryset(self, user, archive, team):
        """
        گرفتن تمام Taskهای مرتبط با کاربر: کارهای خودش، اطلاع‌رسانی‌ها، تیم
        """
        # تسک‌های خود کاربر
        user_tasks = Task.objects.filter(user=user, job__archive=archive)

        # تسک‌هایی که کاربر به عنوان مطلع است
        informee_tasks = Task.objects.filter(job__informees=user, job__archive=archive)

        # تسک‌های تیم
        team_tasks = Task.objects.none()
        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_tasks = Task.objects.filter(user__in=team_users, job__archive=archive)

        # merge کردن و distinct بر اساس job_id
        all_tasks = user_tasks.union(informee_tasks, team_tasks)
        return all_tasks

    def annotate_tasks(self, tasks, user):
        """
        اضافه کردن اطلاعات مالک و مطلع بودن
        """
        task_list = []
        for task in tasks:
            task_data = SerTaskList([task], many=True).data[0]
            # تعیین مالک
            task_data['job']['is_owner'] = task.user_id == user.id
            # تعیین مطلع بودن
            task_data['job']['is_informees'] = user in task.job.informees.all()
            task_list.append(task_data)
        return task_list

    def paginate_tasks(self, tasks, request):
        paginator = ColumnPagination()
        page = paginator.paginate_queryset(tasks, request)
        return page, paginator

    def get(self, request):
        user = request.user
        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'
        tag_param = request.GET.get('tag')
        status_param = request.GET.get('status')

        # ------------------------------------------------
        # گرفتن Taskها
        # ------------------------------------------------
        base_qs = self.get_base_queryset(user, archive, team)

        # تبدیل queryset به لیست برای پردازش و جلوگیری از تکراری
        all_tasks = self.annotate_tasks(base_qs, user)

        # ------------------------------------------------
        # حالت pagination یک ستون خاص
        # ------------------------------------------------
        if tag_param is not None and status_param is not None:
            if tag_param in ["None", "null"]:
                filtered_tasks = [t for t in all_tasks if t['job']['status'] == status_param and t['tag'] is None]
            else:
                try:
                    tag_id = int(tag_param)
                    filtered_tasks = [t for t in all_tasks if t['job']['status'] == status_param and t['tag'] == tag_id]
                except ValueError:
                    filtered_tasks = []

            page, paginator = self.paginate_tasks(filtered_tasks, request)
            return paginator.get_paginated_response(page)

        # ------------------------------------------------
        # حالت لود کل board
        # ------------------------------------------------
        statuses = ["todo", "doing", "done"]
        columns = []

        user_tags = list(user.tag_set.all())
        columns_data = [{"id": None, "title": "کارهای من"}] + [
            {"id": tag.id, "title": tag.title} for tag in user_tags
        ]

        for column in columns_data:
            column_statuses = {}
            for st in statuses:
                # فیلتر بر اساس ستون و وضعیت
                if column['id'] is None:
                    filtered = [t for t in all_tasks if t['job']['status'] == st and (t['tag'] is None or t['tag'] not in [tag.id for tag in user_tags])]
                else:
                    filtered = [t for t in all_tasks if t['job']['status'] == st and t['tag'] == column['id']]

                # صفحه‌بندی
                page, paginator = self.paginate_tasks(filtered, request)
                column_statuses[st] = {
                    "count": len(filtered),
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": page
                }

            columns.append({
                "id": column['id'],
                "title": column['title'],
                "statuses": column_statuses
            })

        return Response({
            "meta": {
                "archive": archive,
                "team": team,
                "page_size": ColumnPagination.page_size,
                "generated_at": timezone.now()
            },
            "columns": columns
        })




class TaskListV6(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get_base_queryset(self, user, archive, team):
        # Jobهای کاربر
        user_job_ids = set(Task.objects.filter(user=user, job__archive=archive)
                           .values_list('job_id', flat=True).distinct())
        # Jobهای اطلاع‌رسانی
        informee_job_ids = set(Job.objects.filter(informees=user, archive=archive)
                               .values_list('id', flat=True).distinct())
        # Jobهای تیم
        team_job_ids = set()
        if team:
            team_users = get_all_subordinates(user)
            if team_users.exists():
                team_job_ids = set(Task.objects.filter(user__in=team_users, job__archive=archive)
                                   .values_list('job_id', flat=True).distinct())

        all_job_ids = user_job_ids | informee_job_ids | team_job_ids
        return Task.objects.filter(job_id__in=all_job_ids).select_related('job', 'tag')

    def get_paginated_jobs(self, qs, request):
        """
        صفحه‌بندی بر اساس Job نه Task تکراری
        """
        # distinct job_ids
        job_ids = qs.order_by('job_id').values_list('job_id', flat=True).distinct()
        paginator = ColumnPagination()
        page_job_ids = paginator.paginate_queryset(list(job_ids), request)

        # برای هر Job فقط یک Task (مثلاً کوچکترین id)
        page_qs = (qs.filter(job_id__in=page_job_ids)
                     .order_by('job_id', 'id')
                     .distinct('job_id'))  # distinct بر اساس Job
        serializer = SerTaskList(page_qs, many=True)
        return paginator, serializer

    def get(self, request):
        user = request.user
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
                qs = base_qs.filter(job__status=status_param).filter(
                    Q(tag__isnull=True) | ~Q(tag_id__in=user.tag_set.values_list('id', flat=True))
                )
            else:
                qs = base_qs.filter(job__status=status_param, tag_id=tag_id)

            paginator, serializer = self.get_paginated_jobs(qs, request)
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
                    )
                else:
                    qs = base_qs.filter(job__status=st, tag_id=column["id"])

                paginator, serializer = self.get_paginated_jobs(qs, request)
                count = qs.values_list('job_id', flat=True).distinct().count()
                column_total_count += count

                column_statuses[st] = {
                    "count": count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
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



class TaskListV3(GenericAPIView):
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
        return Task.objects.filter(job_id__in=all_job_ids).select_related('job', 'tag')

    def get_paginated_jobs(self, qs, request):
        """صفحه‌بندی روی Jobها، بدون تکرار"""
        job_ids = qs.values_list('job_id', flat=True).distinct()
        paginator = ColumnPagination()
        page_job_ids = paginator.paginate_queryset(list(job_ids), request)
        page_qs = qs.filter(job_id__in=page_job_ids).select_related('job', 'tag').order_by('job_id')
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

        # حالت Pagination یک ستون (برای تگ مشخص یا بدون تگ)
        if status_param is not None:
            if tag_id is None:
                qs = base_qs.filter(
                    job__status=status_param
                ).filter(
                    Q(tag__isnull=True) | ~Q(tag_id__in=user.tag_set.values_list('id', flat=True))
                )
            else:
                qs = base_qs.filter(job__status=status_param, tag_id=tag_id)

            paginator, serializer = self.get_paginated_jobs(qs, request)
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
                    )
                else:
                    qs = base_qs.filter(job__status=st, tag_id=column["id"])

                paginator, serializer = self.get_paginated_jobs(qs, request)
                job_count = qs.values_list('job_id', flat=True).distinct().count()
                column_total_count += job_count

                column_statuses[st] = {
                    "count": job_count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
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
