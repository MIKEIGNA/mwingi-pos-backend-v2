from decimal import Decimal
from pprint import pprint
import time
import pandas as pd
import numpy as np

from django.db.models.functions import Coalesce
from django.db.models import F, Sum, ExpressionWrapper, DecimalField,Value
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When
from django.db.models import F

from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from accounts.utils.user_type import TOP_USER
from api.utils.api_filter_helpers import FilterModelsList

from api.serializers import (
    ProductReportListSerializer,
    SaleSummarySerializer,
) 
from api.views.reports.report_mixins import ReportSaleSummaryMixin
from core.number_helpers import NumberHelpers

from core.queryset_helpers import QuerysetFilterHelpers
from core.time_utils.time_localizers import is_valid_iso_format

from products.models import Product
from profiles.models import EmployeeProfile, Profile
from sales.models import Receipt, ReceiptLine


class TpSaleSummaryView(generics.RetrieveUpdateAPIView, ReportSaleSummaryMixin):
    serializer_class = SaleSummarySerializer
    permission_classes = (permissions.IsAuthenticated,)

    # Custom fields
    date_after = None
    date_before = None
    store_reg_no = None

    is_owner = None 

    def verify_dates(self, date_list):
        """
        Returns True if the list is empty or has valid dates. Otherwise False
        is returned 
        """
        for date in date_list:
            if date:
                if not is_valid_iso_format(date):
                    return False

        return True

    def verify_reg_no(self, reg_nos):
        """
        Returns True if the reg_no is empty or is a valid integers. Otherwise False
        is returned 
        """
        if reg_nos:

            reg_no_list = reg_nos.split(',')

            for reg_no in reg_no_list:
   
                if reg_no.isdigit():
                    if int(reg_no) > 6000000000000:
                        return False
                else:
                    return False

        return True

    def get(self, request, *args, **kwargs): 

        self.is_owner = self.request.user.user_type == TOP_USER

        # Retrive and verify date values
        self.date_after = self.request.GET.get('date_after', '')
        self.date_before = self.request.GET.get('date_before', '')
        
        if not self.verify_dates([self.date_after, self.date_before]):
            return Response(
                {'date': ['Enter a valid date.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrive and verify store reg no values
        self.store_reg_no = self.request.GET.get('store_reg_no', '')
    
        if not self.verify_reg_no(self.store_reg_no):
            return Response(
                {'store_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super(TpSaleSummaryView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her profile 
        """
        if self.is_owner:
            queryset = queryset = Profile.objects.all()
        else:
            queryset = EmployeeProfile.objects.all()

        queryset = queryset.filter(user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = generics.get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj
    
    def get_receipt_queryset(self):

        if self.is_owner:
            return Receipt.objects.filter(
                store__profile=self.request.user.profile
            )

        else:
            employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            return Receipt.objects.filter(
                store__employeeprofile=employee_profile
            )
        
    def get_serializer_context(self):
        context = super(TpSaleSummaryView, self).get_serializer_context()

        queryset = self.get_receipt_queryset()

        # Measure first query time
        start_time = time.time()
        # Filter dates if they have been provided
        if self.store_reg_no:
            store_reg_nos = self.store_reg_no.split(',')
            queryset = queryset.filter(store__reg_no__in=store_reg_nos)
 
        # Filter dates if they have been provided
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name='created_date',
            date_after=self.date_after,
            date_before=self.date_before,
            local_timezone=self.request.user.get_user_timezone()
        ) 

        # Annonate by hour if date after and before have been provided and they
        # are the same
        single_day_query = self.date_after and self.date_after == self.date_before
        duration_desc = self.request.GET.get('duration', None)
     
        print('==========================================>>>')
        print("Duration ", duration_desc)


        # Get sales data
        # The following methods have been defined in ReportSaleSummaryMixin

        empty_total_sales_data = {
            'receipts_count': '0',
            'gross_sales': '0',
            'net_sales': '0',
            'discounts':'0',
            'profits': '0',
            'costs_sales': '0',
            'costs_refunds': '0',
            'refunds': '0',
            'taxes': '0',
            'net_sale_without_taxes': '0',
        }

        # Check if the user has permission to view profits
        has_profit_perm = self.request.user.has_perm_for_profits()

        if queryset.count():
            context['total_sales_data'] = self.get_total_sales_data(
                queryset=queryset, 
                has_profit_perm=has_profit_perm
            )
        else: 
            context['total_sales_data'] = empty_total_sales_data


        if queryset.count():
            context['sales_data'] = self.get_sales_data(
                queryset, 
                single_day_query,
                duration_desc,
                self.date_after,
                self.date_before,
                has_profit_perm
            )
        else:
            context['sales_data'] = []

        context['users'] = FilterModelsList.get_user_list(self.request.user)
        context['stores'] = FilterModelsList.get_store_list(self.request.user)

        return context

 
class TpSaleSummaryView2(generics.RetrieveUpdateAPIView, ReportSaleSummaryMixin):
    serializer_class = SaleSummarySerializer
    permission_classes = (permissions.IsAuthenticated,)

    # Custom fields
    date_after = None
    date_before = None
    store_reg_no = None
    user_reg_no = None

    is_owner = None

    def verify_dates(self, date_list):
        """
        Returns True if the list is empty or has valid dates. Otherwise False
        is returned 
        """
        for date in date_list:
            if date:
                if not is_valid_iso_format(date):
                    return False

        return True

    def verify_reg_no(self, reg_nos):
        """
        Returns True if the reg_no is empty or is a valid integers. Otherwise False
        is returned 
        """
        if reg_nos:
            reg_no_list = reg_nos.split(',')

            for reg_no in reg_no_list:
   
                if reg_no.isdigit():
                    if int(reg_no) > 6000000000000:
                        return False
                else:
                    return False

        return True

    def get(self, request, *args, **kwargs): 

        self.is_owner = self.request.user.user_type == TOP_USER

        # Retrive and verify date values
        self.date_after = self.request.GET.get('date_after', '')
        self.date_before = self.request.GET.get('date_before', '')
        
        if not self.verify_dates([self.date_after, self.date_before]):
            return Response(
                {'date': ['Enter a valid date.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrive and verify store reg no values
        self.store_reg_no = self.request.GET.get('store_reg_no', '')
    
        if not self.verify_reg_no(self.store_reg_no):
            return Response(
                {'store_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrive and verify user reg no values
        self.user_reg_no = self.request.GET.get('user_reg_no', '')

        if not self.verify_reg_no(self.user_reg_no):
            return Response(
                {'user_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return super(TpSaleSummaryView2, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her profile 
        """
        if self.is_owner:
            queryset = queryset = Profile.objects.all()
        else:
            queryset = EmployeeProfile.objects.all()

        queryset = queryset.filter(user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = generics.get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj
    
    def get_receipt_queryset(self):

        if self.is_owner:
            return Receipt.objects.filter(
                store__profile=self.request.user.profile
            )

        else:
            employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            return Receipt.objects.filter(
                store__employeeprofile=employee_profile
            )
        
    def get_serializer_context(self):
        context = super(TpSaleSummaryView2, self).get_serializer_context()

        queryset = self.get_receipt_queryset()

        # Measure first query time
        start_time = time.time()
        # Filter dates if they have been provided
        if self.store_reg_no:
            store_reg_nos = self.store_reg_no.split(',')
            queryset = queryset.filter(store_reg_no__in=store_reg_nos)

    
        end_time = time.time()
        print(f"First query time {end_time - start_time}")


        print("==========================================================")

        # Measure first query time
        start_time = time.time()
        # Make sure a user can only view his/her models or that of his/her
        # employees
        # if self.user_reg_no:
        #     user_reg_nos = self.user_reg_no.split(',')
        #     queryset = queryset.filter(user_reg_no__in=user_reg_nos)

        end_time = time.time()
        print(f"Second query time {end_time - start_time}")


        print(f'Date after {self.date_after}')
        print(f'Date before {self.date_before}')
            
        # Measure first query time
        start_time = time.time()

        # Filter dates if they have been provided
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name='created_date',
            date_after=self.date_after,
            date_before=self.date_before,
            local_timezone=self.request.user.get_user_timezone()
        ) 

        end_time = time.time()
        print(f"Third query time {end_time - start_time}")

        # Measure first query time
        start_time = time.time()

        sales = queryset.filter(is_refund=False).order_by('-created_date')
        refunds = queryset.filter(is_refund=True)

        end_time = time.time()
        print(f"Fourth query time {end_time - start_time}")
        
        # print(f"Receipts count {queryset.count()}")
        # print(f"Receipts sales {sales.count()}")
        # print(f"Receipts refunds {refunds.count()}") 

        # import csv

        # with open('sales_summary.csv', 'w', newline='') as file:
        #     writer = csv.writer(file)

        #     writer.writerow(["Receipt number", "Total amount",])

        #     for sale in sales:
        # #     print(f'{sale.receipt_number}, {sale.total_amount}')
        #         writer.writerow([sale.receipt_number, sale.total_amount])

        # Measure first query time
        start_time = time.time()

        # Annonate by hour if date after and before have been provided and they
        # are the same
        single_day_query = self.date_after and self.date_after == self.date_before

        has_profit_perm = self.request.user.has_perm_for_profits()

        # Get sales data
        # The following methods have been defined in ReportSaleSummaryMixin
        context['total_sales_data'] = self.get_total_sales_data(
            queryset=queryset,
            has_profit_perm=has_profit_perm
        )

        end_time = time.time()
        print(f"Fifth query time {end_time - start_time}")

        # Measure first query time
        start_time = time.time()
        context['sales_data'] = self.get_sales_data(
            queryset, 
            single_day_query,
            '',
            self.date_after,
            self.date_before,
            has_profit_perm
        ) 

        end_time = time.time()
        print(f"Sixth query time {end_time - start_time}")

        # Measure first query time
        start_time = time.time()

        context['users'] = FilterModelsList.get_user_list(self.request.user)

        end_time = time.time()
        print(f"Seventh query time {end_time - start_time}")

        # Measure first query time
        start_time = time.time()

        context['stores'] = FilterModelsList.get_store_list(self.request.user)

        end_time = time.time()
        print(f"Eighth query time {end_time - start_time}")

        return context


class SalesReportView(APIView):
    PRODUCT_REPORT = 0
    CATEGORY_REPORT = 1
    EMPLOYEE_REPORT = 2
    TAX_REPORT = 3
    STORE_REPORT = 4
    
    queryset = Product.objects.all()
    serializer_class = ProductReportListSerializer
    permission_classes = (permissions.IsAuthenticated, )

    # Custom fields
    report_type = None

    def verify_reg_no(self, reg_nos):
        """
        Returns True if the reg_no is empty or is a valid integers. Otherwise False
        is returned 
        """
        if reg_nos:

            reg_no_list = reg_nos.split(',')

            for reg_no in reg_no_list:
   
                if reg_no.isdigit():
                    if int(reg_no) > 6000000000000:
                        return False
                else:
                    return False

        return True

    def get_sales_data(self, date_after, date_before, store_reg_no, user_reg_no):

        lookup_name =''
        if self.report_type == self.PRODUCT_REPORT:
            lookup_name = 'product__name'
        
        elif self.report_type == self.CATEGORY_REPORT:
            lookup_name = 'product__category__name'

        elif self.report_type == self.EMPLOYEE_REPORT:
            lookup_name = 'receipt__user__full_name'
        
        elif self.report_type == self.TAX_REPORT:
            lookup_name = 'tax__name'
        
        elif self.report_type == self.STORE_REPORT:
            lookup_name = 'store__name'
 
        current_user = self.request.user

        queryset = None

        if (current_user.user_type == TOP_USER):
            queryset = ReceiptLine.objects.filter(receipt__store__profile__user__email=current_user)
        else:
            queryset = ReceiptLine.objects.filter(receipt__store__employeeprofile__user=current_user)

        if store_reg_no:
            queryset = queryset.filter(
                receipt__store__reg_no__in=store_reg_no.split(',')
            )

        # if user_reg_no:
        #     queryset = queryset.filter(
        #         receipt__user__reg_no__in=user_reg_no.split(',')
        #     )

        queryset = queryset.filter().values( 
            lookup_name,
            'units',
            'price',
            'cost',
            'discount_amount',
            'receipt__refund_for_receipt_number',
            'receipt__receipt_number',
            'tax__rate'
        )
        
        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'receipt__created_date', 
            date_after, 
            date_before,
            self.request.user.get_user_timezone()
        )

        if not queryset: return []

        pd.set_option('display.max_rows', 1000)  # Display up to 10 rows
        pd.set_option('display.max_columns', 1000)  # Display up to 5 columns

        df = pd.DataFrame(queryset)

        # Rename columns appropriately
        df.rename(
            columns={
                lookup_name: 'name',
                'units': 'items_sold',
                'receipt__refund_for_receipt_number': 'receipt_refunded'
            }, inplace=True
        )

        # Calculate net sales and taxes
        df['net_sales'] = (df['price'] * df['items_sold']) - df['discount_amount']
        df['taxes'] = df['net_sales'] - (df['net_sales'] / (df['tax__rate'] + 100) * 100)


        # Measure sixth query time

        start_time = time.time()

        # Convert the following columns to Decimal
        list_to_quantize = ['price', 'net_sales', 'discount_amount', 'cost', 'taxes']
        for column in list_to_quantize:
            df[column] = df[column].apply(lambda x: Decimal(x))
            df[column] = df[column].apply(lambda x: x.quantize(Decimal('0.00')))
       
        df['refundend_amount'] = 0
        df['refunded_units'] = 0
        df['refunded_discount'] = 0
        df['net_sales_without_tax'] = 0

        # Do the following for rows that have 'receipt_refunded' column with an
        # empty string
        df.loc[df['receipt_refunded'] != '', 'refundend_amount'] = df['net_sales']
        df.loc[df['receipt_refunded'] != '', 'refunded_units'] = df['items_sold']
        df.loc[df['receipt_refunded'] != '', 'refunded_discount'] = df['discount_amount']

        df.loc[df['receipt_refunded'] != '', 'cost'] = df['cost'] * -1
        df.loc[df['receipt_refunded'] != '', 'net_sales'] = df['net_sales'] * -1
        df.loc[df['receipt_refunded'] != '', 'taxes'] = df['taxes'] * -1
        df.loc[df['receipt_refunded'] != '', 'discount_amount'] = df['discount_amount'] * -1

        # Sum up everything
        result_df = df.groupby('name', as_index=False).agg(
            {
                'price': 'sum',
                'net_sales': 'sum', 
                'items_sold': 'sum',
                'cost': 'sum',
                'refunded_units': 'sum',
                'refundend_amount': 'sum',
                'discount_amount': 'sum',
                'refunded_discount': 'sum',
                'taxes': 'sum',
                'net_sales_without_tax': 'sum',
            }
        )

        # Calculate the 'profit' column as the difference between 'net sales' and 'cost'
        result_df['profit'] = result_df['net_sales'] - result_df['cost']
        result_df['items_sold'] = result_df['items_sold'] - result_df['refunded_units']
        result_df['net_sales_without_tax'] = result_df['net_sales'] - result_df['taxes']
        result_df['refundend_amount'] = result_df['refundend_amount'] + result_df['refunded_discount']
        result_df['gross_sales'] = result_df['net_sales'] + result_df['refundend_amount'] + result_df['discount_amount']
        result_df['margin'] = np.where(result_df['net_sales'] == 0, 0, (result_df['profit'] / result_df['net_sales']) * 100)

        result_df['margin'] = result_df['margin'].apply(lambda x: x.quantize(Decimal('0.00')))
    
        # Convert numbers to strings
        result_df['profit'] = result_df['profit'].astype(str)
        result_df['gross_sales'] = result_df['gross_sales'].astype(str)
        result_df['net_sales'] = result_df['net_sales'].astype(str)
        result_df['cost'] = result_df['cost'].astype(str)
        result_df['items_sold'] = result_df['items_sold'].astype(str)
        result_df['refunded_units'] = result_df['refunded_units'].astype(str)
        result_df['refundend_amount'] = result_df['refundend_amount'].astype(str)
        result_df['discount_amount'] = result_df['discount_amount'].astype(str)
        result_df['taxes'] = result_df['taxes'].astype(str)
        result_df['net_sales_without_tax'] = result_df['net_sales_without_tax'].astype(str)
        result_df['margin'] = result_df['margin'].astype(str)

        # Sort the DataFrame by 'product name' in ascending order
        df_sorted = result_df.sort_values(by='name')

        # Convert the DataFrame to a list of dictionaries
        result_list = df_sorted.to_dict('records')

        sales_data = []
        for result in result_list:
            sales_data.append(
                {
                    'report_data': {
                        'is_variant': False,
                        'product_data': {
                            'name': result['name'],
                            'gross_sales': result['gross_sales'],
                            'net_sales': result['net_sales'],
                            'items_sold': result['items_sold'],
                            'taxes': result['taxes'],
                            'refunded_units': result['refunded_units'],
                            'refundend_amount': result['refundend_amount'],
                            'discount_amount': result['discount_amount'],
                            'cost': result['cost'],
                            'profit': result['profit'],
                            'net_sales_without_tax': result['net_sales_without_tax'],
                            'margin': result['margin'], 
                        }
                    }
                }
            )

        return sales_data
    
    def get(self, request, *args, **kwargs):

        date_after=self.request.GET.get('date_after', '')
        date_before=self.request.GET.get('date_before', '')
        store_reg_no=self.request.GET.get('store_reg_no', '')
        user_reg_no=self.request.GET.get('user_reg_no', '')
        
        if not self.verify_reg_no(store_reg_no):
            return Response(
                {'store_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            ) 
        
        if not self.verify_reg_no(user_reg_no):
            return Response(
                {'user_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Measure second query time
        start_time = time.time()
        sales_data2 =  self.get_sales_data(
            date_after=date_after, 
            date_before=date_before,
            store_reg_no=store_reg_no,
            user_reg_no=user_reg_no
        )

        end_time = time.time()
        print(f"#### Query time {end_time - start_time}")

        data = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': sales_data2,
            'users': FilterModelsList.get_user_list(self.request.user),
            'stores': FilterModelsList.get_store_list(self.request.user),
        } 
        
        return Response(data)
    

class SalesReportView2(APIView):
    PRODUCT_REPORT = 0
    CATEGORY_REPORT = 1
    EMPLOYEE_REPORT = 2
    TAX_REPORT = 3
    STORE_REPORT = 4
    
    queryset = Product.objects.all()
    serializer_class = ProductReportListSerializer
    permission_classes = (permissions.IsAuthenticated, )

    # Custom fields
    report_type = None

    def verify_reg_no(self, reg_nos):
        """
        Returns True if the reg_no is empty or is a valid integers. Otherwise False
        is returned 
        """
        if reg_nos:
            reg_no_list = reg_nos.split(',')
            for reg_no in reg_no_list:
                if reg_no.isdigit():
                    if int(reg_no) > 6000000000000:
                        return False
                else:
                    return False

        return True

    def get_sales_data(self, date_after, date_before, store_reg_no):

        lookup_name =''
        if self.report_type == self.PRODUCT_REPORT:
            lookup_name = 'product__name'
        
        elif self.report_type == self.CATEGORY_REPORT:
            lookup_name = 'product__category__name'

        elif self.report_type == self.EMPLOYEE_REPORT:
            lookup_name = 'receipt__user__full_name'
        
        elif self.report_type == self.TAX_REPORT:
            lookup_name = 'tax__name'
        
        elif self.report_type == self.STORE_REPORT:
            lookup_name = 'store__name'
 
        current_user = self.request.user

        queryset = None

        if (current_user.user_type == TOP_USER):
            queryset = ReceiptLine.objects.filter(receipt__store__profile__user__email=current_user)
        else:
            queryset = ReceiptLine.objects.filter(receipt__store__employeeprofile__user=current_user)

        if store_reg_no:
            queryset = queryset.filter(
                receipt__store__reg_no__in=store_reg_no.split(',')
            )

        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'created_date', 
            date_after, 
            date_before,
            self.request.user.get_user_timezone()
        )

        queryset = queryset.annotate(name=F(lookup_name))

        def get_net_sales_sub():
            return ((F('price') * F('units')) - F('discount_amount'))
        
        query_data = queryset.values(
            'name',
        ).annotate(
            total_sold_units =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=False, then='units'),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            total_refunded_units =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then='units'),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            total_sold_costs =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=False, then='cost'),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            total_refunded_costs =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then='cost'),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            total_sales_discount_amount =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=False, then='discount_amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            total_refunded_discount_amount =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then='discount_amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ), 

            net_sales = Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=False, then=F('price') * F('units') - F('discount_amount')),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            net_taxes =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=False, then=get_net_sales_sub()- (get_net_sales_sub() / (F('tax_rate') + 100) * 100)),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            refunded_taxes =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then=get_net_sales_sub()- (get_net_sales_sub() / (F('tax_rate') + 100) * 100)),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ),
            refunded_net_sales =Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then=F('price') * F('units') - F('discount_amount')),
                        default=0,
                        output_field=DecimalField()
                    )
                ), Decimal(0.00)
            ), 
        )
        
        # Check if the user has permission to view profits
        has_profit_perm = self.request.user.has_perm('accounts.can_view_profits')

        data = []
        for item in query_data:
            refunded_net_sales = item['refunded_net_sales']
            net_sales = item['net_sales'] - refunded_net_sales
            taxes = item['net_taxes'] - item['refunded_taxes']
            net_sales_without_tax = net_sales - taxes
            
            total_sold_costs = item['total_sold_costs']
            total_refunded_costs = item['total_refunded_costs']
            total_sales_discount_amount = item['total_sales_discount_amount']
            total_refunded_discount_amount = item['total_refunded_discount_amount']

            total_discount = total_sales_discount_amount - total_refunded_discount_amount

            total_costs = total_sold_costs - total_refunded_costs

            refunded_amount = refunded_net_sales + total_refunded_discount_amount
            
            profit = net_sales - total_costs

            # Calculate margin
            margin = 0
            try:
                margin = (profit / net_sales) * 100
            except:
                margin = 0

            gross_sales = net_sales + refunded_amount + total_discount


            '''
            has_profit_perm=has_profit_perm
            '''

            row_data = {
                'report_data': {
                    'is_variant': False,
                    'product_data': {
                        'name': item['name'],
                        'gross_sales': NumberHelpers.normal_round(gross_sales, 2),
                        'net_sales': NumberHelpers.normal_round(net_sales, 2),
                        'items_sold': NumberHelpers.normal_round(item['total_sold_units'], 2),
                        'taxes': NumberHelpers.normal_round(taxes, 2),
                        'taxes_net': NumberHelpers.normal_round(item['net_taxes'], 2),
                        'taxes_refunded': NumberHelpers.normal_round(item['refunded_taxes'], 2), 
                        'taxes_total_refunded_discount_amount': NumberHelpers.normal_round(item['total_refunded_discount_amount'], 2),
                        'refunded_units': NumberHelpers.normal_round(item['total_refunded_units'], 2),
                        'refundend_amount': NumberHelpers.normal_round(refunded_amount, 2),
                        'discount_amount': NumberHelpers.normal_round(total_discount, 2),
                        'cost': NumberHelpers.normal_round(total_costs, 2),
                        'net_sales_without_tax': NumberHelpers.normal_round(net_sales_without_tax, 2),
                    }
                }
            }

            if has_profit_perm:
                row_data['report_data']['product_data']['profit'] = NumberHelpers.normal_round(profit, 2)
                row_data['report_data']['product_data']['margin'] = NumberHelpers.normal_round(margin,2)

            data.append(row_data)
                
        return data

    def get(self, request, *args, **kwargs):

        date_after=self.request.GET.get('date_after', '')
        date_before=self.request.GET.get('date_before', '')
        store_reg_no=self.request.GET.get('store_reg_no', '')
        
        if not self.verify_reg_no(store_reg_no):
            return Response(
                {'store_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            ) 
        
        # Measure second query time
        start_time = time.time()
        sales_data2 =  self.get_sales_data(
            date_after=date_after, 
            date_before=date_before,
            store_reg_no=store_reg_no
        ) 

        end_time = time.time()
        print(f"#### Second query time {end_time - start_time}")

        data = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': sales_data2,
            'users': FilterModelsList.get_user_list(self.request.user),
            'stores': FilterModelsList.get_store_list(self.request.user),
        } 
        
        return Response(data)