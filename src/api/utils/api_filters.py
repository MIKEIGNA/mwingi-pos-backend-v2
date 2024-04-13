from django.contrib.auth import get_user_model
from django_filters import FilterSet
from django_filters.filters import (
    BooleanFilter, 
    DateFromToRangeFilter, 
    DateTimeFromToRangeFilter,
    NumberFilter,
    BaseInFilter
)
from django.conf import settings
from core.queryset_helpers import QuerysetFilterHelpers
from inventories.models import InventoryCount, InventoryHistory, ProductTransform, PurchaseOrder, StockAdjustment, TransferOrder

from products.models import Modifier, Product
from sales.models import Invoice, Receipt
from stores.models import Category, Discount, StorePaymentMethod, Tax


class NumberInFilter(BaseInFilter, NumberFilter):
    pass

class ReceiptFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    datetime = DateTimeFromToRangeFilter(
        field_name='created_date', 
        method='datetime_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='store__reg_no',
        lookup_expr='in'
    )
    reg_nos = NumberInFilter(
        field_name='reg_no',
        lookup_expr='in'
    )
    # user_reg_no = NumberInFilter(
    #     field_name='user__reg_no',
    #     lookup_expr='in'
    # )

    is_refund = BooleanFilter()
    payment_type_reg_no = NumberInFilter(
        field_name='receiptpayment__payment_method__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):

        if not self.request.user.is_authenticated:
            self.request.user = get_user_model().objects.get(
                email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
            )
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    def datetime_filter(self, queryset, name, value):

        if not self.request.user.is_authenticated:
            self.request.user = get_user_model().objects.get(email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_datetime_filter(
            queryset=queryset,
            field_name=name,
            datetime_after=self.data['datetime_after'],
            datetime_before=self.data['datetime_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = Receipt
        fields = [
            'date',
            'datetime',
            'store_reg_no', 
            # 'user_reg_no', 
            'is_refund',
            'reg_nos',
            'payment_type_reg_no'
        ]


class InvoiceFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    payment_completed = BooleanFilter()
    payment_type_reg_no = NumberFilter(field_name='payment_type__reg_no')

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset
    class Meta:
        model = Invoice
        fields = [
            'date',
            'payment_completed',
            'payment_type_reg_no'
        ]



class DiscountReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='receipt__created_date',
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='receipt__store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='receipt__user__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset
    
    class Meta:
        model = Discount
        fields = ['date', 'store_reg_no', 'user_reg_no']


class TaxReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='receipt__created_date',
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='receipt__store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='receipt__user__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset

    class Meta:
        model = Tax
        fields = ['date', 'store_reg_no', 'user_reg_no']


class CategoryReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='product__receiptline__receipt__created_date',
        method='date_filter'
    )
    
    store_reg_no = NumberInFilter(
        field_name='product__receiptline__receipt__store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='product__receiptline__receipt__user__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset

    class Meta:
        model = Category
        fields = ['date', 'store_reg_no', 'user_reg_no']

class ProductReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='receiptline__receipt__created_date',
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='receiptline__receipt__store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='receiptline__receipt__user__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset

    class Meta:
        model = Product
        fields = ['date', 'store_reg_no', 'user_reg_no']


class ModifierReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='modifieroption__receiptline__receipt__created_date',
        method='date_filter'
    )
    store_reg_no = NumberFilter(
        field_name='modifieroption__receiptline__receipt__store__reg_no'
    )
    user_reg_no = NumberFilter(
        field_name='modifieroption__receiptline__receipt__user__reg_no'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset

    class Meta:
        model = Modifier
        fields = ['date', 'store_reg_no', 'user_reg_no']


class StorePaymentMethodReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='receiptpayment__receipt__created_date',
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='receiptpayment__receipt__store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='receiptpayment__receipt__user__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset

    class Meta:
        model = StorePaymentMethod
        fields = ['date', 'store_reg_no', 'user_reg_no']


class UserReportFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='receipt__created_date',
        method='date_filter',
    )
    store_reg_no = NumberInFilter(
        field_name='receipt__store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='receipt__user__reg_no'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )

        return queryset

    class Meta:
        model = get_user_model()
        fields = ['date', 'store_reg_no']


class StockAdjustmentFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='store__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = StockAdjustment
        fields = [
            'date',
            'store_reg_no', 
            'reason',
        ]

class PurchaseOrderFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    supplier_reg_no = NumberInFilter(
        field_name='supplier__reg_no',
        lookup_expr='in'
    )
    store_reg_no = NumberInFilter(
        field_name='store__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = PurchaseOrder
        fields = [
            'date',
            'supplier_reg_no',
            'store_reg_no', 
            'status',
        ]


class TransferOrderFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    source_store_reg_no= NumberInFilter(
        field_name='source_store__reg_no',
        lookup_expr='in'
    )
    destination_store_reg_no = NumberInFilter(
        field_name='destination_store__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = TransferOrder
        fields = [
            'date',
            'source_store_reg_no',
            'destination_store_reg_no', 
            'status',
        ]

class InventoryCountFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='store__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = InventoryCount
        fields = [
            'date',
            'store_reg_no', 
            'status',
        ]


class InventoryHistoryFilterFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='store__reg_no',
        lookup_expr='in'
    )
    user_reg_no = NumberInFilter(
        field_name='user__reg_no',
        lookup_expr='in'
    )
    product_reg_no = NumberInFilter(
        field_name='product__reg_no',
        lookup_expr='in'
    )
    reason = NumberInFilter(
        field_name='reason',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = InventoryHistory
        fields = [
            'date',
            'store_reg_no', 
            'user_reg_no',
            'product_reg_no',
            'reason',
        ]

class ProductTransformFilter(FilterSet):
    date = DateFromToRangeFilter(
        field_name='created_date', 
        method='date_filter'
    )
    store_reg_no = NumberInFilter(
        field_name='store__reg_no',
        lookup_expr='in'
    )

    def date_filter(self, queryset, name, value):
        
        # We filter date manually
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name=name,
            date_after=self.data['date_after'],
            date_before=self.data['date_before'],
            local_timezone=self.request.user.get_user_timezone()
        )
        
        return queryset

    class Meta:
        model = ProductTransform
        fields = [
            'date',
            'store_reg_no', 
        ]