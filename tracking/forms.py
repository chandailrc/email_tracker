#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from django import forms
from .models import EmailBatch

class EmailBatchForm(forms.ModelForm):
    schedule_type = forms.ChoiceField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], required=True)
    send_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'), required=True)

    class Meta:
        model = EmailBatch
        fields = [
            'schedule_type', 'send_time', 'day_of_week', 'day_of_month',
            'delay_between_emails', 'delay_between_batches', 'batch_size'
        ]