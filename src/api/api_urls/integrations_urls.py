from django.urls import path

from api import views

integrations_url_patterns = [
     
    path(
        'api/tims/receipts/update/',
        views.TimsReceiptUpdateView.as_view(),
        name='tims-receipt-update'
    ),
     
     
]
