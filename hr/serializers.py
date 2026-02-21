from .models import *
from rest_framework import serializers
from core.models import User, Unit, Post


class SerWorkUnitList(serializers.ModelSerializer):
    department_title = serializers.CharField(read_only=True, source='department.title')

    class Meta:
        model = Unit
        fields = ['id', 'title', 'department_title', 'work_personnel_count', 'overtime_quota', 'bonus_quota', 'overtime_bonus_open']


class SerPersonnel(serializers.ModelSerializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    post_title = serializers.CharField(read_only=True, source='post.title')
    level = serializers.CharField(read_only=True, source='post.level')
    unit_title = serializers.CharField(read_only=True, source='post.unit.title')
    department = serializers.IntegerField(read_only=True, source='post.department.id')
    department_title = serializers.CharField(read_only=True, source='post.department.title')

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'personnel_code', 'post', 'post_title', 'level', 'unit_title', 'department', 'department_title', 'mobile']


class SerBlankPostList(serializers.ModelSerializer):
    department_title = serializers.CharField(read_only=True, source='department.title')

    class Meta:
        model = Post
        fields = ['id', 'title', 'department_title']


class SerTimesheet(serializers.ModelSerializer):
    project_title = serializers.CharField(read_only=True, source='project.title')

    class Meta:
        model = Timesheet
        fields = ['id', 'project', 'project_title', 'note', 'percent']


class SerWork(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='user.get_full_name')
    is_permanent = serializers.BooleanField(read_only=True, source='user.profile.is_permanent')
    is_advisor = serializers.BooleanField(read_only=True, source='user.profile.is_advisor')
    is_corporate = serializers.BooleanField(read_only=True, source='user.profile.is_corporate')
    is_sacrificer = serializers.BooleanField(read_only=True, source='user.profile.is_sacrificer')
    attendance_min = serializers.IntegerField(read_only=True, source='user.profile.attendance_min')
    post = serializers.CharField(read_only=True, source='user.post.title')
    personnel_code = serializers.IntegerField(read_only=True, source='user.personnel_code')
    gross_work = serializers.SerializerMethodField()
    work = serializers.SerializerMethodField()
    paid_leave = serializers.SerializerMethodField()
    mission = serializers.SerializerMethodField()
    delay = serializers.SerializerMethodField()
    work_overtime = serializers.SerializerMethodField()
    timesheet_set = SerTimesheet(many=True)

    def get_gross_work(self, work):
        hours, remainder = divmod(work.gross_work.days * 60 * 60 * 24 + work.gross_work.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}'

    def get_work(self, work):
        hours, remainder = divmod(work.work.days * 60 * 60 * 24 + work.work.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}'

    def get_paid_leave(self, work):
        hours, remainder = divmod(work.paid_leave.days * 60 * 60 * 24 + work.paid_leave.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}'

    def get_mission(self, work):
        hours, remainder = divmod(work.mission.days * 60 * 60 * 24 + work.mission.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}'

    def get_delay(self, work):
        hours, remainder = divmod(work.delay.days * 60 * 60 * 24 + work.delay.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}'

    def get_work_overtime(self, work):
        hours, remainder = divmod(work.work_overtime.days * 60 * 60 * 24 + work.work_overtime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}'

    class Meta:
        model = Work
        fields = ['is_corporate', 'id', 'user', 'name', 'post', 'personnel_code', 'is_permanent', 'is_advisor', 'is_sacrificer', 'work_days', 'gross_work', 'work', 'paid_leave', 'sick_leave', 'telecommuting',
                  'mission', 'delay', 'absence', 'work_overtime', 'overtime', 'bonus', 'percent', 'history', 'attendance_min', 'timesheet_set', 'meed', 'meed_note', 'amenity_percent']


