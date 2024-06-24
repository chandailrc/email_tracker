# -*- coding: utf-8 -*-

from django.urls import path
from .views import *

urlpatterns = [
    path('batch/', batch_email_view, name='batch_email'),
    path('compose/', compose_email_view, name='compose_email'),
    path('send-tracked-email/', send_tracked_email_view, name='send_tracked_email_view'),
    path('tracking/<int:email_id>/', track_email, name='track_email'),
    path('dashboard/', dashboard, name='dashboard'),
    path('track-link/<int:link_id>/', track_link, name='track_link'),
    path('unsubscribe/', unsubscribe, name='unsubscribe'),
    path('unsubscribed_users/', unsubscribed_users_list, name='unsubscribed_users_list'),
]
