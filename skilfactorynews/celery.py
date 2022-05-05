import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skilfactorynews.settings')

app = Celery('skilfactorynews')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()