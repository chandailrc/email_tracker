from django.http import HttpResponse
from django.utils import timezone
from .models import TrackingLog
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .email_utils import send_tracked_email
from django.shortcuts import get_object_or_404, redirect
from .models import Link, LinkClick
import time
from django.utils.html import escape
from .forms import EmailBatchForm
import threading
from .models import Email, UnsubscribedUser
from .tasks import send_batch_emails
from celery import current_app
from datetime import timedelta
from datetime import datetime
import random


@csrf_exempt
def track_email(request, email_id):
    try:
        email = Email.objects.get(id=email_id)
        TrackingLog.objects.create(
            email=email,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            opened_at=timezone.now()
        )
        # 1x1 transparent GIF data
        pixel = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff'
            b'\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x44\x01\x00\x3b'
        )
        return HttpResponse(pixel, content_type='image/gif')
    except Email.DoesNotExist:
        return HttpResponse(status=404)
    


def track_link(request, link_id):
    link = get_object_or_404(Link, pk=link_id)
    LinkClick.objects.create(
        link=link,
        clicked_at=datetime.now(),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    return redirect(link.url)

    

def dashboard(request):
    emails = Email.objects.all()
    unsubscribed_users = UnsubscribedUser.objects.values_list('email', flat=True)
    return render(request, 'dashboard.html', {'emails': emails, 'unsubscribed_emails': unsubscribed_users})

def unsubscribe(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            UnsubscribedUser.objects.get_or_create(email=email)
            return HttpResponse('You have been unsubscribed.')
    return render(request, 'unsubscribe.html')


def unsubscribed_users_list(request):
    unsubscribed_users = UnsubscribedUser.objects.values_list('email', flat=True)
    return render(request, 'unsubscribed_users_list.html', {'unsubscribed_emails': unsubscribed_users})

def compose_email_view(request):
    return render(request, 'compose_email.html')

def send_tracked_email_view(request):
    if request.method == 'POST':
        recipients = request.POST.get('recipients').split()  # Split on whitespace
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        delay_type = request.POST.get('delay_type')
        delay_value = int(request.POST.get('delay_value', 0))
        min_delay = int(request.POST.get('min_delay', 0))
        max_delay = int(request.POST.get('max_delay', 0))
        
        sent_count = 0
        for recipient in recipients:
            recipient = recipient.strip()
            if recipient:
                success = send_tracked_email(recipient, subject, body)
                if success:
                    sent_count += 1
                    print(f"Email sent successfully to {recipient}")
                else:
                    print(f"Failed to send email to {recipient}")
                
                if delay_type == 'fixed':
                    time.sleep(delay_value)
                elif delay_type == 'random':
                    time.sleep(random.uniform(min_delay, max_delay))
        
        confirmation_message = f"{sent_count} email(s) sent successfully!"
        print(confirmation_message)  # Add this line for debugging
        return render(request, 'compose_email.html', {'confirmation_message': confirmation_message})
    
    return render(request, 'compose_email.html')


# views.py
from django.http import HttpResponse
from django.shortcuts import render
from .models import EmailBatch
from .forms import EmailBatchForm
from .scheduling import schedule_next_batch

from django.http import HttpResponse
from django.shortcuts import render
from .models import EmailBatch
from .forms import EmailBatchForm
from .scheduling import schedule_next_batch

def batch_email_view(request):
    if request.method == 'POST':
        form = EmailBatchForm(request.POST)

        if form.is_valid():
            email_batch = form.save(commit=False)
            email_batch.recipients = ','.join(request.POST['recipients'].split())
            email_batch.save()

            # Schedule the initial task
            schedule_next_batch(email_batch)

            return HttpResponse('<html><body><h3>Email batch scheduled successfully!</h3></body></html>')
    else:
        form = EmailBatchForm()
    return render(request, 'batch_email.html', {'form': form})

# def schedule_next_batch(email_batch):
#     now = timezone.now()
#     send_time = datetime.combine(now.date(), email_batch.send_time)

#     if email_batch.schedule_type == 'daily':
#         if send_time <= now:
#             send_time += timedelta(days=1)
#     elif email_batch.schedule_type == 'weekly':
#         days_ahead = email_batch.day_of_week - now.weekday()
#         if days_ahead <= 0:
#             days_ahead += 7
#         send_time = datetime.combine(now.date() + timedelta(days=days_ahead), email_batch.send_time)
#     elif email_batch.schedule_type == 'monthly':
#         next_month = now.replace(day=1) + timedelta(days=32)
#         next_run = next_month.replace(day=min(email_batch.day_of_month, (next_month.replace(day=1) - timedelta(days=1)).day))
#         send_time = datetime.combine(next_run.date(), email_batch.send_time)

#     delay_until_send = (send_time - now).total_seconds()

#     # Schedule the task to run at send_time
#     current_app.send_task('tracking.tasks.send_batch_emails', args=[email_batch.id], countdown=delay_until_send)
