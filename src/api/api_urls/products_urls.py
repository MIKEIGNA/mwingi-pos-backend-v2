from django.urls import path

from api import views

product_url_patterns = [
    # ------  Top user views

    
    path(
        'api/pos/products/<int:store_reg_no>/', 
        views.TpProductPosIndexView.as_view(), 
        name='tp_pos_product_index'
    ),

    path(
        'api/products/lean/store/<int:store1_reg_no>/<int:store2_reg_no>/', 
        views.TpLeanProductStoreIndexView.as_view(), 
        name='tp_lean_product_store_index'
    ),


    






    path(
        'api/products/available/data/', 
        views.TpProductAvailableDataView.as_view(), 
        name='tp_product_available_data'
    ),
    path(
        'api/products/lean/', 
        views.TpLeanProductIndexView.as_view(), 
        name='tp_lean_product_index'
    ),
    path(
        'api/products/', 
        views.TpProductIndexView.as_view(), 
        name='tp_product_index'
    ),

    path(
        'api/products/map', 
        views.ProductMapIndexView.as_view(), 
        name='product_map_index'
    ),
    path(
        'api/products/map/<int:reg_no>/', 
        views.TpProductMapEditView.as_view(), 
        name='tp_product_map_edit'
    ),
    path(
        'api/products/transform/map/<int:store_reg_no>/', 
        views.ProductTransformMapIndexView.as_view(), 
        name='product_transform_map_index'
    ),


    path(
        'api/products/<int:reg_no>/', 
        views.TpProductEditView.as_view(), 
        name='tp_product_edit'
    ),




    path(
        'api/ep/products/available/data/', 
        views.EpProductAvailableDataView.as_view(), 
        name='ep_product_available_data'
    ),
    path(
        'api/ep/products/lean/', 
        views.EpLeanProductIndexView.as_view(), 
        name='ep_lean_product_index'
    ),
    path(
        'api/ep/products/', 
        views.EpProductIndexView.as_view(), 
        name='ep_product_index'
    ),
    path(
        'api/ep/products/<int:reg_no>/', 
        views.EpProductEditView.as_view(), 
        name='ep_product_edit'
    ),
    

    path(
        'api/pos/modifiers/<int:store_reg_no>/', 
        views.TpModifierPosIndexView.as_view(), 
        name='tp_pos_modifier_index'
    ),
    path(
        'api/modifiers/lean/', 
        views.TpLeanModifierIndexView.as_view(), 
        name='tp_lean_modifier_index'
    ),
    path(
        'api/modifiers/', 
        views.TpModifierIndexView.as_view(), 
        name='tp_modifier_index'
    ),
    path(
        'api/modifiers/<int:reg_no>/'
        ,views.TpModifierView.as_view(), 
        name='tp_modifier_view'
    ),
    path(
        'api/ep/modifiers/lean/', 
        views.EpLeanModifierIndexView.as_view(), 
        name='ep_lean_modifier_index'
    ),
    path(
        'api/ep/modifiers/', 
        views.EpModifierIndexView.as_view(), 
        name='ep_modifier_index'
    ),
    path(
        'api/ep/modifiers/<int:reg_no>/'
        ,views.EpModifierView.as_view(), 
        name='ep_modifier_view'
    ),

    # ------ Employee user views
    path(
        'api/pos/ep/products/<int:store_reg_no>/', 
        views.EpProductPosIndexView.as_view(), 
        name='ep_pos_product_index'
    ),
    path(
        'api/pos/ep/products/<int:store_reg_no>/edit/<int:reg_no>/', 
        views.EpProductPosEditView.as_view(), 
        name='ep_pos_product_edit'
    ),
    path(
        'api/pos/ep/products/<int:store_reg_no>/edit/image/<int:reg_no>/', 
        views.EpProductPosImageEditView.as_view(), 
        name='ep_pos_product_image'
    ),

    path(
        'api/pos/ep/modifiers/<int:store_reg_no>/', 
        views.EpModifierPosIndexView.as_view(), 
        name='ep_pos_modifier_index'
    ),
]