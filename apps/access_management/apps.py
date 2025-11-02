from django.apps import AppConfig


class AccessManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.access_management'
    verbose_name = 'Управление доступом'
    
    def ready(self):
        import apps.access_management.signals  # noqa

