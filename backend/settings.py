import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.templatetags.static import static
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-n6xou%tk^-p@lc*o3^y%+a!&9njazx)e657zb51q(u@p60gi*7'
DEBUG = True
ALLOWED_HOSTS = ['*', '127.0.0.1', 'localhost', '192.168.19.161', 'ahadi.csnc.local', "192.168.19.174"]
AUTH_USER_MODEL = 'core.User'
INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'unfold.contrib.inlines',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'core.apps.CoreConfig',
    'prj.apps.PrjConfig',
    'pm.apps.PmConfig',
    'fd.apps.FdConfig',
    'hr.apps.HrConfig',
    'cn.apps.CnConfig',
    'fn.apps.FnConfig',
    'chat.apps.ChatConfig',
    'corsheaders',
    'django_jalali',
    # 'debug_toolbar',
    'rest_framework',
    'rest_framework.authtoken',
    'django_cleanup.apps.CleanupConfig',
    'django_ckeditor_5',
    'django.contrib.humanize',
    'st.apps.StConfig',
    "video.apps.VideoConfig",
    'captcha',

    # 'django_crontab',
]
ASGI_APPLICATION = 'backend.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('it.local', 6379)]},
    },
}
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
 #   'core.middleware.UserActivityLogMiddleware',
]
ROOT_URLCONF = 'backend.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
DATABASESs = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'it.local',
        'NAME': 'majazi',
        'USER': 'postgres',
        'PASSWORD': 'AURuNHt)>7%x0{0[UR+x',
        'PORT': '5432',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1',
        'NAME': 'portal',
        'USER': 'postgres',
        'PASSWORD': '1q2w3e4r',
        'PORT': '5432',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'fa-IR'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = False
STATIC_URL = 'static/'
if DEBUG:
    STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'), )
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1', 'http://192.168.19.174:8000']
CORS_ALLOWED_ORIGINS = ['http://localhost:8080', 'http://192.168.19.174:8000']
CORS_ORIGIN_ALLOW_ALL = True
LOGIN_URL = '/login/'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
}
INTERNAL_IPS = ['127.0.0.1']
CRONJOBS = [
    # ('0 2 * * *', 'kpf.models.daily_update')
]
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
customColorPalette = [
    {'color': 'hsl(4, 90%, 58%)', 'label': 'Red'},
    {'color': 'hsl(340, 82%, 52%)', 'label': 'Pink'},
    {'color': 'hsl(291, 64%, 42%)', 'label': 'Purple'},
    {'color': 'hsl(262, 52%, 47%)', 'label': 'Deep Purple'},
    {'color': 'hsl(231, 48%, 48%)', 'label': 'Indigo'},
    {'color': 'hsl(207, 90%, 54%)', 'label': 'Blue'},
]
CKEDITOR_5_CONFIGS = {
    'default': {'toolbar': ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', ]},
    'extends': {
        'blockToolbar': ['paragraph', 'heading1', 'heading2', 'heading3', '|', 'bulletedList', 'numberedList', '|', 'blockQuote'],
        'toolbar': [
            'heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough', 'code', 'subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing',
            'bulletedList', 'numberedList', 'todoList', '|',  'blockQuote', 'imageUpload', '|', 'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'removeFormat', 'insertTable'
        ],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft', 'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side',  '|'],
            'styles': ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter']
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells', 'tableProperties', 'tableCellProperties'],
            'tableProperties': {'borderColors': customColorPalette, 'backgroundColors': customColorPalette},
            'tableCellProperties': {'borderColors': customColorPalette, 'backgroundColors': customColorPalette}
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'}
            ]
        },
        'language': {'ui': 'ar', 'content': 'ar'},
    },
    'list': {'properties': {'styles': 'true', 'startIndex': 'true', 'reversed': 'true'}}
}


from .unfold_config import UNFOLD