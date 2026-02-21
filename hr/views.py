from .serializers import *
from rest_framework import status
from django.db.models import Q, Sum
from core.models import User, Unit, Post
from rest_framework.views import APIView
from rest_framework.response import Response
from core.permissions import IsManager, HasPost, IsHrAdmin
from rest_framework.generics import ListAPIView, GenericAPIView, UpdateAPIView, get_object_or_404, RetrieveAPIView

import os
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status


class WorkUnitList(ListAPIView):
    serializer_class = SerWorkUnitList

    def get_queryset(self):
        if self.request.user.groups.filter(name='hr').exists():
            return Unit.objects.all()
        if self.request.user.post.is_deputy:
            return Unit.objects.filter(Q(parent_id=self.request.user.post.unit_id) | Q(id=self.request.user.post.unit_id))
        if self.request.user.post.is_manager:
            return Unit.objects.filter(id=self.request.user.post.unit_id)
        return Unit.objects.filter(id=0)


class PersonnelList(ListAPIView):
    serializer_class = SerPersonnel

    def get_queryset(self):
        if self.request.user.groups.filter(name='hr').exists():
            return User.objects.filter(is_active=1, post__isnull=False)
        return User.objects.filter(id=0)


class BlankPostList(ListAPIView):
    serializer_class = SerBlankPostList

    def get_queryset(self):
        if self.request.user.groups.filter(name='hr').exists():
            return Post.objects.filter(user=None)
        return Post.objects.filter(id=0)


class UpdatePersonnel(UpdateAPIView):
    serializer_class = SerPersonnel

    def get_queryset(self):
        if self.request.user.groups.filter(name='hr').exists():
            return User.objects.all()
        return User.objects.filter(id=0)


class ToggleUnitOvertimeBonusOpenHasVisitant(GenericAPIView):
    def post(self, request):
        if request.user.groups.filter(name='hr').exists():
            unit = get_object_or_404(Unit, pk=request.data['id'])
            unit.overtime_bonus_open = not unit.overtime_bonus_open
            unit.save()
            return Response(data=unit.overtime_bonus_open)
        return Response(data='شما دسترسی لازم را ندارید', status=status.HTTP_403_FORBIDDEN)


class UpdateUnitOvertimeBonus(UpdateAPIView):
    serializer_class = SerWorkUnitList

    def get_queryset(self):
        if self.request.user.groups.filter(name='hr').exists():
            return Unit.objects.all()
        return Unit.objects.filter(id=0)


