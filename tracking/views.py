from django.http import HttpResponse
from django.utils import timezone
from .models import TrackingLog
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .email_utils import send_tracked_email
from django.shortcuts import get_object_or_404, redirect
from .models import Link, LinkClick
import time
# from django.utils.html import escape
from .forms import EmailBatchForm
# import threading
from .models import Email, UnsubscribedUser
# from .tasks import send_batch_emails
# from celery import current_app
# from datetime import timedelta
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

import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def load_emails(request):
    if request.method == 'POST' and request.FILES.get('json_file'):
        json_file = request.FILES['json_file']
        path = default_storage.save('tmp/bulk_emails.json', ContentFile(json_file.read()))
        
        with default_storage.open(path) as file:
            data = json.load(file)
        
        emails = []
        for item in data:
            email_content = item.get('email', '')
            subject, _, body = email_content.partition('\n\n')
            subject = subject.replace('Subject: ', '').strip()
            emails.append({
                'recipient': item.get('Business Email'),
                'subject': subject,
                'body': body
            })
        
        default_storage.delete(path)
        
        return render(request, 'bulk_email.html', {'emails': emails})
    
    return render(request, 'bulk_email.html')

def send_bulk_emails(request):
    if request.method == 'POST':
        delay_type = request.POST.get('delay_type')
        delay_value = int(request.POST.get('delay_value', 0))
        min_delay = int(request.POST.get('min_delay', 0))
        max_delay = int(request.POST.get('max_delay', 0))

        sent_count = 0
        index = 0
        while True:
            recipient = request.POST.get(f'email_{index}')
            subject = request.POST.get(f'subject_{index}')
            body = request.POST.get(f'body_{index}')
            
            if not recipient:  # No more emails to process
                break
            
            if recipient and subject and body:
                success = send_tracked_email(recipient, subject, body)
                if success:
                    sent_count += 1
                
                if delay_type == 'fixed':
                    time.sleep(delay_value)
                elif delay_type == 'random':
                    time.sleep(random.uniform(min_delay, max_delay))
            
            index += 1
        
        confirmation_message = f"{sent_count} email(s) sent successfully!"
        return render(request, 'bulk_email.html', {'confirmation_message': confirmation_message})
    
    return redirect('load_emails')