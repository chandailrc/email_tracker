# -*- coding: utf-8 -*-

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
import re
from urllib.parse import urlparse
from .models import Email, Link
from django.utils import timezone
from .models import UnsubscribedUser
import datetime
# import logging
# logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)

def send_tracked_email(recipient, subject, body):
    if UnsubscribedUser.objects.filter(email=recipient).exists():
        print(f"Email not sent to {recipient} as they have unsubscribed.")
        return False

    try:
        email = Email.objects.create(recipient=recipient, subject=subject, body=body, sent_at=timezone.now())
        tracking_id = email.id

        def replace_link(match):
            original_url = match.group(0)
            parsed_url = urlparse(original_url)
            link = Link.objects.create(email=email, url=original_url)
            tracked_url = f"{settings.BASE_URL}/track-link/{link.id}/"
            return tracked_url
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        tracked_body = re.sub(r'http[s]?:\/\/[^\s]*', replace_link, body)
        html_body = tracked_body.replace('\n', '<br>')  # Convert newlines to <br> tags
        
        pixel_url = f"{settings.BASE_URL}/pixel.png?email_id={tracking_id}&timestamp={timestamp}"

        email_body = f"""
            <html>
              <head></head>
              <body>
                <p>{html_body}</p>
                <img src="{pixel_url}" alt="tracking pixel" width="1" height="1" style="display:none;">
                <p>If you wish to unsubscribe, click <a href="{settings.BASE_URL}/unsubscribe/?email={recipient}">here</a>.</p>
              </body>
            </html>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = recipient

        msg.attach(MIMEText(tracked_body, 'plain'))
        msg.attach(MIMEText(email_body, 'html'))

        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(settings.EMAIL_HOST_USER, recipient, msg.as_string())

        print(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        return False        
        
        
        

