from django.urls import path

from api import views

profile_url_patterns = [
    # ------  Top user views
    path('api/roles/lean/', views.LeanRoleIndexView.as_view(), name='lean_role_index'),
    path('api/roles/', views.RoleIndexView.as_view(), name='role_index'),
    path('api/roles/edit/<int:reg_no>/',views.RoleEditView.as_view(), name='role_edit_view'),


    path('api/profile/', views.ProfileEditView.as_view(), name='tp_edit_profile'),
    path('api/profile/picture/', views.ProfilePictureEditView.as_view(), name='tp_edit_profile_image'),
    path('api/profile/users/lean/', views.TpLeanUserIndexView.as_view(), name='tp_user_index_lean'),

    path('api/profile/employees/lean/', views.TpLeanEmployeeProfileIndexView.as_view(), name='tp_employee_profile_index_lean'),
    path('api/profile/employees/', views.TpEmployeeProfileIndexView.as_view(), name='tp_employee_profile_index'),
    path('api/profile/employees/<int:reg_no>/', views.TpEmployeeProfileEditView.as_view(), name='tp_employee_profile_edit'),

    path('api/profile/employees/clusters/', views.TpEmployeeProfileClusterIndexView.as_view(), name='tp_employee_profile_cluster_index'),
    path('api/profile/employees/clusters/<int:reg_no>/', views.TpEmployeeProfileClusterView.as_view(), name='tp_employee_profile_cluster_edit'),
 
    path('api/settings/loyalty/', views.LoyaltySettingView.as_view(), name='loyalty_setting_view'),
    path('api/settings/receipts/', views.ReceiptSettingIndexView.as_view(), name='receipt_setting_index'),
    path('api/settings/receipts/<int:reg_no>/', views.ReceiptSettingView.as_view(), name='receipt_setting_view'),
    path('api/settings/general/', views.UserGeneralSettingView.as_view(), name='user_general_setting_view'),

    path('api/customers/lean/', views.TpLeanCustomerIndexView.as_view(), name='tp_customer_index_lean'),
    path('api/customers/', views.TpCustomerIndexView.as_view(), name='tp_customer_index'),
    path('api/customers/<int:reg_no>/',views.TpCustomerView.as_view(), name='tp_customer_view'),
    
    path('api/pos/customers/', views.TpPosCustomerIndexView.as_view(), name='tp_pos_customer_index'),
    path('api/pos/customers/edit/<int:reg_no>/',views.TpPosCustomerView.as_view(), name='tp_pos_customer_edit_view'),

    # ------ Employee user views
    path('api/ep/profile/', views.EmployeeProfileEditView.as_view(), name='ep_edit_employee_profile'),
    path('api/ep/profile/picture/', views.EmployeeProfilePictureEditView.as_view(), name='ep_edit_employee_profile_image'),
    path('api/ep/profile/users/lean/', views.EpLeanUserIndexView.as_view(), name='ep_user_index_lean'),
    
    path('api/mg/profile/employees/lean/', views.MgLeanEmployeeProfileIndexView.as_view(), name='mg_employee_profile_index_lean'),
    path('api/mg/profile/employees/', views.MgEmployeeProfileIndexView.as_view(), name='mg_employee_profile_index'),

    path('api/ep/customers/lean/', views.EpLeanCustomerIndexView.as_view(), name='ep_customer_index_lean'),
    path('api/ep/customers/', views.EpCustomerIndexView.as_view(), name='ep_customer_index'),
    path('api/ep/customers/<int:reg_no>/',views.EpCustomerView.as_view(), name='ep_customer_edit_view'),

    path('api/ep/pos/customers/', views.EpPosCustomerIndexView.as_view(), name='ep_pos_customer_index'),
    path('api/ep/pos/customers/edit/<int:reg_no>/',views.EpPosCustomerView.as_view(), name='ep_pos_customer_edit_view'),
        
]