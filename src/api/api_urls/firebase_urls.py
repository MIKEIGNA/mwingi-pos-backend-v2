from django.urls import path

from api import views

firebase_url_patterns = [
    path('api/fcm/', views.FirebaseDeviceView.as_view(), name='fcm'),
]