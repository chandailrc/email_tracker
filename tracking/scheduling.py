from django.utils import timezone
from celery import current_app

def schedule_next_batch(email_batch):
    now = timezone.now()
    send_time = email_batch.get_next_run_time()

    delay_until_send = max((send_time - now).total_seconds(), 0)

    # Schedule the task to run at send_time
    current_app.send_task('tracking.tasks.send_batch_emails', 
                          args=[email_batch.id], 
                          countdown=delay_until_send)

def calculate_next_run_time(email_batch):
    return email_batch.get_next_run_time()

def reschedule_batch(email_batch):
    schedule_next_batch(email_batch)