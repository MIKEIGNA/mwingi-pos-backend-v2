# import pandas as pd

import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django.conf import settings
import zoneinfo
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Case, When
from django.db.models.fields import DecimalField
from django.db.models.functions.datetime import ( 
    TruncDay, 
    TruncHour, 
    TruncWeek, 
    TruncMonth
)
from django.db.models import OuterRef
from django.db.models.functions import Coalesce
from core.number_helpers import NumberHelpers

from core.time_utils.time_localizers import utc_to_local_datetime
from sales.models import ReceiptLine


class ReportSaleSummaryMixin:

    def receiptline_cost_subquery_for_cost(self):
        """
        Two things to know about subquery

        1. It can't be evaluated before it is used
        2. It can only return a single record with a single column

        So, you can't call aggregate on the subquery, because this evaluates the 
        subquery immediately. Instead you have to annotate the value. You also 
        have to group by the outer ref value, otherwise you'll just annotate each 
        Transaction independently.

        The first .values causes the correct group by. The second .values causes 
        selecting the one value that you want.
        """

        return ReceiptLine.objects.filter(
            receipt__is_refund=False,
            receipt=OuterRef('pk')
        ).values(
            'receipt__pk'
        ).annotate(
            total_cost=Sum('cost_total')
        ).values(
            'total_cost'
        )

    def receiptline_cost_subquery_for_refund(self):
        """
        Two things to know about subquery

        1. It can't be evaluated before it is used
        2. It can only return a single record with a single column

        So, you can't call aggregate on the subquery, because this evaluates the 
        subquery immediately. Instead you have to annotate the value. You also 
        have to group by the outer ref value, otherwise you'll just annotate each 
        Transaction independently.

        The first .values causes the correct group by. The second .values causes 
        selecting the one value that you want.
        """

        return ReceiptLine.objects.filter(
            receipt__is_refund=True,
            receipt=OuterRef('pk')
        ).values(
            'receipt__pk'
        ).annotate(
            total_cost=Sum('cost_total')
        ).values(
            'total_cost'
        )
    
    def get_total_sales_data(self, queryset, has_profit_perm):
        """
        Returns a dict with aggregate of receipt data. 

        Args: 
            queryset: Receipt model queryset

        Example of data returned

        {
            'gross_sales': '144300.00', 
            'net_sales': '142237.00', 
            'discounts': '1804.00', 
            'profits': '67237.00', 
            'refunds': '46500'
        }
        """
        def subtotal_amount_query():
            return Sum(
                Case(
                    When(is_refund=False, then='subtotal_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ) 
        
        receipt_count = queryset.count()
       
        queryset_agg = queryset.aggregate(
            gross_sales=subtotal_amount_query(),
            total_sale_amount=Sum(
                Case(
                    When(is_refund=False, then='total_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_refund_amount=Sum(
                Case(
                    When(is_refund=True, then='total_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_discount_amount=Sum(
                Case(
                    When(is_refund=False, then='discount_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_discount_refund_amount=Sum(
                Case(
                    When(is_refund=True, then='discount_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_tax_amount=Sum(
                Case(
                    When(is_refund=False, then='tax_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_tax_refund_amount=Sum(
                Case(
                    When(is_refund=True, then='tax_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_receiptline_sale_cost=Coalesce(
                Sum(self.receiptline_cost_subquery_for_cost()), 
                Decimal(0.00)
            ),
            total_receiptline_refund_cost=Coalesce(
                Sum(self.receiptline_cost_subquery_for_refund()), 
                Decimal(0.00)
            ), 
        )

        total_sale_amount = queryset_agg['total_sale_amount']
        total_refund_amount = queryset_agg['total_refund_amount']
        total_discount_amount = queryset_agg['total_discount_amount']
        total_discount_refund_amount = queryset_agg['total_discount_refund_amount']
        total_receiptline_sale_cost = queryset_agg['total_receiptline_sale_cost']
        total_receiptline_refund_cost = queryset_agg['total_receiptline_refund_cost']
        total_tax_amount = queryset_agg['total_tax_amount']
        total_tax_refund_amount = queryset_agg['total_tax_refund_amount']
        net_sales = total_sale_amount - total_refund_amount

        queryset_agg['net_sales'] = net_sales
        queryset_agg['discounts'] = total_discount_amount - total_discount_refund_amount
        queryset_agg['profits'] = total_sale_amount - total_refund_amount - \
            (total_receiptline_sale_cost - total_receiptline_refund_cost)
        queryset_agg['costs_sales'] = total_receiptline_sale_cost
        queryset_agg['costs_refunds'] = total_receiptline_refund_cost
        queryset_agg['refunds'] = total_refund_amount + total_discount_refund_amount
        queryset_agg['taxes'] = total_tax_amount - total_tax_refund_amount
        queryset_agg['net_sale_without_taxes'] = net_sales - total_tax_amount + total_tax_refund_amount

        new_queryset = {
            'receipts_count': receipt_count,
            'gross_sales': queryset_agg['gross_sales'],
            'net_sales': queryset_agg['net_sales'],
            'discounts': queryset_agg['discounts'],
            'costs_sales': queryset_agg['costs_sales'],
            'costs_refunds': queryset_agg['costs_refunds'],
            'refunds': queryset_agg['refunds'],
            'taxes': queryset_agg['taxes'],
            'net_sale_without_taxes': queryset_agg['net_sale_without_taxes'],
        }

        if has_profit_perm:
            new_queryset['profits'] = queryset_agg['profits']

        # Turn decimal values into strings
        return {k: str(round(v, 2)) if v else '0.00' for k, v in new_queryset.items()}

    def fill_in_lables_with_empty_values(self, lables):
        """
        From the provided lables, We create a list of sales data with all 
        fields having 0 as a value
        """
        return [
            {
                'date': lable,
                'count': '0',
                'gross_sales': '0.00',
                'net_sales': '0.00',
                'discounts': '0.00',
                'taxes': '0.00',
                'costs': '0.00',
                'profits': '0.00',
                'margin': '0',
                'refunds': '0.00'
            }
            for lable in lables
        ]

    def insert_missing_sales_data(self, sales_data, lables):
        """
        Updates blank data with the provided salses data
        """
        blank_data = self.fill_in_lables_with_empty_values(lables)

        for data in sales_data:
            index = lables.index(data['date'])
            blank_data[index] = data

        return blank_data
    

    def insert_missing_sales_data_for_named_labels(self, sales_data, lables, date_labels_desc):
        """
        Updates blank data with the provided salses data
        """
        blank_data = self.fill_in_lables_with_empty_values(lables)

        for data in sales_data:
            index = lables.index(data['date'])
            data['date'] = date_labels_desc[data['date']]
            blank_data[index] = data

        return blank_data
   
    def fill_single_day_data(self, sales_data):
        """
        Returns sales data from all the hours in a day
        """

        time_lables = [
            '12:00:AM', '01:00:AM', '02:00:AM', '03:00:AM', '04:00:AM', '05:00:AM',
            '06:00:AM', '07:00:AM', '08:00:AM', '09:00:AM', '10:00:AM', '11:00:AM',
            '12:00:PM', '01:00:PM', '02:00:PM', '03:00:PM', '04:00:PM', '05:00:PM',
            '06:00:PM', '07:00:PM', '08:00:PM', '09:00:PM', '10:00:PM', '11:00:PM'
        ]

        return self.insert_missing_sales_data(sales_data, time_lables)

    def fill_days_data(self, sales_data, date_after, date_before):
        """
        Returns sales data from all the dates between date_after and date_before
        """
        date_after = datetime.date.fromisoformat(date_after)
        date_before = datetime.date.fromisoformat(date_before)

        diff = (date_before - date_after).days

        # Generate date lables inbetween the provided dates
        date_lables = []
        for i in range(diff+1):
            date = date_after + relativedelta(days=i)
            date_lables.append(date.strftime("%b, %d, %Y"))

        return self.insert_missing_sales_data(sales_data, date_lables)
    
    def get_weeks(self,start_date, end_date):
        """
        This function iterates through weeks starting on Monday
        and returns a list of week tuples (start_date, end_date) covering
        the provided date range (inclusive).
        """
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

        current_date = start_date
        while current_date <= end_date:
            # Get the start of the current week (Monday)
            week_start = current_date - datetime.timedelta(days = current_date.weekday())

            # Get the end of the current week (Sunday)
            days_in_week = 6
            week_end = week_start + datetime.timedelta(days=days_in_week)

            # Check if the end of the week goes past the end_date
            if week_end > end_date:
                week_end = end_date

            yield week_start, week_end

            # Move to the next week's Monday
            current_date = week_end + datetime.timedelta(days=1)

    def fill_week_data(self, sales_data, start_date, end_date):

        def convert_date_to_string(date):
            return date.strftime("%b, %d, %Y")

        date_labels = []
        date_labels_desc = {}
        for week_start, week_end in self.get_weeks(start_date, end_date):
            start_date = convert_date_to_string(week_start)
            end_date = convert_date_to_string(week_end)
            date_labels.append(start_date)
            date_labels_desc[start_date] = f'{start_date} - {end_date}'

        return self.insert_missing_sales_data_for_named_labels(sales_data, date_labels, date_labels_desc)
    
    def get_months(self, start_date, end_date):

        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
     
        month_names = {}
        month_first_days = []

        # Initialize the current month with the start date
        current_month = datetime.datetime(start_date.year, start_date.month, 1)

        # Iterate through each month from start_date to end_date
        while current_month <= end_date :
            # Get the name of the current month
            month_name = current_month.strftime('%B')  # %B gives the full month name
            month_first_date = current_month.strftime('%b, %d, %Y')

            month_first_days.append(month_first_date)
            month_names[month_first_date] = month_name
                
            # Move to the next month
            current_month = current_month.replace(month=current_month.month + 1, day=1)

        return month_names, month_first_days
    
    def fill_month_data(self, sales_data, start_date, end_date):
    
        month_names, month_first_days = self.get_months(start_date, end_date)

        return self.insert_missing_sales_data_for_named_labels(
            sales_data, 
            month_first_days, 
            month_names
        )

    def round_if_decimal(self, value):
        return round(value, 2) if type(value) == Decimal else value

    def get_sales_data(
            self, 
            queryset, 
            single_day_query, 
            duration_desc,
            date_after, 
            date_before,
            has_profit_perm):
        """
        Returns list of receipts with each receipt aggregated. 

        Args: 
            queryset: Receipt model queryset
            single_day_query: A flag indicatiing if this query is for a single
            day or multiple days
            date_after:
            date_before:

        Example of data returned

        [
            {
                'date': self.today.strftime('%b, %d, %Y'), 
                'count': '2', 
                'gross_sales': '63600.00', 
                'net_sales': '62788.00', 
                'discounts': '702.00', 
                'taxes': '110.00', 
                'costs': '33000.00', 
                'profits': '29788.00', 
                'margin': '52', 
                'refunds': '0.00'
            }, 
        ]
        """

        is_days = duration_desc == 'days'
        is_weeks = duration_desc == 'weeks'
        is_months = duration_desc == 'months'

        local_timezone = zoneinfo.ZoneInfo(settings.LOCATION_TIMEZONE)

        if single_day_query:
            queryset = queryset.annotate(
                receipt_date=TruncHour(
                    'created_date', 
                    tzinfo=local_timezone 
                )
            )

        elif is_days:
            queryset = queryset.annotate(
                receipt_date=TruncDay(
                    'created_date', 
                    tzinfo=local_timezone    
                )
            )

        elif is_weeks:
            queryset = queryset.annotate(
                receipt_date=TruncWeek(
                    'created_date', 
                    tzinfo=local_timezone    
                )
            )

        else:
            queryset = queryset.annotate(
                receipt_date=TruncMonth(
                    'created_date', 
                    tzinfo=local_timezone    
                )
            )

        def subtotal_amount_query():
            return Sum(
                Case(
                    When(is_refund=False, then='subtotal_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ) 
            
        queryset1 = queryset.values('receipt_date').annotate(
            count=Count('id'),
            gross_sales=subtotal_amount_query(),
            total_sale_amount=Sum(
                Case(
                    When(is_refund=False, then='total_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_refund_amount=Sum(
                Case(
                    When(is_refund=True, then='total_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_discount_amount=Sum(
                Case(
                    When(is_refund=False, then='discount_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_discount_refund_amount=Sum(
                Case(
                    When(is_refund=True, then='discount_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_tax_amount=Sum(
                Case(
                    When(is_refund=False, then='tax_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_tax_refund_amount=Sum(
                Case(
                    When(is_refund=True, then='tax_amount'),
                    default=0,
                    output_field=DecimalField()
                )
            ),
            total_receiptline_sale_cost=Coalesce(
                Sum(self.receiptline_cost_subquery_for_cost()), 
                Decimal(0.00)
            ),
            total_receiptline_refund_cost=Coalesce(
                Sum(self.receiptline_cost_subquery_for_refund()), 
                Decimal(0.00)
            ), 
        )

        user_timezone = self.request.user.get_user_timezone()

        def format_date(single_day_query, value):

            local_date = utc_to_local_datetime(value, user_timezone)

            if single_day_query:
                return local_date.strftime("%I:%M:%p")
            else:
                return local_date.strftime("%b, %d, %Y")
            
        sales_data = []
        for q in queryset1:

            total_discount_sales_amount = q['total_discount_amount']
            total_discount_refund_amount = q['total_discount_refund_amount']
            total_discount = total_discount_sales_amount - total_discount_refund_amount
            costs = q['total_receiptline_sale_cost'] if has_profit_perm else '0.00'
            net_sales = q['total_sale_amount'] - q['total_refund_amount']
            refunds = q['total_refund_amount'] + total_discount_refund_amount
            total_tax_amount = q['total_tax_amount']
            total_tax_refund_amount = q['total_tax_refund_amount']
            total_tax = total_tax_amount - total_tax_refund_amount

            sales_data.append(
                {
                    'date': format_date(single_day_query, q['receipt_date']),
                    'costs': str(NumberHelpers.normal_round(costs)) if has_profit_perm else '0.00',
                    'count': str(q['count']),
                    'discounts': str(NumberHelpers.normal_round(total_discount)),
                    'gross_sales': str(NumberHelpers.normal_round(q['gross_sales'])),
                    'margin': str(NumberHelpers.normal_round((costs * 100) / net_sales)) if has_profit_perm else '0.00',
                    'net_sales': str(NumberHelpers.normal_round(net_sales)),
                    'profits': str(NumberHelpers.normal_round(net_sales - costs)) if has_profit_perm else '0.00',
                    'refunds': str(NumberHelpers.normal_round(refunds)),
                    'taxes': str(NumberHelpers.normal_round(total_tax)),
                }
            )

        # Fill in data
        if single_day_query:
            return self.fill_single_day_data(sales_data)
        else:

            if date_after and date_before:

                if is_weeks:
                    return self.fill_week_data(sales_data, date_after, date_before) 
                elif is_months:
                    return self.fill_month_data(sales_data, date_after, date_before)
                else:
                    return self.fill_days_data(sales_data, date_after, date_before)
                
            else:
                return sales_data
