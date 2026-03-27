from django.apps import AppConfig

class CustomAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'custom_admin'

    def ready(self):
        # This ensures signals are connected when Django starts
        import custom_admin.signals