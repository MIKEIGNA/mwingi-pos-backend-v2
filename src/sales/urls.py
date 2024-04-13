from django.urls import path

from .views import ReceiptEmailIndexView, ReceiptEmailView

app_name = 'sales'      
urlpatterns = [
    path('sales/', ReceiptEmailIndexView.as_view(), name='receipt_index'), 
    path('sales/<int:pk>/', ReceiptEmailView.as_view(), name='receipt_view')        
]

