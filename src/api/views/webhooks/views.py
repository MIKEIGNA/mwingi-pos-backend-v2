from django.conf import settings
from django.db.models.query_utils import Q
from django.contrib.auth import get_user_model

import django_filters

from rest_framework import generics
from rest_framework import filters

from api.serializers.webhooks.webhook_serializers import ApiCustomerIndexViewSerializer, ApiEmployeeIndexViewSerializer, ApiProductIndexViewSerializer, ApiReceiptIndexViewSerializer, ApiStockLevelIndexViewSerializer, ApiStoreIndexViewSerializer, ApiTaxIndexViewSerializer
from api.utils.api_filters import ReceiptFilter
from api.utils.api_pagination import StandardResultsSetPagination_200

from inventories.models import StockLevel
from profiles.models import Customer
from sales.models import Receipt
from stores.models import Store, Tax
from products.models import Product

class ApiStockLevelIndexView(generics.ListAPIView):
    queryset = StockLevel.objects.all()
    serializer_class = ApiStockLevelIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200

    def get_queryset(self):
     
        queryset = super(ApiStockLevelIndexView, self).get_queryset()

        queryset = queryset.filter(
            store__profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        ).order_by('id')

        return queryset

class ApiCustomerIndexView(generics.ListAPIView):
    queryset = Customer.objects.all()
    serializer_class = ApiCustomerIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_fields = ['reg_no']

    def get_queryset(self):
     
        queryset = super(ApiCustomerIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        ).order_by('id')

        return queryset

class ApiEmployeeIndexView(generics.ListAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = ApiEmployeeIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200

    def get_queryset(self):
     
        queryset = super(ApiEmployeeIndexView, self).get_queryset()

        queryset = queryset.filter(
            Q(email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT) | 
            Q(employeeprofile__profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)
        ).order_by('id')

        return queryset

class ApiTaxIndexView(generics.ListAPIView):
    queryset = Tax.objects.all()
    serializer_class = ApiTaxIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200

    def get_queryset(self):
     
        queryset = super(ApiTaxIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        ).order_by('id')

        return queryset

class ApiStoreIndexView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = ApiStoreIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200

    def get_queryset(self):
     
        queryset = super(ApiStoreIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        ).order_by('id')

        return queryset

class ApiProductIndexView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ApiProductIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200

    def get_queryset(self):
     
        queryset = super(ApiProductIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        ).order_by('id')

        return queryset

class ApiReceiptIndexView(generics.ListAPIView):
    queryset = Receipt.objects.all()
    serializer_class = ApiReceiptIndexViewSerializer
    permission_classes = ()
    pagination_class = StandardResultsSetPagination_200 
    filterset_class=ReceiptFilter 

    def get_queryset(self):
     
        queryset = super(ApiReceiptIndexView, self).get_queryset()

        queryset = queryset.filter(
            Q(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT) | 
            Q(user__employeeprofile__profile__user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)
        ).order_by('-id')

        return queryset 