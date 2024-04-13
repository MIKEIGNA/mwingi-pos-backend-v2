from django.urls import path

from api import views

loyverse_url_patterns = [
    path(
        'api/loyverse/webhook/receipt-update/',
        views.LoyverseWebhookReceiptUpdateView.as_view(),
        name='loyverse_webhook_receipt_update'
    ),
    path(
        'api/loyverse/webhook/tax-update/',
        views.LoyverseWebhookCustomerUpdateView.as_view(),
        name='loyverse_webhook_customer_update'
    ),
    path(
        'api/loyverse/webhook/tax-update/',
        views.LoyverseWebhookTaxUpdateView.as_view(),
        name='loyverse_webhook_tax_update'
    ),
    path(
        'api/loyverse/webhook/loyverse_app_data/',
        views.LoyverseLoyverseAppDataUpdateView.as_view(),
        name='loyverse_webhook_loyverse_app_data'
    ),

]