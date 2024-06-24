from celery import shared_task
from .models import EmailBatch
from tracking.email_utils import send_tracked_email
import time

@shared_task
def send_batch_emails(batch_id):
    email_batch = EmailBatch.objects.get(id=batch_id)
    emails = email_batch.emails.all()
    
    for email in emails:
        send_tracked_email(email.recipient, email.subject, email.body)
        if email_batch.delay_between_emails > 0:
            time.sleep(email_batch.delay_between_emails)
    
    if email_batch.delay_between_batches > 0:
        time.sleep(email_batch.delay_between_batches)
