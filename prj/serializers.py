from rest_framework import serializers

from cn.models import Contract
from cn.serializers import SerContractList
from .models import Mission, Project, Phase, Report, ReportAppendix, Allocation, ProjectsTeam, ProjectOutcome, PhaseTeam
from django_jalali.serializers.serializerfield import JDateField
from core.models import User

class SerPhaseList(serializers.ModelSerializer):
    class Meta:
        model = Phase
        fields = ['id', 'title', 'step', 'importance', 'cost', 'progress', 'expected']


class SerPhaseTeam(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user'
    )
    phase_title = serializers.CharField(source='phase.title', read_only=True)

    class Meta:
        model = PhaseTeam
        fields = [
            'id',
            'user_id',
            'user_full_name',
            'participation_percentage',
            'phase_title'
        ]

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()


class SerPhaseDetail(serializers.ModelSerializer):
    team_phase = SerPhaseTeam(source='teams', many=True)

    class Meta:
        model = Phase
        fields = [
            'team_phase',
            'id', 'title', 'step', 'priority', 'importance',
            'cost', 'type', 'method', 'hr', 'ph',
            'progress', 'expected', 'delay',
            'start', 'finish', 'goal','goal_value' ,'report_count'
        ]

    def update(self, instance, validated_data):

        teams_data = validated_data.pop('team_percent', None)

        # آپدیت فیلدهای خود فاز
        instance = super().update(instance, validated_data)

        if teams_data is not None:
            new_user_ids = [team['user']['id'] for team in teams_data]

            # حذف کسانی که دیگر در لیست نیستند
            PhaseTeam.objects.filter(phase=instance) \
                .exclude(user_id__in=new_user_ids) \
                .delete()

            # آپدیت یا ایجاد اعضای جدید
            for team in teams_data:
                user_id = team['user']['id']
                percentage = team.get('participation_percentage', 0)

                PhaseTeam.objects.update_or_create(
                    phase=instance,
                    user_id=user_id,
                    defaults={
                        'participation_percentage': percentage
                    }
                )

        return instance
    def create(self, validated_data):
        teams_data = validated_data.pop('team_percent', None)

class SerProjectList(serializers.ModelSerializer):
    phases = SerPhaseList(read_only=True, many=True)

    class Meta:
        model = Project
        fields = ['id', 'year', 'unit', 'title', 'priority', 'priority_percentage', 'progress', 'expected', 'delay', 'confirmed', 'accepted', 'approved', 'cost', 'allocation', 'phases']


