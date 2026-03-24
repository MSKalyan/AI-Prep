from django.apps import AppConfig
import sys

class AiServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_service'  # Ensure this matches your path in settings.py

    def ready(self):
        # We check if we are running the 'runserver' command 
        # so it doesn't trigger during migrations or other commands
        if 'runserver' in sys.argv:
            from ml_utils import ModelLoader
            ModelLoader.get_model()