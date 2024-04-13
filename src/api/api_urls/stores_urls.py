from django.urls import path

from api import views


store_url_patterns = [
    # ------  Top user views
    path('api/stores/', views.TpStoreIndexView.as_view(), name='tp_store_index'),
    path('api/stores/lean/', views.TpLeanStoreIndexView.as_view(), name='tp_store_index_lean'),
    path(
        'api/stores_with_receipt/lean/', 
        views.TpLeanStoreWithReceiptSettingIndexView.as_view(), 
        name='tp_store_with_receipt_index_lean'
    ),
    path('api/stores/edit/<int:reg_no>/', views.TpStoreEditView.as_view(), name='tp_store_edit_view'),

    path('api/categories/', views.TpPosCategoryIndexView.as_view(is_pos=False), name='category_index'),
    path('api/pos/categories/', views.TpPosCategoryIndexView.as_view(is_pos=True), name='pos_category_index'),
    path('api/categories/lean/', views.TpLeanCategoryIndexView.as_view(), name='category_index_lean'),
    path('api/categories/edit/<int:reg_no>/',views.TpCategoryEditView.as_view(), name='category_edit_view'),

    path('api/discounts/', views.TpDiscountIndexView.as_view(), name='tp_discount_index'),
    path('api/discounts/<int:reg_no>/',views.TpDiscountEditView.as_view(), name='tp_discount_edit_view'),

    path('api/pos/discounts/<int:store_reg_no>/', views.TpDiscountPosIndexView.as_view(), name='tp_pos_discount_index'),
    path('api/pos/discounts/<int:store_reg_no>/<int:reg_no>/',views.TpDiscountPosEditView.as_view(), name='tp_pos_discount_edit_view'),

    path('api/taxes/', views.TpTaxIndexView.as_view(), name='tp_tax_index'), 
    path('api/taxes/edit/<int:reg_no>/',views.TpTaxEditView.as_view(), name='tp_tax_edit_view'),

    path('api/pos/taxes/<int:store_reg_no>/', views.TpTaxPosIndexView.as_view(), name='tp_pos_tax_index'),
    path('api/pos/taxes/edit/<int:store_reg_no>/<int:reg_no>/',views.TaxPosEditView.as_view(), name='tp_pos_tax_edit_view'),

    
    # ------ Employee user views
    path('api/ep/stores/', views.EpStoreIndexView.as_view(), name='ep_store_index'),
    path(
        'api/ep/stores_with_receipt/lean/', 
        views.EpStoreIndexView.as_view(), 
        name='ep_store_with_receipt_index_lean'
    ),
    path('api/ep/stores/lean/', views.EpLeanStoreIndexView.as_view(), name='ep_store_index_lean'),

    
    path('api/ep/categories/', views.EpPosCategoryIndexView.as_view(is_pos=False), name='ep_category_index'),
    path('api/ep/pos/categories/', views.EpPosCategoryIndexView.as_view(is_pos=True), name='ep_pos_category_index'),
    path('api/ep/categories/lean/', views.EpLeanCategoryIndexView.as_view(), name='ep_category_index_lean'),
    path('api/ep/categories/edit/<int:reg_no>/',views.EpCategoryEditView.as_view(), name='ep_category_edit_view'),

    path('api/ep/discounts/', views.EpDiscountIndexView.as_view(), name='ep_discount_index'),
    path('api/ep/discounts/<int:reg_no>/',views.EpDiscountEditView.as_view(), name='ep_discount_edit_view'),

    path('api/ep/pos/discounts/<int:store_reg_no>/', views.EpDiscountPosIndexView.as_view(), name='ep_pos_discount_index'),
    path('api/ep/pos/discounts/edit/<int:store_reg_no>/<int:reg_no>/',views.EpDiscountPosEditView.as_view(), name='ep_pos_discount_edit_view'),

    path('api/ep/taxes/', views.EpTaxIndexView.as_view(), name='ep_tax_index'),
    path('api/ep/pos/taxes/<int:store_reg_no>/', views.EpTaxPosIndexView.as_view(), name='ep_pos_tax_index'),
    
]