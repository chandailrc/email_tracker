from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import json

class Email(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

class TrackingLog(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    opened_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)

class Link(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    url = models.URLField()

class LinkClick(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE)
    clicked_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    

class UnsubscribedUser(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email
    
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta

class EmailBatch(models.Model):
    SCHEDULE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    DAY_OF_WEEK_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    recipients = models.TextField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES)
    batch_size = models.IntegerField()
    send_time = models.TimeField()
    delay_between_emails = models.IntegerField()  # in seconds
    delay_between_batches = models.IntegerField()  # in seconds
    last_sent = models.DateTimeField(null=True, blank=True)
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES, null=True, blank=True)
    day_of_month = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(31)]
    )

    def get_next_run_time(self):
        now = timezone.now()
        today = now.date()
        send_datetime = timezone.make_aware(datetime.combine(today, self.send_time))

        if self.schedule_type == 'daily':
            if send_datetime <= now:
                send_datetime += timedelta(days=1)
        elif self.schedule_type == 'weekly':
            days_ahead = self.day_of_week - now.weekday()
            if days_ahead <= 0 or (days_ahead == 0 and send_datetime <= now):
                days_ahead += 7
            send_datetime = timezone.make_aware(datetime.combine(today + timedelta(days=days_ahead), self.send_time))
        elif self.schedule_type == 'monthly':
            next_month = today.replace(day=1) + timedelta(days=32)
            next_run = next_month.replace(day=min(self.day_of_month, (next_month.replace(day=1) - timedelta(days=1)).day))
            send_datetime = timezone.make_aware(datetime.combine(next_run, self.send_time))
            if send_datetime <= now:
                next_month = next_run + timedelta(days=32)
                next_run = next_month.replace(day=min(self.day_of_month, (next_month.replace(day=1) - timedelta(days=1)).day))
                send_datetime = timezone.make_aware(datetime.combine(next_run, self.send_time))

        return send_datetime