from django.urls import path

from api import views

webhook_url_patterns = [
     
    path(
        'api/webhook/stock-levels/',
        views.ApiStockLevelIndexView.as_view(), 
        name='webhook_stock_levels'
    ),
    path(
        'api/webhook/customers/',
        views.ApiCustomerIndexView.as_view(), 
        name='webhook_customers'
    ),
    path(
        'api/webhook/employees/',
        views.ApiEmployeeIndexView.as_view(), 
        name='webhook_empoyees'
    ),
    path(
        'api/webhook/taxes/',
        views.ApiTaxIndexView.as_view(), 
        name='webhook_taxes'
    ),
    path(
        'api/webhook/stores/',
        views.ApiStoreIndexView.as_view(), 
        name='webhook_stores'
    ),
    path(
        'api/webhook/products/',
        views.ApiProductIndexView.as_view(), 
        name='webhook_products'
    ),
    path(
        'api/webhook/receipts/',
        views.ApiReceiptIndexView.as_view(), 
        name='webhook_receipts'
    ),
     
     
]
