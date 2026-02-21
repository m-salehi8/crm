from django.db import models
from django.contrib import admin
import django_jalali.admin as jadmin
from unfold.admin import ModelAdmin, TabularInline
from django_ckeditor_5.fields import CKEditor5Widget
from .models import Mission, Project, Phase, Report, ReportAppendix, DailyUpdateLog, Allocation, Document, DocumentColleague, DocumentLog, ProjectsTeam, ProjectOutcome, PhaseTeam


from django.contrib import admin

class ProjectOutcomeInline(TabularInline):
    model = ProjectOutcome
    extra = 1

@admin.register(PhaseTeam)
class PhaseTeamAdmin(ModelAdmin):
    list_display = ('user', 'phase', 'participation_percentage')
    list_filter = ('user', 'phase')

@admin.register(Mission)
class MissionAdmin(ModelAdmin):
    list_display = ['title', 'type', 'realization_year']
    list_filter = ['units']
    search_fields = ['title']


class PhaseInline(TabularInline):
    model = Phase
    extra = 0


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ['title', 'year', 'unit', 'cost', 'confirmed', 'accepted', 'approved', 'priority', 'progress', 'delay', 'priority_percentage']
    list_filter = ['year', 'priority', 'unit', 'missions']
    readonly_fields = ['progress', 'expected']
    inlines = [PhaseInline, ProjectOutcomeInline]
    search_fields = ['title']
    formfield_overrides = {
        models.TextField: {'widget': CKEditor5Widget(config_name='extends')},
    }


class ReportAppendixInline(TabularInline):
    model = ReportAppendix
    extra = 0


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    list_display = ['phase', 'progress_claimed', 'progress_accepted', 'progress_approved', 'accepted', 'approved']
    list_filter = ['accepted', 'approved', 'phase__project__unit']
    inlines = [ReportAppendixInline]
    readonly_fields = ['claim_date', 'accept_date', 'approve_date']
    raw_id_fields = ['phase']
    search_fields = ['phase__title', 'phase__project__title']


@admin.register(DailyUpdateLog)
class DailyUpdateLogAdmin(ModelAdmin):
    list_display = ['start', 'finish', 'updated_count']


@admin.register(Allocation)
class AllocationAdmin(ModelAdmin):
    list_display = ['project', 'title', 'date', 'amount']
    list_filter = ['project__unit']
    raw_id_fields = ['project']
    search_fields = ['project__title']


class DocumentColleagueAdmin(TabularInline):
    model = DocumentColleague
    extra = 0


class DocumentLogAdmin(TabularInline):
    model = DocumentLog
    extra = 0


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = ['title', 'trustee', 'get_draft', 'post_comments', 'post_to_commission', 'post_to_approval_authority', 'approve', 'approval_authority']
    list_filter = ['get_draft', 'post_comments', 'post_to_commission', 'post_to_approval_authority', 'approve']
    inlines = [DocumentColleagueAdmin, DocumentLogAdmin]
    readonly_fields = ['title']
    search_fields = ['title']

@admin.register(ProjectsTeam)
class ProjectsTeamAdmin(ModelAdmin):
    list_display = ['user', 'project', 'participation_percentage']
    list_filter = ['user', 'project']
    search_fields = ['user', 'project']