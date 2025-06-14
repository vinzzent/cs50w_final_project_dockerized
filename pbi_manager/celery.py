import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pbi_manager.settings')

app = Celery('pbi_manager')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.broker_url = 'redis://localhost:6379/0'

# Set the result backend
app.conf.result_backend = 'django-db'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
