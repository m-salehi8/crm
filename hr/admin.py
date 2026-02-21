from .models import *
import django_jalali.admin as jadmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import display
from django.utils.html import format_html
from django.db.models import Sum, Count


class TimesheetInline(TabularInline):
    model = Timesheet
    extra = 0
    autocomplete_fields = ['project', 'work']

@admin.register(Deduction)
class DeductionInline(ModelAdmin):
    list_display = ['user', 'year', 'month']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_filter = ['year', 'month']

from django.contrib import admin
from django.utils.html import format_html


@admin.register(Work)
class WorkAdmin(ModelAdmin):

    list_display = [
        'user',
        'year',
        'month',
        'gross_work',
        'work',
        'work_overtime',
        'salary_display',   # 👈 به جای salary
    ]

    list_filter = ['year', 'month']
    inlines = [TimesheetInline]
    autocomplete_fields = ['user']
    search_fields = ['user__first_name', 'user__last_name', 'user__personnel_code']
    ordering = ['id']

    # -----------------------------------
    # نمایش سه‌رقم سه‌رقم
    # -----------------------------------
    def salary_display(self, obj):
        if obj.salary:
            return f"{obj.salary:,}"
        return "0"

    salary_display.short_description = "حقوق"
    salary_display.admin_order_field = "salary"


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ['__str__', 'personnel_code', 'ad', 'is_active', 'is_permanent', 'is_corporate', 'is_advisor', 'is_agent', 'is_sacrificer', 'has_work', 'is_soldier', 'has_sf_mobile', 'has_sf_food']
    list_filter = ['user__is_active', 'user__post__level', 'is_permanent', 'is_advisor', 'is_agent', 'is_sacrificer', 'has_work', 'is_soldier', 'has_sf_mobile', 'has_sf_food', 'is_corporate', 'user__is_active']
    #autocomplete_fields = ['user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__personnel_code']
    ordering = ['id']


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ['body', 'year', 'respondent']
    list_filter = ['year', 'respondent']
    search_fields = ['body']

    def get_queryset(self, request):
        return Question.objects.filter(year=1404)


@admin.register(Assessment)
class AssessmentAdmin(ModelAdmin):
    list_display = ['who', 'whom', 'year']
    list_filter = ['year', 'who__post__unit']
    search_fields = ['who__first_name', 'who__last_name', 'who__personnel_code', 'whom__first_name', 'whom__last_name', 'whom__personnel_code']
    fields = ['who', 'whom']
    autocomplete_fields = ['who', 'whom']
    ordering = ['who', 'whom']

    def get_queryset(self, request):
        return Assessment.objects.filter(year=1404)


@admin.register(EvaluationGroup)
class EvaluationGroupAdmin(ModelAdmin):
    list_display = ['user', 'title', 'importance', 'member_count']
    autocomplete_fields = ['user', 'members']
    list_editable = ['importance']

    def get_queryset(self, request):
        return EvaluationGroup.objects.prefetch_related('members')


class EvaluationAnswerInline(TabularInline):
    model = EvaluationAnswer
    extra = 0


@admin.register(EvaluationAnswer)
class EvaluationAnswerAdmin(ModelAdmin):
    #list_display = ['answer', 'user', 'year', 'month', 'insurance']
    search_fields = ['user__first_name', 'user__last_name', 'user__personnel_code']

@admin.register(Evaluation)
class EvaluationAdmin(ModelAdmin):
    list_display = ['evaluator', 'group', 'year', 'month', 'is_done']
    list_filter = ['is_done', 'year', 'month']
    inlines = [EvaluationAnswerInline]
    search_fields = ['group__title']





@admin.register(DeductionType)
class DeductionTypeAdmin(ModelAdmin):
    list_display = ['code', 'title', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['code', 'title', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'code']
    sortable_by = ['code', 'title', 'order']



@admin.register(DeductionWork)
class DeductionWorkAdmin(ModelAdmin):
    list_display = ['user', 'type','year', 'month']
    list_filter = ['year', 'month', 'type']
    search_fields = ['user__first_name', 'user__last_name', 'user__personnel_code']