class WorkList(GenericAPIView):
    def get(self, request):
        now = jdatetime.datetime.now()
        year = int(request.GET.get('year')) if request.GET.get('year') else now.year
        month = int(request.GET.get('month')) if request.GET.get('month') else now.month
        unit_id = int(request.GET.get('unit')) if request.GET.get('unit') else request.user.post.unit_id
        unit = get_object_or_404(Unit, id=unit_id)
        if request.user.groups.filter(name='hr').exists() or (request.user.is_head_of_unit and unit == request.user.post.unit or unit.parent == request.user.post.unit):
            work_list = Work.objects.exclude(user=request.user).filter(year=year, month=month, user__profile__has_work=True).filter(Q(user__post__unit=unit) | Q(user__post__unit__parent=unit)).order_by('year', 'month')
            data = {
                'year': year,
                'month': month,
                'unit': unit_id,
                'overtime_quota': unit.overtime_quota,
                'bonus_quota': unit.bonus_quota,
                'can_edit': year == now.year and month == now.month and (((unit == request.user.post.unit or unit.parent == request.user.post.unit) and unit.overtime_bonus_open and request.user.post.is_manager) or request.user.id == 9),
                'list': SerWork(instance=work_list, many=True).data
            }
            return Response(data=data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class SaveTalents(APIView):
    def post(self, request):
        for (index, pk) in enumerate(request.data['ranks']):
            work = get_object_or_404(Work, pk=pk, user__post__unit=request.user.post.unit)
            work.rank = index
            work.save()
        for i in [1, 2, 3]:
            for j in [1, 2, 3]:
                for item in request.data['talents'][f'performance{i}'][f'potential{j}']:
                    work = get_object_or_404(Work, pk=item['id'], user__post__unit=request.user.post.unit)
                    work.performance = i
                    work.potential = j
                    work.save()
        return Response()


class SaveWork(GenericAPIView):
    def post(self, request):
        if request.user.todo_evaluate:
            return Response(data='ابتدا ارزیابی عملکرد نیروها را ثبت کنید', status=status.HTTP_400_BAD_REQUEST)
        work = get_object_or_404(Work, id=request.data['id'])
        now = jdatetime.datetime.now()
        unit = work.user.post.unit
        if work.year == now.year and work.month == now.month and (((unit == request.user.post.unit or unit.parent == request.user.post.unit) and unit.overtime_bonus_open and request.user.post.is_manager) or request.user.id == 9):
            overtime_sum = Work.objects.exclude(id=work.id).filter(year=now.year, month=now.month, user__post__unit=unit).aggregate(val=Sum('overtime'))['val'] or 0
            bonus_sum = Work.objects.exclude(id=work.id).filter(year=now.year, month=now.month, user__post__unit=unit).aggregate(val=Sum('bonus'))['val'] or 0
            work.bonus = int(request.data['bonus'])
            work.overtime = int(request.data['overtime'])
            work.percent = int(request.data['percent'])
            work.amenity_percent = int(request.data['amenity_percent'])
            work.meed = int(request.data['meed'])
            work.meed_note = request.data['meed_note']
            if request.user.id != 9 and (overtime_sum + work.overtime > unit.overtime_quota or bonus_sum + work.bonus > unit.bonus_quota):
                return Response(data='کارآیی یا اضافه‌کار بیش از سقف مجاز است', status=status.HTTP_400_BAD_REQUEST)
            work.save()
            data = {
                'data': SerWork(work).data,
                'todo_timesheet': request.user.todo_timesheet
            }
            return Response(data)
        return Response(data='شما دسترسی لازم ندارید', status=status.HTTP_403_FORBIDDEN)


class ProfileDetail(GenericAPIView):
    permission_classes = [IsManager | IsHrAdmin]

    def get(self, request, pk, year, month):
        if self.request.user.groups.filter(name='hr').exists():
            profile = get_object_or_404(Profile, id=pk)
        else:
            profile = Profile.objects.filter(Q(user__post__unit=self.request.user.post.unit) | Q(user__post__unit__parent=self.request.user.post.unit)).get(id=pk)
        return Response(data=SerProfileV2(instance=profile, context={'year': year, 'month': month}).data)


# #################### 360 Degree Assessment ####################


class AssessmentList(ListAPIView):
    permission_classes = [HasPost]
    serializer_class = SerAssessmentList

    def get_queryset(self):
        my_post = self.request.user.post
        pks = []
        for user in User.objects.filter(Q(post__parent=my_post.parent) | Q(post__parent=my_post) | Q(post__parent__parent=my_post) | Q(post=my_post.parent)):
            assessment, created = Assessment.objects.get_or_create(who=self.request.user, whom=user, year=1404)
            pks.append(assessment.pk)
        self.request.user.assessment_who_set.exclude(pk__in=pks).delete()
        return self.request.user.assessment_who_set.filter(year=1404)


class AssessmentDetail(GenericAPIView):
    permission_classes = [HasPost]

    def get(self, request, pk):
        assessment = get_object_or_404(Assessment, id=pk)
        return Response(SerAssessmentDetail(assessment).data)

    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, id=pk)
        assessment.done = True
        assessment.save()
        for item in request.data['questions']:
            question = get_object_or_404(Question, id=item['id'])
            answer = question.answers.filter(assessment=assessment).first()
            if answer:
                answer.rate = item['rate']
                answer.save()
            else:
                question.answers.create(assessment=assessment, rate=item['rate'])
        return Response()


class CreatEvaluationsForCurrentMonth(APIView):
    def get(self, request):
        if request.user.groups.filter(name='hr').exists():
            today = jdatetime.date.today()
            for group in EvaluationGroup.objects.all():
                evaluation, created = Evaluation.objects.get_or_create(group=group, year=today.year, month=today.month)
                pks = []
                for user in group.members.all():
                    evaluation.answers.get_or_create(user=user)
                    pks.append(user.pk)
                evaluation.answers.exclude(user__in=pks).delete()
                if evaluation.answers.filter(rank=None).exists():
                    evaluation.is_done = False
                    evaluation.save()
            return Response(EvaluationGroup.objects.count())
        return Response(status=status.HTTP_403_FORBIDDEN)


class EvaluationList(APIView):
    def get(self, request):
        today = jdatetime.date.today()
        year = int(request.GET.get('year', 0)) or today.year
        month = int(request.GET.get('month', 0)) or today.month
        evaluation_list = Evaluation.objects.filter(group__user=request.user, year=year, month=month)
        data = {
            'list': SerEvaluationList(evaluation_list, many=True).data,
            'editable': year == today.year and month == today.month,
        }

        return Response(data=data)


