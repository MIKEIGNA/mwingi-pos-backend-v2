from collections import OrderedDict
from decimal import Decimal
from pprint import pprint

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.utils.user_type import TOP_USER
from api.utils.api_filter_helpers import FilterModelsList
from profiles.models import Profile

from stores.models import Category, Store

from inventories.models import Supplier

class PaginationResponseAddStoresMixin:

    def get_paginated_response(self, data):
    
        if self.request.user.user_type == TOP_USER:
            queryset = Store.objects.filter(profile__user=self.request.user)

        else:
            queryset = Store.objects.filter(
                employeeprofile=self.request.user.employeeprofile
            )

        queryset = queryset.filter(is_deleted=False)

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('stores', FilterModelsList.get_store_list(self.request.user)),
        ]))


class StandardWebResultsAndStoresSetPagination(
    PaginationResponseAddStoresMixin, 
    PageNumberPagination
    ):
    page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION
    page_size_query_param = 'page_size'
    max_page_size = page_size

class EmployeeWebResultsAndStoresSetPagination(
    PaginationResponseAddStoresMixin, 
    PageNumberPagination
    ):
    page_size = settings.LEAN_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

class InventoryHistorResultsSetPagination(PageNumberPagination):
    page_size = settings.STANDARD_WEB_RESULTS_AND_STORES_PAGINATION
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        request_user = self.request.user
        if not request_user.user_type == TOP_USER:
            request_user = get_user_model().objects.get(
                profile__employeeprofile__user=self.request.user
            )

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('users', FilterModelsList.get_user_list(request_user)),
            ('products', FilterModelsList.get_product_list(request_user)),
            ('stores', FilterModelsList.get_store_list(request_user)),
        ])) 
    
class InventoryHistorResultsSetPagination2(PageNumberPagination):
    page_size = settings.INVENTORY_HISTORY_PAGINATION
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        request_user = self.request.user
        if not request_user.user_type == TOP_USER:
            request_user = get_user_model().objects.get(
                profile__employeeprofile__user=self.request.user
            )

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('users', FilterModelsList.get_user_list(request_user)),
            ('products', FilterModelsList.get_product_list(request_user)),
            ('stores', FilterModelsList.get_store_list(request_user)),
        ])) 

class PurchaseOrderWebResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_supplier_list(self):
        
        suppliers_data = []
        if self.request.user.user_type == TOP_USER:
            suppliers_data = Supplier.objects.filter(
                profile__user=self.request.user
            ).order_by('id').values('name', 'reg_no')

        else:
            suppliers_data = Supplier.objects.filter(
                profile=self.request.user.employeeprofile.profile
            ).order_by('id').values('name', 'reg_no')

        return list(suppliers_data)

    def get_paginated_response(self, data):
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('stores', FilterModelsList.get_store_list(self.request.user)),
            ('suppliers', self.get_supplier_list()),
        ]))

class InventoryValuationResultsSetPagination(PageNumberPagination):
    page_size = settings.INVENTORY_VALUATION_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    @staticmethod
    def get_stores_reg_nos(request):
        """
        Retrieves stores__reg_no__in param from request and the turns the reg nos
        into a list if they are there. If they are not found, None is returned
        """

        reg_nos = request.query_params.get('stores__reg_no__in', None)

        if reg_nos:
            # Removes white spaces and splits from commas
            return reg_nos.replace(' ', '').split(',')
        else:
            return None

    def get_store_list(self):
        
        stores_data = []
        if self.request.user.user_type == TOP_USER:
            stores_data = Store.objects.filter(
                profile__user=self.request.user
            ).order_by('name').values('name', 'reg_no')

        else:
            stores_data = Store.objects.filter(
                profile__employeeprofile=self.request.user.employeeprofile
            ).order_by('name').values('name', 'reg_no')

        return list(stores_data)
    
    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)

    def get_paginated_response(self, data):

        # Get profile's inventory value
        profile = self.get_profile()
        profile_inventory_valuation = profile.get_inventory_valuation(
            InventoryValuationResultsSetPagination.get_stores_reg_nos(self.request)
        )
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('profile_inventory_valuation', profile_inventory_valuation),
            ('stores', FilterModelsList.get_store_list(self.request.user)),
        ]))


class ReceiptResultsSetPagination(PageNumberPagination):
    page_size = settings.REPORT_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('payments', FilterModelsList.get_payment_types(self.request.user)),
            ('users', FilterModelsList.get_user_list(self.request.user)),
            ('stores', FilterModelsList.get_store_list(self.request.user)),
            ('receipt_counts', self.request.data['receipts_count'])
        ])) 


class InvoiceResultsSetPagination(PageNumberPagination):
    page_size = settings.REPORT_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data, receipt_counts):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('receipt_counts', receipt_counts),
            ('payments', FilterModelsList.get_payment_types(self.request.user)),
        ]))

class ReportResultsSetPagination(PageNumberPagination):
    page_size = settings.REPORT_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):
        
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('users', FilterModelsList.get_user_list(self.request.user)),
            ('stores', FilterModelsList.get_store_list(self.request.user)),
        ]))

class ReportStorePaymentMethodResultsSetPagination(PageNumberPagination):
    page_size = settings.REPORT_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        if data:
            total_count = 0
            total_amount = 0
            total_refund_count = 0
            total_refund_amount = 0
            for d in data:
                total_count += d['report_data']['count']
                total_amount += Decimal(d['report_data']['amount'])
                total_refund_count += d['report_data']['refund_count']
                total_refund_amount += Decimal(d['report_data']['refund_amount'])

            data.append(
                {
                    'report_data': {
                        'name': 'Total', 
                        'count': total_count, 
                        'amount': str(round(total_amount, 2)), 
                        'refund_count': total_refund_count,
                        'refund_amount': str(round(total_refund_amount, 2)), 
                    }
                }
            )

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('users', FilterModelsList.get_user_list(self.request.user)),
            ('stores', FilterModelsList.get_store_list(self.request.user)),
        ]))


class ProductLeanWebResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_LEAN_WEB_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

class ProductWebResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_WEB_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_category_list(self):
        
        queryset = None
        if self.request.user.user_type == TOP_USER:
            queryset = Category.objects.filter(profile__user=self.request.user)

        else:
            queryset = Category.objects.filter(
                profile=self.request.user.employeeprofile.profile
            )

        querset = queryset.order_by('name').values('name', 'reg_no')

        return list(querset)

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('categories', self.get_category_list()),
            ('stores', FilterModelsList.get_store_list(
                current_user=self.request.user,
                hide_deleted=True
            )),
        ]))
    
class DiscountWebResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_WEB_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('stores', FilterModelsList.get_store_list(
                current_user=self.request.user,
                hide_deleted=True
            )),
        ]))
    
class TaxWebResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_WEB_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('stores', FilterModelsList.get_store_list(
                current_user=self.request.user,
                hide_deleted=True
            )),
        ]))
    
class ProductTransformWebResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_WEB_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('stores', FilterModelsList.get_store_list(
                current_user=self.request.user,
                hide_deleted=True
            )),
        ]))
    

class EmployeeWebResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_WEB_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('stores', FilterModelsList.get_store_list(
                current_user=self.request.user,
                hide_deleted=True
            )),
        ]))