from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from inventories.models import Product

from profiles.models import EmployeeProfile

PERMISSION_DEFS = {
    'can_view_shift_reports': 'Can view shift reports',
    'can_manage_open_tickets': 'Can manage open tickets',
    'can_void_open_ticket_items': 'Can void saved items in open tickets',

    'can_manage_items': 'Can manage items',
    'can_refund_sale': 'Can refund sale',
    'can_open_drawer': 'Can open drawer',
    'can_reprint_receipt': 'Can reprint receipt',
    'can_change_settings': 'Can change settings',
    'can_apply_discount': 'Can apply discount',
    'can_change_taxes': 'Can change taxes',

    'can_accept_debt': 'Can accept debt',
    'can_manage_customers': 'Can manage customer',
    'can_manage_employees': 'Can manage employee',
    'can_change_general_settings': 'Can change general settings',

    'can_view_customers': 'Can view all customers',
    'can_edit_purchase_order_date': 'Can edit purchase order date',

    'can_view_items': 'Can view items',
    'can_view_inventory': 'Can view inventory',
    'can_view_reports': 'Can view reports',
    'can_view_employees': 'Can view employees',
    'can_view_clusters': 'Can view clusters',
    'can_view_stores': 'Can view stores',
    'can_view_settings': 'Can view settings',

    'can_view_profits': 'Can view profits',

}

class CreatePermission:
    
    @staticmethod
    def create_permissions():

        for key, value in PERMISSION_DEFS.items():
            Permission.objects.get_or_create(
                codename=key,
                name=value,
                content_type=ContentType.objects.get_for_model(get_user_model()),
            )
        
class PermissionHelpers:
    
    @staticmethod
    def assign_group_permissions(group, perms):
        """
        If a permissoin name is in perms with a value of True, it is assigned
        to the group

        Args:
            group: UserGroup
            perms: A dict with permission names as key and boolean values indicationg
                   if they should be added to group or not
        """
        selected_perms_names = []
        for key, value in perms.items():
            if value:
                selected_perms_names.append(key)

        selected_perms = Permission.objects.filter(
            codename__in=selected_perms_names,
            content_type=ContentType.objects.get_for_model(get_user_model())
        )

        group.permissions.set(selected_perms)


class GetPermission():

    def __init__(self):
        pass

    def _get_permission(self, codename, model):
        return  Permission.objects.get(
            codename=codename,
            content_type=ContentType.objects.get_for_model(model)
        )

    def _get_user_permission(self, codename):
        return  Permission.objects.get(
            codename=codename,
            content_type=ContentType.objects.get_for_model(get_user_model())
        )

    def get_manage_employee_permission(self):
        return self._get_permission(
            codename='add_employeeprofile',
            model=EmployeeProfile
        )

    def get_manage_products_permission(self):
        return self._get_permission(
            codename='can_manage_items',
            model=Product
        )

    def get_owner_permissions(self):

        # Give owner all permissions

        permissions = [
            self._get_user_permission(key) for key, _ in PERMISSION_DEFS.items()]

        # permissions = [
        #     self._get_user_permission('can_view_shift_reports'),
        #     self._get_user_permission('can_manage_open_tickets'),
        #     self._get_user_permission('can_void_open_ticket_items'),

        #     self._get_user_permission('can_manage_items'),
        #     self._get_user_permission('can_refund_sale'),
        #     self._get_user_permission('can_open_drawer'),
        #     self._get_user_permission('can_reprint_receipt'),
        #     self._get_user_permission('can_change_settings'),
        #     self._get_user_permission('can_apply_discount'),
        #     self._get_user_permission('can_change_taxes'),

        #     self._get_user_permission('can_accept_debt'),
        #     self._get_user_permission('can_manage_customers'),
        #     self._get_user_permission('can_manage_employees'),
        #     self._get_user_permission('can_change_general_settings'),
        #     self._get_user_permission('can_view_customers'),
        #     self._get_user_permission('can_edit_purchase_order_date')
        # ]

        return permissions

    def get_manager_permissions(self):

        permissions = [
            self._get_user_permission('can_view_shift_reports'),
            self._get_user_permission('can_manage_open_tickets'),
            self._get_user_permission('can_void_open_ticket_items'),

            self._get_user_permission('can_manage_items'),
            self._get_user_permission('can_refund_sale'),
            self._get_user_permission('can_open_drawer'),
            self._get_user_permission('can_reprint_receipt'),
            self._get_user_permission('can_change_settings'),
            self._get_user_permission('can_apply_discount'),
            self._get_user_permission('can_change_taxes'),
            self._get_user_permission('can_view_customers')
        ]

        return permissions

    def get_cashier_permissions(self):

        permissions = []

        return permissions

