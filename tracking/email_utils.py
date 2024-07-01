# custom_email_backend.py

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import re
from urllib.parse import urlparse
from .models import Email, Link, UnsubscribedUser
from django.utils import timezone
import datetime

import logging

logger = logging.getLogger(__name__)

def send_tracked_email(recipient, subject, body):
    if UnsubscribedUser.objects.filter(email=recipient).exists():
        print(f"Email not sent to {recipient} as they have unsubscribed.")
        return False

    try:
        
        email = Email.objects.create(recipient=recipient, subject=subject, body=body, sent_at=timezone.now())
        tracking_id = email.id
        
        logger.info(f"email_utils.py: Email db entry created for {recipient} at {timezone.now()}")

        def replace_link(match):
            original_url = match.group(0)
            parsed_url = urlparse(original_url)
            link = Link.objects.create(email=email, url=original_url)
            tracked_url = f"{settings.BASE_URL}/track-link/{link.id}/"
            return f'<a href="{tracked_url}">Link</a>'
        
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

        msg = EmailMultiAlternatives(
            subject=subject,
            body=tracked_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(email_body, "text/html")
        msg.send()

        print(f"email_utils.py: Email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"email_utils.py: Error sending email to {recipient}: {e}")
        return False
