from .models import *
import django_jalali.admin as jadmin
from django.forms import CheckboxSelectMultiple
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin, TabularInline
from django_ckeditor_5.widgets import CKEditor5Widget


@admin.register(ProclamationSeen)
class ProclamationSeenAdmin(ModelAdmin):
    pass


@admin.register(Unit)
class UnitAdmin(ModelAdmin):
    list_display = ['title', 'id', 'personnel_count', 'progress', 'expected']
    list_filter = ['parent']
    search_fields = ['title']
    save_on_top = True
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
        models.TextField: {'widget': CKEditor5Widget(config_name='extends')},
    }

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        return ['title', 'parent', 'progress', 'expected', 'overtime_quota', 'bonus_quota', 'overtime_bonus_open', 'note1404']


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ['title', 'id', 'level', 'unit', 'active_user_name', 'is_manager', 'position', 'parent']
    list_filter = ['level', 'is_manager', 'is_deputy', 'unit']
    search_fields = ['title']
    autocomplete_fields = ['parent', 'locations']


@admin.register(User)
class UserAdmin(UserAdmin, ModelAdmin):
    list_display = ['username', 'name', 'mobile', 'id', 'personnel_code', 'post', 'is_active', 'birth_date']
    list_filter = ['is_active', 'is_staff', 'post__level', 'groups', 'post__unit', 'is_interim']
    search_fields = ['first_name', 'last_name', 'username', 'personnel_code']
    ordering = ['id']
    autocomplete_fields = ['post']
    save_on_top = True
    fieldsets = [
        ('', {'fields': ('username', 'password')}),
        ('اطلاعات شخصی',
         {'fields': ('first_name', 'last_name', 'personnel_code', 'mobile', 'photo', 'post', 'is_interim', 'nc', 'birth_date', 'signature')}),
        ('theme', {'fields': ('theme', 'bg', 'main', 'tint1', 'tint2', 'tint3')}),
        ('اجازه‌ها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    ]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        if request.user.groups.filter(name='portal-admin').exists():
            return ['is_staff', 'is_superuser', 'user_permissions']
        return ['is_staff', 'is_superuser', 'groups', 'user_permissions']

    def get_queryset(self, request):
        qs = super().get_queryset(self)
        if request.user.is_superuser:
            return qs
        return qs.filter(is_superuser=False)


@admin.register(Key)
class KeyAdmin(ModelAdmin):
    list_display = ['key', 'value', 'description']


class ProclamationAppendixInline(TabularInline):
    model = ProclamationAppendix
    extra = 0


class ProclamationGalleryInline(TabularInline):
    model = ProclamationGallery
    extra = 0


@admin.register(Proclamation)
class ProclamationAdmin(ModelAdmin):
    list_display = ['title', 'type', 'display_duration', 'user', 'unit', 'publish_time', 'main_page_order']
    list_filter = ['type']
    raw_id_fields = ['user', 'unit']
    search_fields = ['title', 'body']
    inlines = [ProclamationGalleryInline, ProclamationAppendixInline]

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []
        return ['user', 'unit']

    def get_queryset(self, request):
        if request.user.is_superuser or request.user.username in ['javdani', 'j.ebrahimi', 'k.shokraei']:
            return Proclamation.objects.all()
        return request.user.proclamation_set.all()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
            obj.unit = request.user.post.unit
        super().save_model(request, obj, form, change)


@admin.register(Notification)
class AdminNotification(ModelAdmin):
    list_display = ['title', 'user', 'body', 'url', 'seen_time']
    readonly_fields = ['task', 'job_chat', 'node', 'contract']
    search_fields = ['user__first_name', 'user__last_name', 'title', 'body']


@admin.register(SMS)
class SMSAdmin(ModelAdmin):
    list_display = ['mobile', 'text', 'user', 'user_id', 'create_time', 'status']
    list_filter = ['status']
    readonly_fields = ['user', 'mobile', 'text', 'sent', 'create_time']
    search_fields = ['text', 'user__personnel_code', 'mobile']


@admin.register(Computer)
class ComputerAdmin(ModelAdmin):
    list_display = ['user', 'active_directory_account', 'pc_name', 'ip', 'cpu', 'motherboard', 'ram', 'vga', 'hdd', 'ssd', 'os']
    list_filter = ['user__post__unit', 'os', 'ram']
    search_fields = ['active_directory_account', 'user__username', 'pc_name', 'user__first_name', 'user__last_name']
    autocomplete_fields = ['user']


@admin.register(Theme)
class ThemeAdmin(ModelAdmin):
    list_display = ['title', 'bg', 'main', 'tint1', 'tint2', 'tint3']


@admin.register(Menu)
class MenuAdmin(ModelAdmin):
    list_display = ['key', 'title', 'icon', 'should_has_post', 'interim_not_allowed']
    autocomplete_fields = ['groups', 'posts', 'users']


class DashboardAccessInline(TabularInline):
    model = DashboardAccess
    extra = 1
    autocomplete_fields = ['user']


@admin.register(Dashboard)
class DashboardAdmin(ModelAdmin):
    list_display = ['title', 'slug']
    list_editable = ['slug', ]

    inlines = [DashboardAccessInline]


@admin.register(UserActivityLog)
class UserActivityLogAdmin(ModelAdmin):
    list_display = ('user', 'session_key', 'ip_address', 'method', 'path', 'status_code', 'timestamp')
    list_filter = ('user', 'method', 'status_code', 'app_name')
    search_fields = ('user__username', 'session_key', 'ip_address', 'path', 'view_name', 'user_agent')
    readonly_fields = [
        'user', 'session_key', 'path', 'method', 'status_code',
        'view_name', 'app_name', 'timestamp', 'ip_address', 'user_agent'
    ]
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False  # جلوگیری از درج دستی

    def has_change_permission(self, request, obj=None):
        return False  # فقط read-only نمایش داده شود


@admin.register(UserAuthLog)
class UserAuthLogAdmin(ModelAdmin):
    list_display = ['user', 'ip', ]