'''

>  add_firebasedevice
>  change_firebasedevice
>  delete_firebasedevice
>  view_firebasedevice
>  add_resetpasswordtoken
>  change_resetpasswordtoken
>  delete_resetpasswordtoken
>  view_resetpasswordtoken
>  add_user
>  change_user
>  delete_user
>  view_user
>  add_userchannelrecord
>  change_userchannelrecord
>  delete_userchannelrecord
>  view_userchannelrecord
>  add_usersession
>  change_usersession
>  delete_usersession
>  view_usersession
>  add_websocketticket
>  change_websocketticket
>  delete_websocketticket
>  view_websocketticket
>  add_logentry
>  change_logentry
>  delete_logentry
>  view_logentry
>  add_group
>  change_group
>  delete_group
>  view_group
>  add_permission
>  change_permission
>  delete_permission
>  view_permission
>  add_token
>  change_token
>  delete_token
>  view_token
>  add_tokenproxy
>  change_tokenproxy
>  delete_tokenproxy
>  view_tokenproxy
>  add_payment
>  change_payment
>  delete_payment
>  view_payment
>  add_subscription
>  change_subscription
>  delete_subscription
>  view_subscription
>  add_contenttype
>  change_contenttype
>  delete_contenttype
>  view_contenttype
>  add_clockedschedule
>  change_clockedschedule
>  delete_clockedschedule
>  view_clockedschedule
>  add_crontabschedule
>  change_crontabschedule
>  delete_crontabschedule
>  view_crontabschedule
>  add_intervalschedule
>  change_intervalschedule
>  delete_intervalschedule
>  view_intervalschedule
>  add_periodictask
>  change_periodictask
>  delete_periodictask
>  view_periodictask
>  add_periodictasks
>  change_periodictasks
>  delete_periodictasks
>  view_periodictasks
>  add_solarschedule
>  change_solarschedule
>  delete_solarschedule
>  view_solarschedule
>  add_product
>  change_product
>  delete_product
>  view_product
>  add_productbundle
>  change_productbundle
>  delete_productbundle
>  view_productbundle
>  add_productcount
>  change_productcount
>  delete_productcount
>  view_productcount
>  add_receipt
>  change_receipt
>  delete_receipt
>  view_receipt
>  add_receiptcount
>  change_receiptcount
>  delete_receiptcount
>  view_receiptcount
>  add_receiptline
>  change_receiptline
>  delete_receiptline
>  view_receiptline
>  add_receiptlinecount
>  change_receiptlinecount
>  delete_receiptlinecount
>  view_receiptlinecount
>  add_mpesalog
>  change_mpesalog
>  delete_mpesalog
>  view_mpesalog
>  add_paymentlog
>  change_paymentlog
>  delete_paymentlog
>  view_paymentlog
>  add_requesttimeseries
>  change_requesttimeseries
>  delete_requesttimeseries
>  view_requesttimeseries
>  add_useractivitylog
>  change_useractivitylog
>  delete_useractivitylog
>  view_useractivitylog
>  add_mysetting
>  change_mysetting
>  delete_mysetting
>  view_mysetting
>  add_customer
>  change_customer
>  delete_customer
>  view_customer
>  add_customercount
>  change_customercount
>  delete_customercount
>  view_customercount
>  add_employeeprofile
>  change_employeeprofile
>  delete_employeeprofile
>  add_employeeprofile
>  add_employeeprofilecount
>  change_employeeprofilecount
>  delete_employeeprofilecount
>  add_employeeprofilecount
>  add_profile
>  change_profile
>  delete_profile
>  view_profile
>  add_profilecount
>  change_profilecount
>  delete_profilecount
>  view_profilecount
>  add_session
>  change_session
>  delete_session
>  view_session
>  add_category
>  change_category
>  delete_category
>  view_category
>  add_categorycount
>  change_categorycount
>  delete_categorycount
>  view_categorycount
>  add_discount
>  change_discount
>  delete_discount
>  view_discount
>  add_discountcount
>  change_discountcount
>  delete_discountcount
>  view_discountcount
>  add_store
>  change_store
>  delete_store
>  view_store
>  add_storecount
>  change_storecount
>  delete_storecount
>  view_storecount
>  add_tax
>  change_tax
>  delete_tax
>  view_tax
>  add_taxcount
>  change_taxcount
>  delete_taxcount
>  view_taxcount
.


'''