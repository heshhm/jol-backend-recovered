from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.services.analytics'
    verbose_name = 'Analytics'
    
    def ready(self):
        """Import signals or perform other initialization"""
        pass