class SerProfile(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'is_advisor', 'is_sacrificer', 'is_agent', 'sf1', 'sf5', 'sf6', 'sf7', 'sf8', 'sf11', 'sf14', 'sf20', 'sf27', 'sf38', 'sf42', 'sf45', 'sf49', 'sf51', 'sf52', 'sf64', 'sf65', 'sf68', 'sf69', 'sf70', 'sf_house', 'sf_food', 'sf_mobile', 'sf_commuting', 'sf_management', 'deduction']

    deduction = serializers.SerializerMethodField()

    def get_deduction(self, profile):
        deduction = profile.user.deduction_set.filter(year=self.context['year'], month=self.context['month']).first()
        if deduction:
            return {
                'insurance': deduction.insurance,
                'loan': deduction.loan,
                'fund': deduction.fund,
                'other': deduction.other,
            }
        return {
                'insurance': 0,
                'loan': 0,
                'fund': 0,
                'other': 0,
        }


class SerProfileV2(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id', 'is_advisor', 'is_sacrificer', 'is_agent',
            'sf1', 'sf5', 'sf6', 'sf7', 'sf8', 'sf11', 'sf14',
            'sf20', 'sf27', 'sf38', 'sf42', 'sf45', 'sf49', 'sf51',
            'sf52', 'sf64', 'sf65', 'sf68', 'sf69', 'sf70',
            'sf_house', 'sf_food', 'sf_mobile', 'sf_commuting',
            'sf_management', 'deduction'
        ]

    deduction = serializers.SerializerMethodField()

    def get_deduction(self, profile):
        """
        نسخه کاملاً داینامیک - هر نوع جدیدی اضافه بشه، خودکار نمایش داده میشه
        """
        year = self.context.get('year')
        month = self.context.get('month')

        # دریافت همه انواع کسورات فعال
        all_active_types = DeductionType.objects.filter(is_active=True).order_by('order')

        if not year or not month:
            return self._create_empty_response(all_active_types)

        # دریافت کسورات کاربر
        user_deductions = profile.user.deductionwork_set.filter(
            year=year,
            month=month
        ).select_related('type')

        # ساخت مپ از کد به مقدار
        deductions_map = {d.type.code: d.value for d in user_deductions}

        # محاسبه "سایر" - جمع تمام کسوراتی که در mapping قدیمی نیستن
        legacy_other_codes = ['food', 'digipay', 'mashhad']
        other_total = sum(deductions_map.get(code, 0) for code in legacy_other_codes)

        # لیست همه کسورات به صورت داینامیک
        all_deductions_dynamic = {}
        for deduction_type in all_active_types:
            value = deductions_map.get(deduction_type.code, 0)
            all_deductions_dynamic[deduction_type.code] = {
                'title': deduction_type.title,
                'value': value,
                'value_toman': value // 10,
                'description': deduction_type.description,
                'order': deduction_type.order
            }

        # ساختن پاسخ



        response = {
            # بخش قدیمی برای سازگاری
            'insurance': deductions_map.get('tak', 0),
            'loan': deductions_map.get('vam', 0),
            'fund': deductions_map.get('san', 0),
            'other': other_total,

            # بخش جدید - کاملاً داینامیک
            'all_deductions': all_deductions_dynamic,

            # اطلاعات انواع
            'available_types': [
                {
                    'code': dt.code,
                    'title': dt.title,
                    'description': dt.description,
                    'order': dt.order,
                    'is_active': dt.is_active,
                    'has_value': dt.code in deductions_map
                }
                for dt in all_active_types
            ],

            # آمار
            'summary': {
                'total': sum(deductions_map.values()),
                'total_toman': sum(deductions_map.values()) // 10,
                'count': len([v for v in deductions_map.values() if v > 0]),
                'month': f"{year}/{month}"
            }
        }
        deduction = profile.user.deduction_set.filter(year=self.context['year'], month=self.context['month']).first()
        if deduction:
            response['insurance'] = deduction.insurance
            response['loan'] = deduction.loan
            response['fund'] = deduction.fund
            response['other'] = deduction.other

        return response

    def _create_empty_response(self, all_active_types):
        """ساختن پاسخ خالی به صورت داینامیک"""
        all_deductions_empty = {}
        for deduction_type in all_active_types:
            all_deductions_empty[deduction_type.code] = {
                'title': deduction_type.title,
                'value': 0,
                'value_toman': 0,
                'description': deduction_type.description,
                'order': deduction_type.order
            }

        # پیدا کردن کدهایی که مربوط به "سایر" هستند
        legacy_other_codes = self._get_legacy_other_codes(all_active_types)

        return {
            'insurance': 0,
            'loan': 0,
            'fund': 0,
            'other': 0,
            'all_deductions': all_deductions_empty,
            'available_types': [
                {
                    'code': dt.code,
                    'title': dt.title,
                    'description': dt.description,
                    'order': dt.order,
                    'is_active': dt.is_active,
                    'has_value': False
                }
                for dt in all_active_types
            ],
            'summary': {
                'total': 0,
                'total_toman': 0,
                'count': 0,
                'month': None
            }
        }

    def _get_legacy_other_codes(self, all_active_types):
        """
        تشخیص خودکار کدهایی که باید در 'سایر' حساب بشن
        کدهای استاندارد: tak, vam, san مربوط به insurance, loan, fund هستن
        بقیه کدها در other حساب میشن
        """
        standard_codes = ['tak', 'vam', 'san']  # کدهای استاندارد قدیمی

        all_codes = [dt.code for dt in all_active_types]
        other_codes = [code for code in all_codes if code not in standard_codes]

        return other_codes


