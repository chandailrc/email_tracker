#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django import forms
from .models import EmailBatch

class EmailBatchForm(forms.ModelForm):
    class Meta:
        model = EmailBatch
        fields = ['recipients', 'subject', 'body', 'schedule_type', 'batch_size', 
                  'send_time', 'delay_between_emails', 'delay_between_batches', 
                  'day_of_week', 'day_of_month']

    def clean(self):
        cleaned_data = super().clean()
        schedule_type = cleaned_data.get('schedule_type')
        day_of_week = cleaned_data.get('day_of_week')
        day_of_month = cleaned_data.get('day_of_month')

        if schedule_type == 'weekly' and day_of_week is None:
            self.add_error('day_of_week', 'Day of week is required for weekly schedule')
        if schedule_type == 'monthly' and day_of_month is None:
            self.add_error('day_of_month', 'Day of month is required for monthly schedule')

        return cleaned_data