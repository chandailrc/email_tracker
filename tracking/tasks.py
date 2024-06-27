# tasks.py
import time
from celery import shared_task
from django.utils import timezone
from .models import EmailBatch
from .email_utils import send_tracked_email
from .scheduling import schedule_next_batch

@shared_task
def send_batch_emails(batch_id):
    email_batch = EmailBatch.objects.get(id=batch_id)
    recipients = email_batch.recipients.split(',')
    
    for i in range(0, len(recipients), email_batch.batch_size):
        batch = recipients[i:i+email_batch.batch_size]
        for recipient in batch:
            send_tracked_email(recipient, email_batch.subject, email_batch.body)
            time.sleep(email_batch.delay_between_emails)
        
        if i + email_batch.batch_size < len(recipients):
            time.sleep(email_batch.delay_between_batches)
    
    # Update last_sent
    email_batch.last_sent = timezone.now()
    email_batch.save()

    # Schedule the next batch
    schedule_next_batch(email_batch)

@shared_task
def check_scheduled_emails():
    now = timezone.now()
    
    for batch in EmailBatch.objects.all():
        if batch.schedule_type == 'daily':
            if batch.last_sent is None or (now - batch.last_sent).days >= 1:
                if now.time() >= batch.send_time:
                    send_batch_emails.delay(batch.id)
        elif batch.schedule_type == 'weekly':
            if batch.last_sent is None or (now - batch.last_sent).days >= 7:
                if now.weekday() == batch.day_of_week and now.time() >= batch.send_time:
                    send_batch_emails.delay(batch.id)
        elif batch.schedule_type == 'monthly':
            if batch.last_sent is None or (now - batch.last_sent).days >= 28:
                if now.day == batch.day_of_month and now.time() >= batch.send_time:
                    send_batch_emails.delay(batch.id)