from django.urls import path
from django.conf import settings

from .views import (
    MakePaymentView,
    SuperPaymentsNotAllowedView,
    SuperPaymentCompleteView,
    MpesaPaymentView
)

MPESA_VALIDATION_RELATIVE_URL_PATH = settings.MPESA_VALIDATION_RELATIVE_URL_PATH
MPESA_CONFIRMATION_RELATIVE_URL_PATH = settings.MPESA_CONFIRMATION_RELATIVE_URL_PATH

app_name = 'billing'
urlpatterns = [
    # SuperUser Payment Urls
    path('billing/payment/make_payment/',
         MakePaymentView.as_view(), name='super_make_payment'),
    path('payment/payment_complete/',
         SuperPaymentCompleteView.as_view(), name='super_payment_complete'),
    path('payment/payment_disabled/', SuperPaymentsNotAllowedView.as_view(),
         name='super_payment_not_allowed'),

    # Mpesa Payment Urls
    path(MPESA_VALIDATION_RELATIVE_URL_PATH, MpesaPaymentView.as_view(
        request_type="validation"), name='mpesa_validation'),
    path(MPESA_CONFIRMATION_RELATIVE_URL_PATH, MpesaPaymentView.as_view(
        request_type="confirmation"), name='mpesa_confirmation'),

]
