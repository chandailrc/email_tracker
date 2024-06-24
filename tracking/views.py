from django.http import HttpResponse
from django.utils import timezone
from .models import TrackingLog
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .email_utils import send_tracked_email
from django.shortcuts import get_object_or_404, redirect
from .models import Link, LinkClick
import datetime
import time
from django.utils.html import escape
from .forms import EmailBatchForm
import threading
from .models import Email, UnsubscribedUser
from .tasks import send_batch_emails

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
        clicked_at=datetime.datetime.now(),
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
        recipient = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        
        # Call the send_tracked_email function to send the email
        send_tracked_email(recipient, subject, body)
        
        # Display confirmation message
        confirmation_message = "Email sent successfully!"
        
        # Pause for a brief moment (optional)
        time.sleep(2)  # Pauses for 2 seconds
        
        # Redirect back to the compose page after sending email
        return render(request, 'compose_email.html', {'confirmation_message': escape(confirmation_message)})
    
    return HttpResponse('Method not allowed', status=405)

def batch_email_view(request):
    if request.method == 'POST':
        form = EmailBatchForm(request.POST)
        if form.is_valid():
            email_batch = form.save(commit=False)
            email_batch.save()
            recipients = request.POST['recipients'].split()
            subject = request.POST['subject']
            body = request.POST['body']
            for recipient in recipients:
                email = Email(recipient=recipient, subject=subject, body=body, sent_at=timezone.now())
                email.save()  # Ensure the email instance is saved
                email_batch.emails.add(email)
            email_batch.save()
            send_batch_emails.delay(email_batch.id)  # Call the Celery task
            return HttpResponse('<html><body><h3>Email batch scheduled successfully!</h3></body></html>')
    else:
        form = EmailBatchForm()
    return render(request, 'batch_email.html', {'form': form})



def schedule_emails(batch):
    def send_batch_emails():
        for email in batch.emails.all():
            send_tracked_email(email.recipient, email.subject, email.body)
            time.sleep(batch.delay_between_emails)
        time.sleep(batch.delay_between_batches)

    def schedule_next_batch():
        if batch.send_daily:
            batch.next_send_time = timezone.now() + timezone.timedelta(days=1)
        elif batch.send_weekly:
            batch.next_send_time = timezone.now() + timezone.timedelta(weeks=1)
        elif batch.send_monthly:
            batch.next_send_time = timezone.now() + timezone.timedelta(days=30)
        batch.save()
        threading.Timer(1, send_batch_emails).start()

    send_batch_emails()
    if batch.send_daily or batch.send_weekly or batch.send_monthly:
        threading.Timer(1, schedule_next_batch).start()
