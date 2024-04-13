from django.urls import path

from api import views

inventory_url_patterns = [
    path(
        'api/suppliers/lean/', views.LeanSupplierIndexView.as_view(),
         name='lean_supplier_index'),
    path('api/suppliers/', views.SupplierIndexView.as_view(), name='supplier_index'),
    path('api/suppliers/<int:reg_no>/',
         views.SupplierView.as_view(), name='supplier_view'),

    path(
        'api/stock-adjustments/', views.StockAdjustmentIndexView.as_view(), 
        name='stock_adjustment_index'),
    path(
        'api/stock-adjustments/<int:reg_no>/',
         views.StockAdjustmentView.as_view(), name='stock_adjustment_view'),

    path(
        'api/transfer-orders/', views.TransferOrderIndexView.as_view(),
         name='transfer_order_index'),
    path(
        'api/transfer-orders/auto/', views.TransferOrderCompletedView.as_view(),
         name='transfer_order_index_auto'),

    path(
        'api/transfer-orders/<int:reg_no>/',
         views.TransferOrderView.as_view(), name='transfer_order_view'),
    path(
        'api/transfer-orders/status/<int:reg_no>/',
         views.TransferOrderViewStatus.as_view(), name='transfer_order_view-status'),

    path(
        'api/inventory-counts/', views.InventoryCountIndexView.as_view(), 
        name='inventory_count_index'),
    path(
        'api/inventory-counts/<int:reg_no>/',
         views.InventoryCountView.as_view(), name='inventory_count_view'),
    path(
        'api/inventory-counts/status/<int:reg_no>/',
         views.InventoryCountViewStatus.as_view(), name='inventory_count_view-status'),
    path(
        'api/inventory-history/', views.InventoryHistoryIndexView.as_view(), 
        name='inventory_history_index'),
    path(
        'api/inventory-history2/', views.InventoryHistoryIndexView2.as_view(
            VIEW_TYPE = views.InventoryHistoryIndexView2.VIEW_TYPE_NORMAL
            
        ), 
        name='inventory_history_index2'),
    path(
        'api/inventory-history/csv/', views.InventoryHistoryIndexView2.as_view(
            VIEW_TYPE = views.InventoryHistoryIndexView2.VIEW_TYPE_INVENTORY_CSV
        ), 
        name='inventory_history_index_csv'),

    
    path(
        'api/purchase-orders/', views.PurchaseOrderIndexView.as_view(), 
        name='purchase_order_index'),
    path(
        'api/purchase-orders/<int:reg_no>/',
         views.PurchaseOrderView.as_view(), name='purchase_order_view'),
    path(
        'api/purchase-orders/status/<int:reg_no>/',
         views.PurchaseOrderViewStatus.as_view(), name='purchase_order_view-status'),

    path(
        'api/stock-adjustments/', views.StockAdjustmentIndexView.as_view(), 
        name='stock_adjustment_index'),
    path(
        'api/stock-adjustments/<int:reg_no>/',
         views.StockAdjustmentView.as_view(), name='stock_adjustment_view'),

    path(
        'api/product_transformations/', 
        views.ProductTransformIndexView.as_view(), 
        name='product_transform_index'
    ),
    path(
        'api/product_transformations/<int:reg_no>/',
        views.ProductTransformView.as_view(), 
        name='product_transform_view'
    ),
    

    path(
        'api/inventory-valuation/',
        views.InventoryValuationIndexView.as_view(), 
        name='inventory_valuation_index_view'
    ),

    path(
        'api/inventory-valuation-2/',
        views.InventoryValuationView.as_view(
            VIEW_TYPE = views.InventoryValuationView.VIEW_TYPE_NORMAL
        ), 
        name='inventory_valuation_view'
    ),
    path(
        'api/inventory-valuation-2/csv1/',
        views.InventoryValuationView.as_view(
            VIEW_TYPE = views.InventoryValuationView.VIEW_TYPE_COMPREHENSIVE_CSV_REPORT
        ), 
        name='inventory_valuation_view2'
    ),
    path(
        'api/inventory-valuation-2/csv2/',
        views.InventoryValuationView.as_view(
            VIEW_TYPE = views.InventoryValuationView.VIEW_TYPE_SHORT_CSV_REPORT
        ), 
        name='inventory_valuation_view3'
    ),
    

    

]
