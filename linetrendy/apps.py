from django.apps import AppConfig



class LinetrendyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'linetrendy'

    def ready(self):
        import linetrendy.signals
