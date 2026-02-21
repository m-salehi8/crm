from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.shortcuts import redirect
from django.views.static import serve

from django.views.generic import TemplateView

def home(request):
    return redirect(to='admin/')


urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    # path('__debug__/', include("debug_toolbar.urls")),
    path('api-auth/', include('rest_framework.urls')),
    path("ckeditor5/", include('django_ckeditor_5.urls')),

    path('core/', include('core.urls')),
    path('api/', include('captcha.urls')),
    path("captcha/", TemplateView.as_view(template_name="index.html")),

    path('prj/', include('prj.urls')),
    path('fd/', include('fd.urls')),
    path('hr/', include('hr.urls')),
    path('pm/', include('pm.urls')),
    path('fn/', include('fn.urls')),
    path('cn/', include('cn.urls')),
    path('chat/', include('chat.urls')),
    path('videos/', include('video.urls')),

    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
