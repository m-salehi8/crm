import operator
import jdatetime
from core.models import User, Notification
from core.permissions import IsPmUser
from core.serializers import SerUserList
from .models import ProjectsTeam, PhaseTeam
from .serializers import *
from functools import reduce
from django.db.models import Q, F, Sum, Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView, DestroyAPIView, get_object_or_404, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView

class MissionList(ListAPIView):
    serializer_class = SerMission

    def get_queryset(self):
        return Mission.objects.filter(units__in=[self.request.user.post.unit])


class ProjectList(ListAPIView):
    serializer_class = SerProjectList

    def get_queryset(self):
        unit_id = int(self.request.GET['unit'])
        subunit_id = int(self.request.GET['subunit'])
        year = int(self.request.GET['year'])
        user = self.request.user
        if user.groups.filter(name='supervisor').exists() or user.post.is_deputy or (user.groups.filter(name='pm').exists() and (user.post.unit_id == subunit_id or user.post.unit_id == unit_id)):
            return Project.objects.filter(unit_id=subunit_id, year=year) if subunit_id else Project.objects.filter(year=year).filter(Q(unit__parent_id=unit_id) | Q(unit_id=unit_id))
        return Project.objects.filter(id=0)


class ProjectDetail(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        project = Project.objects.prefetch_related('phases', 'phases__reports', 'contracts', 'allocations').get(pk=pk)
        if user.post.is_deputy or user.groups.filter(name='supervisor').exists() or user.groups.filter(name='pm').exists() and (user.post.unit == project.unit or user.post.unit == project.unit.parent):
            return Response(data=SerProjectDetail(project, context={'user': user}).data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class ProjectAddOrUpdate(GenericAPIView):
    def post(self, request):
        if request.data['id']:
            project = get_object_or_404(Project, id=request.data['id'])
            if (project.accepted is True and project.approved is not False) or project.unit != request.user.post.unit or request.user.groups.filter(name='pm').exists() is False:
                return Response(data='شما دسترسی ویرایش این برنامه را ندارید', status=status.HTTP_403_FORBIDDEN)
            project.title = request.data['title']
            project.priority = request.data.get('priority', 1)
            project.priority_percentage = request.data.get('priority_percentage', 0)
            project.year = request.data['year']
            project.note = request.data['note']
            project.accepted = None
            project.approved = None
            project.save()
            project.missions.set(request.data['missions'])
            project.team.set(request.data['team'])
            try:
                team_prj = request.data['team_percent']
                new_user_ids = [int(uid) for uid in team_prj.keys()]
                ProjectsTeam.objects.filter(project=project) \
                    .exclude(user_id__in=new_user_ids) \
                    .delete()

                for user_id, percentage in team_prj.items():
                    ins, created = ProjectsTeam.objects.update_or_create(
                        project=project,
                        user_id=int(user_id),
                        defaults={'participation_percentage': percentage}
                    )

            except:
                pass

            return Response(data=SerProjectDetail(project, context={'user': request.user}).data)
        else:

            if not request.user.groups.filter(name='pm').exists():
                return Response(data='شما دسترسی ثبت برنامه ندارید', status=status.HTTP_403_FORBIDDEN)
            project = Project.objects.create(title=request.data['title'], priority=3, priority_percentage=request.data.get('priority_percentage', 0),  unit=request.user.post.unit, year=request.data['year'], note=request.data['note'])
            project.missions.set(request.data['missions'])
            project.team.set(request.data['team'])

            team_prj = request.data['team_percent']

            for user_id, percentage in team_prj.items():

                user = User.objects.get(id=user_id)
                ins = ProjectsTeam()
                ins.project = project
                ins.user = user
                ins.participation_percentage = int(percentage)
                ins.save()

            return Response(data=SerProjectDetail(project, context={'user': request.user}).data)





class ProjectRemove(DestroyAPIView):
    def get_queryset(self):
        return Project.objects.filter(unit=self.request.user.post.unit, confirmed=False)


class PhaseAddOrUpdate(GenericAPIView):
    def post(self, request):
        project = get_object_or_404(Project, id=request.data['project'])

        print(request.data)
        print("*"*20)
        if (project.accepted is True and project.approved is not False) or project.unit != request.user.post.unit or request.user.groups.filter(name='pm').exists() is False:
            return Response(data='شما دسترسی ویرایش این برنامه را ندارید', status=status.HTTP_403_FORBIDDEN)
        if request.data['id']:
            print("lllllllllllllllllllllllllllllllllllllllllllllllllllllllllllllll")
            phase = get_object_or_404(Phase, id=request.data['id'], project=project)
            ser = SerPhaseForm(instance=phase, data=request.data)



        else:
            print('ggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg')
            ser = SerPhaseForm(data=request.data)
        if ser.is_valid():
            ser.save()
            return Response(data=SerProjectDetail(project, context={'user': request.user}).data)
        else:
            return Response(data=ser.errors, status=status.HTTP_400_BAD_REQUEST)


class PhaseRemove(GenericAPIView):
    def post(self, request):
        phase = get_object_or_404(Phase, id=request.data['id'])
        project = phase.project
        if (project.accepted and project.approved is not False) or project.unit != request.user.post.unit or not request.user.groups.filter(name='pm').exists():
            return Response(data='شما دسترسی ویرایش این برنامه را ندارید', status=status.HTTP_403_FORBIDDEN)
        phase.delete()
        return Response(data=SerProjectDetail(project, context={'user': request.user}).data)


class PhaseReportList(GenericAPIView):
    def get(self, request, pk):
        phase = get_object_or_404(Phase, id=pk)
        if request.user.groups.filter(name='supervisor').exists() or request.user.post.unit == phase.project.unit:
            return Response(SerReportList(phase.reports, many=True).data)


class ProjectConfirmOrAccept(GenericAPIView):
    def post(self, request):
        project = get_object_or_404(Project, id=request.data['id'])
        if request.user.post.unit != project.unit and project.confirmed is False:
            return Response(data='برنامه هنوز توسط مدیر اداره تأیید اولیه نشده است', status=status.HTTP_400_BAD_REQUEST)
        if request.user.post.is_deputy and (project.unit == request.user.post.unit or project.unit.parent == request.user.post.unit and project.confirmed) and project.accepted is None:
            project.confirmed = True
            project.accepted = request.data['accept']
            project.accept_note = request.data['note']
            project.accept_date = jdatetime.datetime.now().date()
            project.save()
            return Response(data=SerProjectDetail(project, context={'user': request.user}).data)
        if project.confirmed is False and request.user.post.is_manager and project.unit == request.user.post.unit:
            project.confirmed = True
            project.save()
            return Response(data=SerProjectDetail(project, context={'user': request.user}).data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class ProjectApprove(GenericAPIView):
    def post(self, request):
        project = get_object_or_404(Project, id=request.data['id'])
        if project.accepted and project.approved is None and request.user.groups.filter(name='project').exists():
            project.approved = request.data['approve']
            project.approve_note = request.data['note']
            project.approve_date = jdatetime.datetime.now().date()
            project.save()
            data = {
                'project': SerProjectDetail(project, context={'user': request.user}).data,
                'todo_project': request.user.todo_project
            }
            return Response(data=data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class ReportList(GenericAPIView):
    def get(self, request):
        unit = int(request.GET.get('unit', 0))
        accept = request.GET.get('accept', 'all')
        approve = request.GET.get('approve', 'all')
        has_file = request.GET.get('has_file', 'all')
        q = request.GET.get('q', None)
        if request.user.groups.filter(name='supervisor').exists():
            report_list = Report.objects.all()
        else:
            report_list = Report.objects.filter(phase__project__unit=request.user.post.unit)
        if unit:
            report_list = report_list.filter(Q(phase__project__unit_id=unit) | Q(phase__project__unit__parent_id=unit))
        if accept != 'all':
            report_list = report_list.filter(accepted=True if accept == 'yes' else False if accept == 'no' else None)
        if approve != 'all':
            report_list = report_list.filter(approved=True if approve == 'yes' else False if approve == 'no' else None)
        if has_file == 'yes':
            report_list = report_list.annotate(val=Count('appendices')).filter(val__gt=0)
        elif has_file == 'no':
            report_list = report_list.annotate(val=Count('appendices')).filter(val=0)
        if q:
            q_list = q.split(' ')
            q_filter = reduce(operator.and_, (Q(phase__project__title__contains=q_text) | Q(phase__title__contains=q_text) for q_text in q_list))
            report_list = report_list.filter(q_filter)
        size = request.user.profile.page_size
        page = min(int(request.GET.get('page', 1)), report_list.count() // size + 1)
        data = {
            'count': report_list.count(),
            'page': page,
            'size': size,
            'list': SerReportDetail(instance=report_list[size*(page-1):size*page], many=True, context={'user': request.user}).data
        }
        return Response(data=data)


class ReportAdd(GenericAPIView):
    def post(self, request):
        phase = get_object_or_404(Phase, id=request.data['phase'])
        if phase.project.approved and (phase.project.unit == request.user.post.unit or phase.project.unit.parent == request.user.post.parent):
            report = phase.reports.create(progress_claimed=request.data['progress_claimed'], claim_note=request.data['claim_note'])
            for file in request.data.getlist('new_files', []):
                report.appendices.create(file=file)
            return Response(data=SerReportDetail(report, context={'user': request.user}).data)
        return Response(data='شما دسترسی ثبت گزارش برای این پروژه ندارید', status=status.HTTP_403_FORBIDDEN)


class ReportRemove(GenericAPIView):
    def post(self, request):
        report = get_object_or_404(Report, id=request.data['id'], phase__project__unit=request.user.post.unit, approved=None)
        report.delete()
        return Response(data='removed')


class ReportAccept(GenericAPIView):
    def post(self, request):
        report = get_object_or_404(Report, id=request.data['id'])
        if report.accepted is None and request.user.post.unit == report.phase.project.unit and request.user.post.is_manager:
            report.accepted = request.data['accepted']
            report.accept_note = request.data['accept_note']
            if report.accepted:
                report.progress_accepted = request.data['progress_accepted']
            else:
                for u in User.objects.filter(groups__name='pm', post__unit=report.phase.project.unit):
                    Notification.objects.create(user=u, title='گزارش پیشرفت پروژه نیاز به بازنگری دارد', body=report.phase.project.title, url=f'/project/{report.phase.project.id}')
            report.save()
            return Response(data=SerReportDetail(report, context={'user': request.user}).data)
        return Response(data='شما دسترسی ویرایش این گزارش را ندارید', status=status.HTTP_403_FORBIDDEN)


class ReportApprove(GenericAPIView):
    def post(self, request):
        report = get_object_or_404(Report, id=request.data['id'])
        if report.approved is None and request.user.groups.filter(name='project').exists():
            report.approved = request.data['approved']
            report.approve_note = request.data['approve_note']
            if report.approved:
                report.progress_approved = request.data['progress_approved']
            report.save()
            data = {
                'report': SerReportDetail(report, context={'user': request.user}).data,
                'todo_report': request.user.todo_report
            }
            return Response(data=data)
        return Response(data='شما دسترسی ویرایش این گزارش را ندارید', status=status.HTTP_403_FORBIDDEN)


class ProjectAllocations(GenericAPIView):
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if request.user.post.unit == project.unit or request.user.groups.filter(name='supervisor').exists():
            return Response(data=SerAllocation(project.allocations.all(), many=True).data)
        return Response(data='شما دسترسی لازم را ندارید', status=status.HTTP_403_FORBIDDEN)


class AllocationList(GenericAPIView):
    def get(self, request):
        if not request.user.groups.filter(name='pm').exists():
            return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)
        department = int(request.GET.get('department', 0))
        project = int(request.GET.get('project', 0))
        q = request.GET.get('q', None)
        if request.user.groups.filter(name='allocate').exists():
            allocate_list = Allocation.objects.all()
        else:
            allocate_list = Allocation.objects.filter(Q(project__unit=request.user.post.unit) | Q(project__unit__parent=request.user.post.unit))
        if department:
            allocate_list = allocate_list.filter(Q(project__unit_id=department) | Q(project__unit__parent_id=department))
        if project:
            allocate_list = allocate_list.filter(project_id=project)
        if q:
            q_list = q.split(' ')
            q_filter = reduce(operator.and_, (Q(title__contains=q_text) for q_text in q_list))
            allocate_list = allocate_list.filter(q_filter)
        size = request.user.profile.page_size
        page = min(int(request.GET.get('page', 1)), allocate_list.count() // size + 1)
        data = {
            'count': allocate_list.count(),
            'page': page,
            'size': size,
            'department': department,
            'project': project,
            'q': q,
            'list': SerAllocation(instance=allocate_list[size*(page-1):size*page], many=True).data
        }
        return Response(data=data)


class AllocationProjectListInDepartment(ListAPIView):
    serializer_class = SerActiveProjectList

    def get_queryset(self):
        return Project.objects.filter(approved=True).filter(Q(unit_id=self.kwargs['pk']) | Q(unit__parent_id=self.kwargs['pk']))


class AddOrUpdateAllocation(GenericAPIView):
    def post(self, request):
        if not request.user.groups.filter(name='allocate').exists():
            return Response(data='شما دسترسی لازم را ندارید', status=status.HTTP_403_FORBIDDEN)
        if request.data['id']:
            allocation = get_object_or_404(Allocation, pk=request.data['id'])
            allocation.project_id = request.data['project']
            allocation.title = request.data['title']
            allocation.date = request.data['date']
            allocation.amount = request.data['amount']
            allocation.save()
        else:
            allocation = Allocation.objects.create(project_id=request.data['project'], title=request.data['title'], date=request.data.get('date', None) or str(jdatetime.datetime.now().date()), amount=request.data['amount'])
        return Response(data=SerAllocation(allocation).data)


class RemoveAllocation(GenericAPIView):
    def post(self, request):
        if not request.user.groups.filter(name='allocate').exists():
            return Response(data='شما دسترسی لازم را ندارید', status=status.HTTP_403_FORBIDDEN)
        get_object_or_404(Allocation, id=request.data['id']).delete()
        return Response(data='removed')


class MyActiveProjectList(ListAPIView):
    serializer_class = SerActiveProjectList

    def get_queryset(self):
        if self.request.user.groups.filter(name='project').exists():
            return Project.objects.filter(approved=True, year=1404).order_by('-id')
        return Project.objects.filter(approved=True, year=1404).filter(Q(unit=self.request.user.post.unit) | Q(unit__parent=self.request.user.post.unit) | Q(id=1)).order_by('-id')


class AllActiveProjectList(ListAPIView):
    serializer_class = SerActiveProjectList
    queryset = Project.objects.filter(approved=True)


class ActiveProjectListInUnits(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SerActiveProjectList

    def get_queryset(self):
        return Project.objects.filter(approved=True).filter(Q(id=1) | Q(year=1404)).filter(Q(unit__in=self.request.GET.getlist('units')) | Q(id=1))


class MyTeammates(ListAPIView):
    permission_classes = [IsAuthenticated, IsPmUser]
    serializer_class = SerUserList

    def get_queryset(self):
        return User.objects.filter(post__unit=self.request.user.post.unit)


class ProjectOutcomeListCreateAPIView(ListCreateAPIView):
    serializer_class = ProjectOutcomeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectOutcome.objects.filter(
            project_id=self.kwargs['project_id']
        )

    def perform_create(self, serializer):
        project = get_object_or_404(
            Project,
            id=self.kwargs['project_id']
        )
        serializer.save(project=project)

    def create(self, request, *args, **kwargs):
        # ایجاد outcome
        response = super().create(request, *args, **kwargs)

        # گرفتن همه outcome های پروژه
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class ProjectOutcomeRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectOutcomeSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return ProjectOutcome.objects.filter(
            project_id=self.kwargs['project_id']
        )
