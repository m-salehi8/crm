from django.apps import AppConfig


class CnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cn'
    verbose_name = 'قراردادها'

    def ready(self):
        import cn.signals
