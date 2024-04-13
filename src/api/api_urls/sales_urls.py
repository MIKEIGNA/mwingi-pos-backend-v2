from django.urls import path

from api import views

sales_url_patterns = [

     # Receipts index viewS
     path('api/receipts/',views.ReceiptIndexView.as_view(
         VIEW_TYPE = views.ReceiptIndexView.VIEW_TYPE_NORMAL
     ), name='receipt_index'),
     path('api/receipts/csv1/',views.ReceiptIndexView.as_view(
         VIEW_TYPE = views.ReceiptIndexView.VIEW_TYPE_RECEIPT_CSV
     ), name='receipt_index'),
     path('api/receipts/csv2/',views.ReceiptIndexView.as_view(
         VIEW_TYPE = views.ReceiptIndexView.VIEW_TYPE_RECEIPT_CSV_PER_ITEM
     ), name='receipt_index'),

     path('api/receipts/<int:reg_no>/',
         views.ReceiptView.as_view(), name='receipt_view'),

    path('api/pos/receipts/<int:store_reg_no>/',
         views.PosReceiptIndexView.as_view(), name='pos_receipt_index'),

    path('api/pos/internal/receipts/<int:store_reg_no>/',
         views.InternalPosReceiptIndexView.as_view(), name='internal_pos_receipt_index'),


    path('api/pos/receipts/payment/<int:store_reg_no>/<int:reg_no>/',
         views.PosReceiptCompletePaymentView.as_view(), name='pos_receipt_complete_payment'),
    path('api/pos/receipts/refund/<int:store_reg_no>/<int:reg_no>/',
         views.PosReceiptRefundPerLineView.as_view(), name='pos_receipt_refund'),

     path('api/invoices/',views.InvoiceIndexView.as_view(), name='invoice_index'),
     path('api/invoices/<int:reg_no>/',
         views.InvoiceView.as_view(), name='invoice_view'),
     
]
