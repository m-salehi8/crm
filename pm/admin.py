from .models import *
from django.contrib import admin
import django_jalali.admin as jadmin
from unfold.admin import ModelAdmin, TabularInline


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['title', 'user']
    search_fields = ['title', 'user__username']
    autocomplete_fields = ['user']
    ordering = ['-id']


class JobAppendixInline(TabularInline):
    model = JobAppendix
    extra = 0


class TaskInline(TabularInline):
    model = Task
    raw_id_fields = ['user']
    autocomplete_fields = ['tag']
    extra = 0
    exclude = ['order', 'last_seen_chat']


class JobChatInline(TabularInline):
    model = JobChat
    raw_id_fields = ['user']
    extra = 0


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ['title', 'public', 'capacity', 'location']
    list_filter = ['public']
    autocomplete_fields = ['posts']
    search_fields = ['title']


class ApprovalInline(TabularInline):
    model = Approval
    extra = 0
    autocomplete_fields = ['members']


@admin.register(Session)
class SessionAdmin(ModelAdmin):
    list_display = ['title', 'room', 'user', 'date','accept_room' ,'approval_count', 'create_time']
    list_filter = ['room', 'user__post__unit', 'accept_room']
    search_fields = ['title']
    ordering = ['-id']
    inlines = [ApprovalInline]
    autocomplete_fields = ['user', 'members', 'breakfast_agents', 'lunch_agents', 'catering_agents', 'room_agents', 'photography_agents', 'recording_agents', 'filming_agents', 'news_agents', 'presentation_agents', 'secretaries']

@admin.register(SessionRate)
class SessionRateAdmin(ModelAdmin):
    list_display = ['user', 'session', 'rate']


class JobInline(TabularInline):
    model = Job
    fields = ['pk', 'title', 'deadline', 'status', 'archive']
    readonly_fields = ['pk']
    extra = 0


@admin.register(Approval)
class ApprovalAdmin(ModelAdmin):
    list_display = ['title', 'session', 'is_done', 'deadline']
    raw_id_fields = ['members']
    search_fields = ['title']
    inlines = [JobInline]


@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = ['title', 'status', 'urgency', 'archive']
    list_filter = ['status', 'urgency', 'archive']
    search_fields = ['title', 'tasks__user__username']
    inlines = [JobAppendixInline, TaskInline, JobChatInline]
    autocomplete_fields = ['project', 'approval', 'session', 'informees']
    ordering = ['-id']


@admin.register(FellowException)
class FellowExceptionAdmin(ModelAdmin):
    list_display = ['fellower', 'fellowed']
    raw_id_fields = ['fellower', 'fellowed']

# Flow:


class AdminFieldInline(TabularInline):
    model = Field
    readonly_fields = ['id']
    extra = 0

@admin.register(FlowPatternType)
class FlowPatternTypeAdmin(ModelAdmin):
    list_display = ['title', 'create_time', 'update_time',  'active']
    list_filter = ['active', ]


@admin.register(FlowPattern)
class AdminFlowPattern(ModelAdmin):
    list_display = ['title', 'flow_type', 'quota_per_user', 'active']
    list_filter = ['flow_type', 'active']
    list_editable = ['flow_type', 'active']
    search_fields = ['title']
    inlines = [AdminFieldInline]
    save_on_top = True
    ordering = ['-id']


@admin.register(Field)
class AdminField(ModelAdmin):
    list_display = ['label', 'flow_pattern', 'type', 'table']
    search_fields = ['label']
    list_filter = ['flow_pattern']
    ordering = ['-id']


class AdminNodeField(TabularInline):
    model = NodeField
    raw_id_fields = ['field']


@admin.register(NodePattern)
class AdminNodePattern(ModelAdmin):
    list_display = ['title', 'flow_pattern', 'is_first']
    inlines = [AdminNodeField]
    list_filter = ['flow_pattern']
    ordering = ['-id']


class AdminDispatchIf(TabularInline):
    model = DispatchIf
    raw_id_fields = ['key']
    extra = 0


@admin.register(Dispatch)
class AdminDispatch(ModelAdmin):
    list_display = ['start', 'end', 'if_operator']
    list_filter = ['start__flow_pattern']
    raw_id_fields = ['start', 'end']
    autocomplete_fields = ['send_to_posts']
    inlines = [AdminDispatchIf]
    ordering = ['-id']


class AdminNode(TabularInline):
    model = Node
    raw_id_fields = ['user', 'node_pattern']
    readonly_fields = ['id', 'create_time']


class AdminAnswer(TabularInline):
    model = Answer
    raw_id_fields = ['field']


@admin.register(Answer)
class AdminAnswers(ModelAdmin):
    list_display = [ 'body']
    search_fields = [ 'body']

@admin.register(Flow)
class AdminFlow(ModelAdmin):
    list_display = ['flow_pattern', 'user_name', 'create_time']
    autocomplete_fields = ['user', 'flow_pattern']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
    inlines = [AdminNode, AdminAnswer]
    list_filter = ['flow_pattern']
    save_on_top = True
    ordering = ['-id']
