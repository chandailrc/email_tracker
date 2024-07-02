from django.http import HttpResponse
from django.utils import timezone
from .models import TrackingLog, TrackingPixelToken
from django.shortcuts import render
from .email_utils import send_tracked_email
from django.shortcuts import get_object_or_404, redirect
from .models import Link, LinkClick
import time
from .models import Email, UnsubscribedUser
from datetime import datetime
import random


import logging

logger = logging.getLogger(__name__)

import base64


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Take the first IP in the list
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def tracking_pixel(request, token):
    
    logger.info(f"views.py/PIXEL: Request received from {request}.")
    return handle_tracking(request, token, is_pixel=True)

def tracking_css(request, token):
    
    logger.info(f"views.py/CSS: Request received from {request}")
    return handle_tracking(request, token, is_pixel=False)

def handle_tracking(request, token, is_pixel):
    try:
        pixel_token = TrackingPixelToken.objects.get(token=token)
               
        TrackingLog.objects.create(
            email=pixel_token.email,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            opened_at=timezone.now(),
            # is_expired_open=pixel_token.is_expired(),
            tracking_type='pixel' if is_pixel else 'css'
        )
        
        if is_pixel:
            # Serve a 1x1 transparent PNG
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIDATx\x9c\x63\x60\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'
           
            # Encode the PNG data to base64
            # base64_png = base64.b64encode(png_data).decode('utf-8')
           
            # Return a 1x1 transparent pixel
            response = HttpResponse(content_type="image/png")
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response.write(png_data)  # Write the raw PNG data, not the base64 encoded version
           
            # Delete the token after use to prevent reuse
            # pixel_token.delete()
           
            return response
        else:
            # Serve an empty CSS file
            response = HttpResponse(content_type="text/css")
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            response.write("")  # Write the raw PNG data, not the base64 encoded version
            return response
    
    except TrackingPixelToken.DoesNotExist:
        return HttpResponse("Not found", status=404)

# def tracking_pixel(request, token):
#     # Get the TrackingPixelToken or return 404 if not found
#     pixel_token = get_object_or_404(TrackingPixelToken, token=token) #, expires_at__gt=timezone.now())
    
#     email = pixel_token.email
    
#     # Log the email open event with a timestamp
#     logger.info(f"views.py: Request received for email {email.id} at {timezone.now()}")
    
#     TrackingLog.objects.create(
#         email=email,
#         ip_address=request.META.get('REMOTE_ADDR'),
#         user_agent=request.META.get('HTTP_USER_AGENT'),
#         opened_at=timezone.now()
#     )
    
#     # 1x1 transparent PNG pixel
#     png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIDATx\x9c\x63\x60\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'
    
#     # Encode the PNG data to base64
#     # base64_png = base64.b64encode(png_data).decode('utf-8')
    
#     # Return a 1x1 transparent pixel
#     response = HttpResponse(content_type="image/png")
#     response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response['Pragma'] = 'no-cache'
#     response['Expires'] = '0'
#     response.write(png_data)  # Write the raw PNG data, not the base64 encoded version
    
#     # Delete the token after use to prevent reuse
#     # pixel_token.delete()
    
#     return response

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
                    print(f"views.py/send_tracked_email_view: Email sent successfully to {recipient}")
                else:
                    print(f"views.py/send_tracked_email_view: Failed to send email to {recipient}")
                
                if delay_type == 'fixed':
                    time.sleep(delay_value)
                elif delay_type == 'random':
                    time.sleep(random.uniform(min_delay, max_delay))
        
        confirmation_message = f"{sent_count} email(s) sent successfully!"
        print(confirmation_message)  # Add this line for debugging
        return render(request, 'compose_email.html', {'confirmation_message': confirmation_message})
    
    return render(request, 'compose_email.html')