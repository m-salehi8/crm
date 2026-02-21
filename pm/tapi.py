from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q
from pm.views import *

class ColumnPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


def _patch_task_list_response(results, informee_job_ids):
    """برای سازگاری با TaskList: is_owner و is_informees روی job ست می‌شود."""
    informee_set = set(informee_job_ids) if informee_job_ids is not None else set()
    for item in results:
        if isinstance(item, dict) and 'job' in item and isinstance(item['job'], dict):
            item['job']['is_owner'] = True
            item['job']['is_informees'] = item['job'].get('id') in informee_set
    return results


def _parse_int_list(param_value):
    """تبدیل پارامتر چندمقداره به لیست اعداد معتبر (مثلاً '1,2,3' یا '1')."""
    if not param_value or param_value.strip() in ('None', 'null', ''):
        return None
    out = []
    for x in param_value.split(','):
        x = x.strip()
        if x.isdigit():
            out.append(int(x))
    return out if out else None


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
        return Task.objects.filter(job_id__in=all_job_ids).select_related('job', 'tag')

    def get_informee_job_ids(self, user, archive):
        return set(Job.objects.filter(informees=user, archive=archive).values_list('id', flat=True))

    def apply_filters(self, qs, search, creator_ids, assignee_ids):
        """اعمال فیلتر جستجو، ایجادکننده و مسئول روی کوئری‌ست."""
        if search and search.strip():
            qs = qs.filter(
                Q(job__title__icontains=search.strip()) | Q(job__note__icontains=search.strip())
            )
        if creator_ids:
            owner_job_ids = Task.objects.filter(
                is_owner=True, user_id__in=creator_ids
            ).values_list('job_id', flat=True).distinct()
            qs = qs.filter(job_id__in=owner_job_ids)
        if assignee_ids:
            qs = qs.filter(user_id__in=assignee_ids)
        return qs

    def get_paginated_tasks(self, qs, request, informee_job_ids):
        """صفحه‌بندی روی Task؛ برای هر job فقط یک تسک برمی‌گردد (PostgreSQL distinct('job_id'))."""
        job_ids = qs.order_by('job_id').values_list('job_id', flat=True).distinct()
        paginator = ColumnPagination()
        page_job_ids = paginator.paginate_queryset(list(job_ids), request)

        # یک تسک به ازای هر job (مثل get_task_list)
        page_qs = qs.filter(job_id__in=page_job_ids).order_by('job_id', 'id').distinct('job_id')
        serializer = SerTaskList(page_qs, many=True, context={'request': request, 'user': request.user})
        data = _patch_task_list_response(serializer.data, informee_job_ids)
        return paginator, data

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        # فیلترها
        archive = request.GET.get('archive', 'false') == 'true'
        team = request.GET.get('team', 'false') == 'true'
        search = (request.GET.get('search') or request.GET.get('q') or '').strip() or None
        creator_ids = _parse_int_list(request.GET.get('creators') or request.GET.get('creator'))
        assignee_ids = _parse_int_list(request.GET.get('assignees') or request.GET.get('assignee'))

        tag_id = request.GET.get('tag')
        if tag_id in ("None", "null"):
            tag_id = None
        status_param = request.GET.get('status')

        base_qs = self.get_base_queryset(user, archive, team)
        base_qs = self.apply_filters(base_qs, search, creator_ids, assignee_ids)
        informee_job_ids = self.get_informee_job_ids(user, archive)

        # حالت pagination یک ستون
        if status_param is not None:
            if tag_id is None:
                qs = base_qs.filter(
                    Q(tag__isnull=True) | ~Q(tag_id__in=user.tag_set.values_list('id', flat=True)),
                    job__status=status_param
                )
            else:
                qs = base_qs.filter(job__status=status_param, tag_id=tag_id)

            paginator, data = self.get_paginated_tasks(qs, request, informee_job_ids)
            return paginator.get_paginated_response(data)

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

                paginator, data = self.get_paginated_tasks(qs, request, informee_job_ids)
                count = qs.values_list('job_id', flat=True).distinct().count()
                column_total_count += count

                # لینک صفحه بعد با پارامترهای کامل (archive, team, tag, status)
                next_url = None
                if count > paginator.page_size:
                    qparams = request.GET.copy()
                    qparams['tag'] = column['id']
                    qparams['status'] = st
                    qparams['page'] = 2
                    next_url = request.build_absolute_uri(request.path) + '?' + qparams.urlencode()

                column_statuses[st] = {
                    "count": count,
                    "next": next_url,
                    "previous": None,
                    "results": data
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
                "search": search,
                "creators": creator_ids or [],
                "assignees": assignee_ids or [],
                "page_size": ColumnPagination.page_size,
                "generated_at": timezone.now(),
                "total_board_count": total_board_count
            },
            "columns": columns
        })