class SaveEvaluationList(APIView):
    def post(self, request):
        evaluation = get_object_or_404(Evaluation, id=request.data['id'], year=jdatetime.date.today().year, month=jdatetime.date.today().month, group__user=request.user)
        for (index, item) in enumerate(request.data['answers']):
            answer = get_object_or_404(EvaluationAnswer, id=item['id'], evaluation=evaluation)
            answer.rank = index + 1
            answer.performance = item['performance']
            answer.potential = item['potential']
            answer.note = item['note']
            answer.save()
            ids = list(map(lambda p: p['id'], item['timesheets']))
            answer.timesheets.exclude(id__in=ids).delete()
            for ts in item['timesheets']:
                if ts['id']:
                    timesheet = get_object_or_404(EvaluationAnswerTimesheet, id=ts['id'], answer=answer)
                    timesheet.project_id = ts['project']
                    timesheet.percent = ts['percent']
                    timesheet.save()
                else:
                    EvaluationAnswerTimesheet.objects.create(answer=answer, project_id=ts['project'], percent=ts['percent'])
        evaluation.is_done = True
        evaluation.save()
        return Response(request.user.todo_evaluate)



class SimpleExcelUpload(APIView):

    parser_classes = [MultiPartParser]

    def post(self, request):
        # چک کن فایل ارسال شده
        if 'file' not in request.FILES:
            return Response({
                'error': 'فایل ارسال نشده'
            }, status=status.HTTP_400_BAD_REQUEST)

        # فایل رو بگیر
        excel_file = request.FILES['file']

        # فقط فرمت‌های اکسل رو قبول کن
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return Response({
                'error': 'فقط فایل اکسل مجاز است'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # در روت پروژه فولدر uploads بساز
            upload_dir = 'uploads'
            os.makedirs(upload_dir, exist_ok=True)

            # نام فایل با timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{excel_file.name}"
            file_path = os.path.join(upload_dir, filename)

            # فایل رو ذخیره کن
            with open(file_path, 'wb+') as f:
                for chunk in excel_file.chunks():
                    f.write(chunk)

            # جواب بده
            return Response({
                'success': True,
                'message': 'فایل ذخیره شد',
                'filename': filename,
                'path': file_path,
                'size': excel_file.size
            })

        except Exception as e:
            return Response({
                'error': f'خطا: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from hr.models import Work, DeductionWork


class WorkFullDetailAPI(APIView):

    def get(self, request, user_id, year, month):

        try:
            work = Work.objects.select_related(
                "user",
                "user__profile"
            ).get(
                user__id=user_id,
                year=year,
                month=month
            )
        except Work.DoesNotExist:
            return Response(
                {"detail": "Work not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # اگر حقوق محاسبه نشده
        if not work.salary:
            work.calculate_salary(save=True)

        profile = work.user.profile

        # --- محاسبات ---
        sum_salary = work.get_sum()
        overtime_amount = work.get_overtime_amount()
        gross = work.get_gross()
        insurance = work.get_insurance()
        tax = work.get_tax()

        deduction = DeductionWork.objects.filter(
            user=work.user,
            year=year,
            month=month
        ).aggregate(total=Sum("value"))["total"] or 0

        net = work.salary

        # --- سه ماه گذشته ---
        last_three = (
            Work.objects
            .filter(user=work.user, year=year, month__lt=month)
            .order_by("-month")[:3]
        )

        last_three_data = [
            {
                "month": w.month,
                "salary": w.salary,
                "salary_display": f"{w.salary:,}"
            }
            for w in last_three
        ]

        data = {
            "employee": {
                "full_name": f"{work.user.first_name} {work.user.last_name}",
                "personnel_code": work.user.personnel_code,
            },
            "period": {
                "year": year,
                "month": month,
            },
            "work_report": {
                "work_days": work.work_days,
                "overtime_hours": work.overtime,
                "bonus": work.bonus,
                "meed": work.meed,
            },
            "salary_breakdown": {
                "sum_benefits": sum_salary,
                "sum_benefits_display": f"{sum_salary:,}",
                "overtime_amount": overtime_amount,
                "overtime_display": f"{overtime_amount:,}",
                "gross": gross,
                "gross_display": f"{gross:,}",
                "insurance": insurance,
                "insurance_display": f"{insurance:,}",
                "tax": tax,
                "tax_display": f"{tax:,}",
                "deduction": deduction,
                "deduction_display": f"{deduction:,}",
                "net_salary": net,
                "net_salary_display": f"{net:,}",
            },
            "last_three_months": last_three_data
        }

        return Response(data)
