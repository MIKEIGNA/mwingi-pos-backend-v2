from django.contrib.auth import get_user_model
from django.db.models.query_utils import Q

from accounts.utils.user_type import TOP_USER
from products.models import Product
from stores.models import StorePaymentMethod
from stores.models import Store

class FilterModelsList():

    @staticmethod
    def get_user_list(current_user):
       
        user_data = []
        if current_user.user_type == TOP_USER:
            
            users = get_user_model().objects.filter(
                Q(pk=current_user.pk) | 
                Q(employeeprofile__profile__user=current_user)
            ).order_by('first_name').values(
                'first_name', 
                'last_name', 
                'reg_no'
            )

        else:

            user_data.append(
                {
                    'name': current_user.get_full_name(), 
                    'reg_no': current_user.reg_no
                }
            )

            users = get_user_model().objects.filter(
                Q(employeeprofile__stores__employeeprofile__user=current_user) | 
                Q(profile__store__employeeprofile__user=current_user)
            ).exclude(reg_no=current_user.reg_no
            ).values(
                'first_name', 
                'last_name', 
                'reg_no'
            ).distinct()

        for emp in users:
            user_data.append(
                {
                    'name': f"{emp['first_name']} {emp['last_name']}", 
                    'reg_no': emp['reg_no']
                }
            )

        # Ored user_data by name
        user_data = sorted(user_data, key=lambda k: k['name'])
            
        return user_data

    @staticmethod
    def get_store_list(current_user, hide_deleted=False):
        
        stores_data = []
        if current_user.user_type == TOP_USER:
            queryset = Store.objects.filter(profile__user=current_user)

        else:
            queryset = Store.objects.filter(
                employeeprofile__user=current_user
            )

        if hide_deleted:
            queryset = queryset.filter(is_deleted=False)

        stores_data = queryset.order_by('name').values(
            'name', 
            'is_shop', 
            'is_truck', 
            'is_warehouse', 
            'reg_no',
            'is_deleted',
            'deleted_date_str',
            'created_date_str',
        )

        return list(stores_data)

    @staticmethod
    def get_product_list(current_user):
        
        stores_data = []
        if current_user.user_type == TOP_USER:
            stores_data = Product.objects.filter(
                profile__user=current_user,
                is_deleted=False
            ).order_by('name').values('name', 'reg_no')

        else:
            stores_data = Product.objects.filter(
                employeeprofile__user=current_user,
                is_deleted=False
            ).order_by('name').values('name', 'reg_no')

        return list(stores_data)

    @staticmethod
    def get_payment_types(current_user):
        
        data = []
        if current_user.user_type == TOP_USER:
            data = StorePaymentMethod.objects.filter(
                profile__user=current_user
            ).order_by('name').values('name', 'reg_no')

        else:
            data = StorePaymentMethod.objects.filter(
                profile__employeeprofile__user=current_user
            ).order_by('name').values('name', 'reg_no')

        return list(data)

