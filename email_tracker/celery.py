# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'email_tracker.settings')

app = Celery('email_tracker')

# Use a string here instead of a file path to make sure the worker doesn't
# have to serialize the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure the beat schedule
app.conf.beat_schedule = {
    'check-scheduled-emails': {
        'task': 'your_app.tasks.check_scheduled_emails',
        'schedule': crontab(minute=0, hour='*'),  # Run every hour
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')