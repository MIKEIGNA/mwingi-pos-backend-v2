from django.urls import path

from api import views

reports_url_patterns = [
    # Sales report 1
    path(
        'api/reports/summary/', 
        views.TpSaleSummaryView.as_view(), 
        name='tp_sale_summary_view'
    ),
    path(
        'api/reports/products/', 
        views.SalesReportView.as_view(report_type=views.SalesReportView.PRODUCT_REPORT), 
        name='product_report_view'
    ),
    path(
        'api/reports/categories/', 
        views.SalesReportView.as_view(report_type=views.SalesReportView.CATEGORY_REPORT), 
        name='category_report_view'
    ),
    path(
        'api/reports/employees/', 
        views.SalesReportView.as_view(report_type=views.SalesReportView.EMPLOYEE_REPORT), 
        name='employee_report_view'
    ),
    path(
        'api/reports/taxes/', 
        views.SalesReportView.as_view(report_type=views.SalesReportView.TAX_REPORT), 
        name='tax_report_view'
    ),
    path(
        'api/reports/stores/', 
        views.SalesReportView.as_view(report_type=views.SalesReportView.STORE_REPORT), 
        name='tax_report_view'
    ),

    # Sales report 1
    path(
        'api/reports/summary2/', 
        views.TpSaleSummaryView2.as_view(), 
        name='tp_sale_summary_view'
    ),
    path(
        'api/reports/products2/', 
        views.SalesReportView2.as_view(report_type=views.SalesReportView2.PRODUCT_REPORT), 
        name='product_report_view'
    ),
    path(
        'api/reports/categories2/', 
        views.SalesReportView2.as_view(report_type=views.SalesReportView2.CATEGORY_REPORT), 
        name='category_report_view'
    ),
    path(
        'api/reports/employees2/', 
        views.SalesReportView2.as_view(report_type=views.SalesReportView2.EMPLOYEE_REPORT), 
        name='employee_report_view'
    ),
    path(
        'api/reports/taxes2/', 
        views.SalesReportView2.as_view(report_type=views.SalesReportView2.TAX_REPORT), 
        name='tax_report_view'
    ),
    path(
        'api/reports/stores2/', 
        views.SalesReportView2.as_view(report_type=views.SalesReportView2.STORE_REPORT), 
        name='tax_report_view'
    ),
    


    
    path(
        'api/ep/reports/summary/', 
        views.EpSaleSummaryView.as_view(), 
        name='ep_sale_summary_view'
    ),
    path(
        'api/ep/reports/users/',
        views.EpUserReportIndexView.as_view(), 
        name='ep_user_report_index'
    ),
    path(
        'api/ep/reports/categories/', 
        views.EpCategoryReportIndexView.as_view(), 
        name='ep_category_report_index'
    ),
    path(
        'api/ep/reports/discounts/', 
        views.EpDiscountReportIndexView.as_view(),
        name='ep_discount_report_index'
    ),
    path(
        'api/ep/reports/taxes/', 
        views.EpTaxReportIndexView.as_view(), 
        name='ep_tax_report_index'
    ),
    path(
        'api/ep/reports/products/', 
        views.EpProductReportIndexView.as_view(), 
        name='ep_product_report_index'
    ),
    path(
        'api/ep/reports/modifiers/', 
        views.EpModifierReportIndexView.as_view(), 
        name='ep_modifier_report_index'
    ),
    path(
        'api/ep/reports/payments/', 
        views.EpStorePaymentMethodReportIndexView.as_view(), 
        name='ep_store_payment_report_index'
    ),

]