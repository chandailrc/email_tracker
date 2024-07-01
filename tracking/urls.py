# -*- coding: utf-8 -*-

from django.urls import path
from .views import *
import logging

logger = logging.getLogger(__name__)

def log_request_pixel(view_func):
    def wrapper(request, *args, **kwargs):
        logger.info(f"urls.py: PIXEL Request received for email with id: {request.GET.get('email_id')}")
        return view_func(request, *args, **kwargs)
    return wrapper

def log_request_link(view_func):
    def wrapper(request, *args, **kwargs):
        logger.info(f"urls.py: LINK Request received for email with id: {request.GET.get('email_id')}")
        return view_func(request, *args, **kwargs)
    return wrapper

urlpatterns = [
    path('compose/', compose_email_view, name='compose_email'),
    path('send-tracked-email/', send_tracked_email_view, name='send_tracked_email_view'),
    # path('tracking/<int:email_id>/', track_email, name='track_email'),
    path('pixel.png', log_request_pixel(tracking_pixel), name='tracking_pixel'),
    path('dashboard/', dashboard, name='dashboard'),
    path('track-link/<int:link_id>/', log_request_link(track_link), name='track_link'),
    path('unsubscribe/', unsubscribe, name='unsubscribe'),
    path('unsubscribed_users/', unsubscribed_users_list, name='unsubscribed_users_list'),
]