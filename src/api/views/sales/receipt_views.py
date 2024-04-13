import csv
from decimal import Decimal

from django.http import StreamingHttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import (
    F, 
    Value, 
    CharField, 
    ExpressionWrapper, 
    Case,
    When
) 
from django.db.models.functions import Cast
from django.contrib.postgres.aggregates.general import StringAgg
from django.db.models.functions import Concat

from rest_framework import generics
from rest_framework import permissions
from rest_framework import filters

from api.serializers import ReceiptListSerializer, ReceiptViewSerializer
from api.utils.api_filters import ReceiptFilter
from api.utils.api_web_pagination import ReceiptResultsSetPagination

from accounts.utils.user_type import TOP_USER
from sales.models import Receipt, ReceiptLine
from django.db.models.functions import Coalesce, Round

 
class ReceiptIndexView(generics.ListCreateAPIView):

    VIEW_TYPE_NORMAL = 'normal'
    VIEW_TYPE_RECEIPT_CSV = 'receipt_csv'
    VIEW_TYPE_RECEIPT_CSV_PER_ITEM = 'receipt_csv_per_item'

    # Default view type
    VIEW_TYPE = VIEW_TYPE_NORMAL

    queryset = Receipt.objects.all().select_related(
        'user', 'store', 'customer', 'tax', 'discount'
    )
    serializer_class = ReceiptListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = ReceiptResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class=ReceiptFilter 
    search_fields = ['receipt_number',]


    # Customer fields
    customer = None
    receipt_classification = {
        'refunds': 0,
        'sales': 0,
        'all_receipts': 0
    }

    def csv_per_receipt_response(self):

        data = [
            [
                'Created Date', 
                'Sync Date',
                'Receipt Number', 
                'Receipt Type', 
                'Gross sales', 
                'Discounts', 
                'Net sales', 
                'Taxes', 
                'Store', 
                'Cashier Name', 
                'Customer Name', 
                'Products'
            ]
        ] 
        
        # Get the already filtered receipts
        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.annotate(
            created_datetime_str=Cast('created_date', output_field=CharField()),
            sync_datetime_str=Cast('sync_date', output_field=CharField()),
            receipt_type=Case(
                When(is_refund=True, then=Value('Refund')),
                default=Value('Sale'),
                output_field=CharField()
            ),
            gross_total_amount_str=Case(
                When(
                    is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('subtotal_amount'), 
                    output_field=CharField()
                ), output_field=CharField())),
                default=Cast('subtotal_amount', output_field=CharField())
            ),
            discount_amount_str=Case(
                When(
                    is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('discount_amount'), 
                    output_field=CharField()), output_field=CharField())
                ),
                default=Cast('discount_amount', output_field=CharField())
            ),
            total_amount_str=Case(
                When(
                    is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('total_amount'), 
                    output_field=CharField()
                ), output_field=CharField())),
                default=Cast('total_amount', output_field=CharField())
            ),
            tax_amount_str=Case(
                When(
                    is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('tax_amount'), 
                    output_field=CharField()
                ), output_field=CharField())),
                default=Cast('tax_amount', output_field=CharField())
            ),
            cashier_name=Concat('user__first_name', Value(' '), 'user__last_name', output_field=CharField()),
            receiptline_names=StringAgg(
                Concat( 
                    F('receiptline__units'), Value(' X '), F('receiptline__product__name')
                ), ', ', distinct=True, 
                output_field=CharField()
            )
        ).order_by('-created_date').values_list(
            'created_datetime_str',
            'sync_datetime_str',
            'receipt_number',
            'receipt_type',
            'gross_total_amount_str',
            'discount_amount_str',
            'total_amount_str',
            'tax_amount_str',
            'store__name', 
            'cashier_name',
            'customer__name',
            'receiptline_names',
        ) 

        receipt_list = [receipt for receipt in list(queryset)]
        data += receipt_list

        class Echo:
            def write(self, value): return value

        echo_buffer = Echo()
        csv_writer = csv.writer(echo_buffer)

        # By using a generator expression to write each row in the queryset
        # python calculates each row as needed, rather than all at once.
        # Note that the generator uses parentheses, instead of square
        # brackets – ( ) instead of [ ].
        rows = (csv_writer.writerow(row) for row in data)

        response = StreamingHttpResponse(rows, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users.csv"'
        return response

    def csv_per_item_response(self):

        data = [
            [
                'Created Date', 
                'Sync Date',
                'Receipt Number', 
                'Receipt Type', 
                'Product Name', 
                'Units', 
                'Gross sales', 
                'Discounts', 
                'Net sales',
                'Costs', 
                'Profit', 
                'Taxes', 
                'Net Sales W/O VAT', 
                'Store Name', 
                'Cashier Name'
            ],
        ]

        multiplied_tax_amount=Round(
            Coalesce(
                ((F('total_amount') / (F('tax__rate') + 100)) * F('tax__rate')),
                Decimal(0.00)
            ), 
            2
        )
        profit=Coalesce(
            F('total_amount') - F('cost_total'),
            Decimal(0.00)
        )
        net_sales_wo_vat=Round(
            Coalesce(
                F('total_amount') - multiplied_tax_amount,
                Decimal(0.00)
            ),
            2
        )

        # Get the already filtered receipts
        queryset = self.filter_queryset(self.get_queryset())

        queryset = ReceiptLine.objects.filter(receipt__in=queryset).annotate(
            created_datetime_str=Cast('created_date', output_field=CharField()),
            sync_datetime_str=Cast('receipt__sync_date', output_field=CharField()),
            receipt_type=Case(
                When(receipt__is_refund=True, then=Value('Refund')),
                default=Value('Sale'),
                output_field=CharField()
            ),
            units_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('units'), 
                    output_field=CharField()
                ), output_field=CharField())),
                default=Cast('units', output_field=CharField())
            ),
            gross_total_amount_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('gross_total_amount'), 
                    output_field=CharField()
                ), output_field=CharField())),
                default=Cast('gross_total_amount', output_field=CharField())
            ),
            discount_amount_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('discount_amount'), 
                    output_field=CharField()), output_field=CharField())
                ),
                default=Cast('discount_amount', output_field=CharField())
            ),
            total_amount_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('total_amount'), 
                    output_field=CharField()), output_field=CharField())
                ),
                default=Cast('total_amount', output_field=CharField())
            ),
            cost_total_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(ExpressionWrapper(-F('cost_total'), 
                    output_field=CharField()), output_field=CharField())
                ),
                default=Cast('cost_total', output_field=CharField())
            ),
            profit_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(-profit, output_field=CharField())
                ),
                default=Cast(profit, output_field=CharField())
            ),
            multiplied_tax_amount_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(-multiplied_tax_amount, output_field=CharField())
                ),
                default=Cast(multiplied_tax_amount, output_field=CharField())
            ),
            net_sales_wo_vat_str=Case(
                When(
                    receipt__is_refund=True, 
                    then=Cast(-net_sales_wo_vat, output_field=CharField())
                ),
                default=Cast(net_sales_wo_vat, output_field=CharField())
            ),
            full_name=Concat('user__first_name', Value(' '), 'user__last_name', output_field=CharField()),
        ).order_by('-created_date').values_list(
            'created_datetime_str',
            'sync_datetime_str',
            'receipt__receipt_number',
            'receipt_type',  # Use the newly created field
            'product__name',
            'units_str',
            'gross_total_amount_str',
            'discount_amount_str',
            'total_amount_str',
            'cost_total_str',
            'profit_str',
            'multiplied_tax_amount_str',
            'net_sales_wo_vat_str',
            'store__name',
            'full_name',
        ) 

        receipt_list = [list(receipt) for receipt in queryset]
        data += receipt_list
        class Echo:
            def write(self, value): return value

        echo_buffer = Echo()
        csv_writer = csv.writer(echo_buffer)

        # By using a generator expression to write each row in the queryset
        # python calculates each row as needed, rather than all at once.
        # Note that the generator uses parentheses, instead of square
        # brackets – ( ) instead of [ ].
        rows = (csv_writer.writerow(row) for row in data)

        response = StreamingHttpResponse(rows, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users.csv"'
        return response

    def get(self, request, *args, **kwargs):

        if self.VIEW_TYPE == self.VIEW_TYPE_RECEIPT_CSV_PER_ITEM:
            return self.csv_per_item_response()
        elif self.VIEW_TYPE == self.VIEW_TYPE_RECEIPT_CSV:
            return self.csv_per_receipt_response()

        return self.list(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(ReceiptIndexView, self).get_queryset()
        
        current_user = self.request.user

        if (current_user.user_type == TOP_USER):
            queryset = queryset.filter(store__profile__user__email=current_user)
        else:
            queryset = queryset.filter(store__employeeprofile__user=current_user)

        queryset = queryset.order_by('-created_date') 

        return queryset
    
    def get_store_list(self, queryset):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = queryset.order_by('id')
        stores = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return stores
    
    def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)


            # Update the receipt classification
            self.receipt_classification['all_receipts'] = queryset.count()
            self.receipt_classification['refunds'] = queryset.filter(
                is_refund=True
            ).count()
            self.receipt_classification['sales'] = queryset.filter(
                is_refund=False
            ).count()

            self.request.data['receipts_count'] = self.receipt_classification

        return queryset
    
class ReceiptView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Receipt.objects.all().select_related(
        'user', 'store', 'customer', 'tax', 'discount'
    )
    serializer_class = ReceiptViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(ReceiptView, self).get_queryset()
        

        current_user = self.request.user

        if (current_user.user_type == TOP_USER):
            queryset = queryset.filter(
                store__profile__user__email=self.request.user, 
                reg_no=self.kwargs['reg_no']
            )
        else:
            stores = current_user.employeeprofile.stores.all().values_list('pk')

            queryset = queryset.filter(
                store__in=stores,
                reg_no=self.kwargs['reg_no']
            )

        return queryset