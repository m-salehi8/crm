from .models import *
import django_jalali.admin as jadmin
from unfold.admin import ModelAdmin, TabularInline


class MemberInline(TabularInline):
    autocomplete_fields = ['user']
    model = Member
    extra = 0


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ['__str__', 'type', 'create_time', 'member_count']
    list_filter = ['type']
    inlines = [MemberInline]
    search_fields = ['title']


@admin.register(Member)
class MemberAdmin(ModelAdmin):
    list_display = ['room', 'id', 'user', 'is_owner', 'is_manager', 'is_mute', 'is_pinned']


@admin.register(Chat)
class ChatAdmin(ModelAdmin):
    list_display = ['user', 'room', 'body', 'create_time']
    list_filter = ['room__type']
    autocomplete_fields = ['user', 'room']
    raw_id_fields = ['parent']
    search_fields = ['body']

