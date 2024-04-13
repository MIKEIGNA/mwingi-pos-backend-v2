from collections import OrderedDict
from pprint import pprint

from django.conf import settings

from rest_framework.response import Response

from rest_framework.pagination import PageNumberPagination

from inventories.models.stock_models import StockLevel


class StandardResultsSetPagination_10(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = page_size

class StandardResultsSetPagination_50(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = page_size

class StandardResultsSetPagination_100(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = page_size
class StandardResultsSetPagination_200(PageNumberPagination):
    page_size = 200
    page_size_query_param = 'page_size'
    max_page_size = page_size



class LeanResultsSetPagination(PageNumberPagination):
    page_size = settings.LEAN_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

class ProductPosResultsSetPagination(PageNumberPagination):
    page_size = settings.PRODUCT_POS_PAGINATION_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = page_size

    def get_paginated_response(self, data):

        prices = StockLevel.objects.filter(
            store__reg_no=self.request.data['view_data']['store_reg_no']
        ).values(
            'product__reg_no', 'price'
        )

        price_map = {price['product__reg_no']: price['price'] for price in prices}

        for item in data:
            item['price'] = price_map.get(item['reg_no'], 0)

        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]))