class SerAssessmentList(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='whom.get_full_name')
    post = serializers.CharField(read_only=True, source='whom.post.title')

    class Meta:
        model = Assessment
        fields = ['id', 'name', 'post', 'done']


class SerQuestionList(serializers.ModelSerializer):
    rate = serializers.SerializerMethodField()

    def get_rate(self, question):
        ans = question.answers.filter(assessment_id=self.context['assessment']).first()
        return ans.rate if ans else None

    class Meta:
        model = Question
        fields = ['id', 'body', 'choice_count', 'rate']


class SerAssessmentDetail(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='whom.get_full_name')
    post = serializers.CharField(read_only=True, source='whom.post.title')
    photo = serializers.CharField(read_only=True, source='whom.photo_url')
    questions = serializers.SerializerMethodField()

    def get_questions(self, assessment):
        if assessment.who == assessment.whom:
            respondent = 'خودارزیابی'
        elif assessment.whom.post.unit.manager == assessment.who:
            respondent = 'مدیر واحد'
        elif assessment.who.post.parent == assessment.whom.post:
            respondent = 'نیروی تحت امر'
        elif assessment.whom.post.parent == assessment.who.post or (assessment.whom.post.parent and assessment.whom.post.parent.parent == assessment.who.post):
            respondent = 'سرپرست مستقیم'
        else:
            respondent = 'همکار'
        return SerQuestionList(Question.objects.filter(year=1404, respondent=respondent), many=True, context={'assessment': assessment.id}).data

    class Meta:
        model = Assessment
        fields = ['id', 'who', 'whom', 'name', 'post', 'photo', 'done', 'bio', 'strength', 'weakness', 'note', 'educations', 'questions']


class SerEvaluationAnswerTimesheet(serializers.ModelSerializer):
    class Meta:
        model = EvaluationAnswerTimesheet
        fields = ['id', 'project', 'percent']


class SerEvaluationAnswer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, source='user.get_full_name')
    timesheets = SerEvaluationAnswerTimesheet(many=True, read_only=True)

    class Meta:
        model = EvaluationAnswer
        fields = ['id', 'evaluation', 'name', 'rank', 'performance', 'potential', 'note', 'timesheets']


class SerEvaluationList(serializers.ModelSerializer):
    group_title = serializers.CharField(read_only=True, source='group.title')
    answers = SerEvaluationAnswer(many=True, read_only=True)

    class Meta:
        model = Evaluation
        fields = ['id', 'year', 'month', 'is_done', 'group_title', 'answers']



class WorkSalarySerializer(serializers.ModelSerializer):

    user_full_name = serializers.SerializerMethodField()
    personnel_code = serializers.CharField(source="user.personnel_code")
    salary_display = serializers.SerializerMethodField()

    class Meta:
        model = Work
        fields = [
            "id",
            "year",
            "month",
            "work_days",
            "overtime",
            "bonus",
            "meed",
            "salary",
            "salary_display",
            "user_full_name",
            "personnel_code",
        ]

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_salary_display(self, obj):
        return f"{obj.salary:,}" if obj.salary else "0"
