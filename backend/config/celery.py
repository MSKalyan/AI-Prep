import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ai_exam_prep')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# Periodic tasks configuration
app.conf.beat_schedule = {
    'update-daily-analytics': {
        'task': 'worker.tasks.update_daily_analytics',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
    },
    'cleanup-old-sessions': {
        'task': 'worker.tasks.cleanup_old_sessions',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
    'send-study-reminders': {
        'task': 'worker.tasks.send_study_reminders',
        'schedule': crontab(hour=9, minute=0),  # Run daily at 9 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