class SerMission(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = ['id', 'title']


class SerContractListInProject(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = ['id', 'registrar', 'no', 'contractor', 'title', 'period', '_start_date', '_finish_date', '_price', 'status', 'sum_of_pay']


class SerAllocationListInProject(serializers.ModelSerializer):
    class Meta:
        model = Allocation
        fields = ['id', 'title', 'date', 'amount']

class SerProjectsTeam(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id')
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = ProjectsTeam
        fields = ['id', 'user_id', 'user_full_name', 'participation_percentage', 'project_title']

    def get_user_full_name(self, obj):
        return obj.user.get_full_name()


class SerProjectDetail(serializers.ModelSerializer):
    unit_title = serializers.CharField(read_only=True, source='unit.title')
    missions = SerMission(read_only=True, many=True)
    team_list = serializers.SerializerMethodField()
    can = serializers.SerializerMethodField()
    phases = SerPhaseDetail(read_only=True, many=True)
    contracts = serializers.SerializerMethodField()
    allocations = serializers.SerializerMethodField()
    team_projects = SerProjectsTeam(source='teams', many=True, read_only=True)  # فیلد جدید

    def get_team_list(self, project):
        return [u.get_full_name() for u in project.team.all()]

    def get_can(self, project):
        user = self.context['user']
        return {
            'edit': (project.confirmed is False or project.accepted is False or project.approved is False) and user.groups.filter(name='pm').exists() and project.unit == user.post.unit,
            'confirm': (project.confirmed is False or project.accepted is False or project.approved is False) and user.groups.filter(name='pm').exists() and project.unit == user.post.unit and user.post.is_manager,
            'accept': project.accepted is None and user.post.is_deputy and (project.unit == user.post.unit or project.unit.parent == user.post.unit and project.confirmed),
            'approve': project.accepted and project.approved is None and user.groups.filter(name='project').exists(),
            'report': project.approved and user.groups.filter(name='pm').exists() and (project.unit == user.post.unit or project.unit.parent == user.post.unit),
        }

    def get_contracts(self, project):
        user = self.context['user']
        if user.groups.filter(name='supervisor').exists() or project.unit == user.post.unit or project.unit.parent == user.post.unit:
            return SerContractListInProject(instance=project.contracts.all(), many=True).data
        return []

    def get_allocations(self, project):
        user = self.context['user']
        if user.groups.filter(name='supervisor').exists() or project.unit == user.post.unit or project.unit.parent == user.post.unit:
            return SerAllocationListInProject(instance=project.allocations.all(), many=True).data
        return []

    class Meta:
        model = Project
        fields = ['team_projects','id', 'year', 'unit', 'unit_title', 'title', 'note', 'priority','priority_percentage', 'progress', 'expected', 'delay', 'confirmed', 'accepted', 'accept_note', 'approved', 'approve_note', 'cost', 'start', 'finish', 'team', 'team_list', 'can', 'missions', 'phases', 'contracts', 'allocations']


class SerPhaseForm(serializers.ModelSerializer):
    start = JDateField()
    finish = JDateField()
    team_percent = serializers.DictField(
        child=serializers.FloatField(min_value=0, max_value=100),
        write_only=True,
        required=False
    )
    class Meta:
        model = Phase
        fields = ['project', 'title', 'priority', 'importance', 'type', 'method', 'cost', 'ph', 'start', 'finish', 'goal','goal_value', 'team_percent']

    def update(self, instance, validated_data):
        """به‌روزرسانی فاز همراه با مدیریت تیم"""
        team_percent = validated_data.pop('team_percent', None)

        # به‌روزرسانی فاز
        phase = super().update(instance, validated_data)

        # مدیریت تیم اگر داده‌ای ارسال شده باشد
        if team_percent is not None:
            self._update_team_percent(phase, team_percent)

        return phase

    def _update_team_percent(self, phase, team_data):
        """تابع کمکی برای مدیریت تیم پروژه"""
        try:
            # تبدیل کلیدها به عدد
            new_user_ids = [int(uid) for uid in team_data.keys()]

            # حذف کاربرانی که در لیست جدید نیستند
            PhaseTeam.objects.filter(phase=phase) \
                .exclude(user_id__in=new_user_ids) \
                .delete()

            # به‌روزرسانی یا ایجاد رکوردهای جدید
            for user_id, percentage in team_data.items():
                PhaseTeam.objects.update_or_create(
                    phase=phase,
                    user_id=int(user_id),
                    defaults={'participation_percentage': percentage}
                )

        except Exception as e:
            # لاگ کردن خطا (می‌توانید از logging استفاده کنید)
            print(f"Error updating team percentages: {e}")
            # یا می‌توانید خطا را به صورت قابل نمایش بازگردانید
            raise serializers.ValidationError(
                {"team_percent": f"خطا در به‌روزرسانی تیم: {str(e)}"}
            )
    def create(self, validated_data):
        """ایجاد فاز جدید همراه با مدیریت تیم"""
        team_percent = validated_data.pop('team_percent', None)

        # ایجاد فاز
        phase = super().create(validated_data)

        # مدیریت تیم اگر داده‌ای ارسال شده باشد
        if team_percent is not None:
            self._update_team_percent(phase, team_percent)

        return phase


class SerReportAppendix(serializers.ModelSerializer):
    file_name = serializers.CharField(read_only=True, source='file.name')

    class Meta:
        model = ReportAppendix
        fields = 'id', 'report', 'file', 'file_name'


class SerReportList(serializers.ModelSerializer):
    appendices = SerReportAppendix(read_only=True, many=True)

    class Meta:
        model = Report
        fields = ['id', 'phase', 'claim_note', 'claim_date', 'progress_claimed', 'accepted', 'progress_accepted', 'accept_date', 'accept_note', 'approved', 'progress_approved', 'approve_date', 'approve_note', 'appendices']


class SerReportDetail(serializers.ModelSerializer):
    appendices = SerReportAppendix(read_only=True, many=True)
    phase_title = serializers.CharField(read_only=True, source='phase.title')
    project = serializers.CharField(read_only=True, source='phase.project.id')
    project_title = serializers.CharField(read_only=True, source='phase.project.title')
    unit_title = serializers.CharField(read_only=True, source='phase.project.unit.title')
    progress = serializers.CharField(read_only=True, source='phase.progress')
    expected = serializers.CharField(read_only=True, source='phase.expected')
    can = serializers.SerializerMethodField()

    def get_can(self, report):
        return {
            'edit': report.approved is None and self.context['user'].post.unit == report.phase.project.unit,
            'approve': report.approved is None and self.context['user'].groups.filter(name='control').exists(),
        }

    class Meta:
        model = Report
        fields = ['id', 'phase', 'phase_title', 'project', 'project_title', 'unit_title', 'claim_note', 'claim_date', 'progress_claimed', 'accepted', 'progress_accepted', 'accept_date', 'accept_note', 'approved', 'progress_approved', 'approve_date', 'approve_note', 'appendices', 'progress', 'expected', 'can']


class SerAllocation(serializers.ModelSerializer):
    date = JDateField()
    project_title = serializers.CharField(read_only=True, source='project.title')
    department = serializers.IntegerField(read_only=True, source='project.unit.department.id')
    department_title = serializers.CharField(read_only=True, source='project.unit.department.title')

    class Meta:
        model = Allocation
        fields = ['id', 'title', 'date', 'amount', 'project', 'project_title', 'department', 'department_title']


class SerActiveProjectList(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title']


class ProjectOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectOutcome
        fields = ['id', 'title', 'value']