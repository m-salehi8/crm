from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from django.utils.html import format_html
from .models import Video, VideoLike, VideoComment, VideoCategory, VideoTag, VideoCategoryRelation, VideoTagRelation, VideoFileAppendix


@admin.register(VideoFileAppendix)
class VideoFileAppendixAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)


@admin.register(VideoCategory)
class VideoCategoryAdmin(ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(VideoTag)
class VideoTagAdmin(ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


class VideoCategoryRelationInline(TabularInline):
    model = VideoCategoryRelation
    extra = 1


class VideoTagRelationInline(TabularInline):
    model = VideoTagRelation
    extra = 1


class VideoCommentInline(TabularInline):
    model = VideoComment
    extra = 0
    readonly_fields = ['user', 'created_at', 'updated_at']
    fields = ['user', 'content', 'is_approved', 'created_at', 'updated_at']


class VideoLikeInline(TabularInline):
    model = VideoLike
    extra = 0
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'created_at']


@admin.register(Video)
class VideoAdmin(ModelAdmin):
    list_display = [
        'title', 'uploader', 'poster_preview', 'is_published',
        'view_count', 'like_count', 'comment_count', 'created_at'
    ]
    list_filter = ['is_published', 'created_at', 'uploader']
    search_fields = ['title', 'description', 'uploader__username']
    readonly_fields = [
        'view_count', 'like_count', 'comment_count',
        'created_at', 'updated_at', 'poster_preview', 'video_preview'
    ]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'uploader', 'is_published')
        }),
        ('فایل‌ها', {
            'fields': ('poster', 'poster_preview', 'video_file', 'video_preview')
        }),
        ('آمار', {
            'fields': ('view_count', 'like_count', 'comment_count'),
            'classes': ('collapse',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [VideoCategoryRelationInline, VideoTagRelationInline, VideoCommentInline, VideoLikeInline]

    def poster_preview(self, obj):
        if obj.poster:
            return format_html(
                '<img src="{}" width="100" height="60" style="border-radius: 5px;" />',
                obj.poster.url
            )
        return "بدون پوستر"

    poster_preview.short_description = "پیش‌نمایش پوستر"

    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="200" height="120" controls>'
                '<source src="{}" type="video/mp4">'
                'مرورگر شما از ویدیو پشتیبانی نمی‌کند.'
                '</video>',
                obj.video_file.url
            )
        return "بدون ویدیو"

    video_preview.short_description = "پیش‌نمایش ویدیو"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploader')


@admin.register(VideoComment)
class VideoCommentAdmin(ModelAdmin):
    list_display = ['user', 'video', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at', 'video__uploader']
    search_fields = ['user__username', 'content', 'video__title']
    readonly_fields = ['created_at', 'updated_at']

    def content_preview(self, obj):
        if len(obj.content) > 50:
            return obj.content[:50] + "..."
        return obj.content

    content_preview.short_description = "متن کامنت"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'video')


@admin.register(VideoLike)
class VideoLikeAdmin(ModelAdmin):
    list_display = ['user', 'video', 'created_at']
    list_filter = ['created_at', 'video__uploader']
    search_fields = ['user__username', 'video__title']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'video')


@admin.register(VideoCategoryRelation)
class VideoCategoryRelationAdmin(ModelAdmin):
    list_display = ['video', 'category']
    list_filter = ['category']
    search_fields = ['video__title', 'category__name']


@admin.register(VideoTagRelation)
class VideoTagRelationAdmin(ModelAdmin):
    list_display = ['video', 'tag']
    list_filter = ['tag']
    search_fields = ['video__title', 'tag__name']


from django.contrib import admin

# Register your models here.
