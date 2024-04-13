from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Case, When

from rest_framework import status
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from api.serializers.reports.report_serializers import StorePaymentMethodReportListSerializer
from api.utils.api_filter_helpers import FilterModelsList

from api.utils.api_filters import (
    CategoryReportFilter, 
    DiscountReportFilter, 
    ModifierReportFilter, 
    ProductReportFilter,
    StorePaymentMethodReportFilter, 
    TaxReportFilter, 
    UserReportFilter
)
from api.utils.api_web_pagination import ReportResultsSetPagination, ReportStorePaymentMethodResultsSetPagination
from api.utils.permission_helpers.api_view_permissions import IsEmployeeUserPermission
from api.serializers import (
    UserReportListSerializer,
    ProductReportListSerializer,
    SaleSummarySerializer,
    CategoryReportListSerializer,
    DiscountReportListSerializer,
    TaxReportListSerializer,
    ModifierReportListSerializer
)
from api.views.reports.report_mixins import ReportSaleSummaryMixin

from core.queryset_helpers import QuerysetFilterHelpers
from core.time_utils.time_localizers import is_valid_iso_format

from products.models import Modifier, Product
from profiles.models import EmployeeProfile
from sales.models import Receipt
from stores.models import Category, Discount, StorePaymentMethod, Tax

class EpSaleSummaryView(generics.RetrieveUpdateAPIView, ReportSaleSummaryMixin):
    queryset = EmployeeProfile.objects.all()
    serializer_class = SaleSummarySerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)

    # Custom fields
    date_after = None
    date_before = None
    store_reg_no = None
    user_reg_no = None

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

        # Retrive and verify date values
        self.date_after = self.request.GET.get('date_after', '')
        self.date_before = self.request.GET.get('date_before', '')
        
        if not self.verify_dates([self.date_after, self.date_before]):
            print("Error 1")
            return Response(
                {'date': ['Enter a valid date.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retrive and verify store reg no values
        self.store_reg_no = self.request.GET.get('store_reg_no', '')
    
        if not self.verify_reg_no(self.store_reg_no):
            print("Error 2")
            return Response(
                {'store_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrive and verify user reg no values
        self.user_reg_no = self.request.GET.get('user_reg_no', '')

        if not self.verify_reg_no(self.user_reg_no):
            print("Error 3")
            return Response(
                {'user_reg_no': ['Enter a number.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return super(EpSaleSummaryView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her profile 
        """
        queryset = super(EpSaleSummaryView, self).get_queryset()
        queryset = queryset.filter(user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = generics.get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj

    def get_serializer_context(self):
        context = super(EpSaleSummaryView, self).get_serializer_context()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)

        queryset = Receipt.objects.filter(
            store__employeeprofile=employee_profile
        )

        # Filter dates if they have been provided
        if self.store_reg_no:
            queryset = queryset.filter(store__reg_no=self.store_reg_no)

        # Make sure a user can only view his/her models, those of employees on
        # the same store or those for the top user in the same store
        if self.user_reg_no:
            queryset = queryset.filter(user__reg_no=self.user_reg_no)

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


        # Get sales data
        # The following methods have been defined in ReportSaleSummaryMixin
        context['total_sales_data'] = self.get_total_sales_data(queryset)
        context['sales_data'] = self.get_sales_data(
            queryset, 
            single_day_query,
            self.date_after,
            self.date_before
        )
        context['users'] = FilterModelsList.get_user_list(self.request.user)
        context['stores'] = FilterModelsList.get_store_list(self.request.user)
       
        return context

class EpUserReportIndexView(generics.ListCreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = UserReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportResultsSetPagination
    filterset_class=UserReportFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpUserReportIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)

        queryset = queryset.filter(
            Q(employeeprofile__stores__employeeprofile=employee_profile) | 
            Q(
                reg_no=self.request.user.employeeprofile.profile.reg_no,
                profile__store__employeeprofile=employee_profile
             )
        ).annotate(
            receipt_count=Count('receipt', distinct=True),
            total_amount=Sum('receipt__total_amount')
        )
        queryset = queryset.exclude(receipt_count=0)
        queryset = queryset.order_by('-total_amount', '-id').distinct()

        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', '')
        )


class EpCategoryReportIndexView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportResultsSetPagination
    filterset_class=CategoryReportFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpCategoryReportIndexView, self).get_queryset()

        employee_profile = self.request.user.employeeprofile

        queryset = queryset.filter(
            profile=employee_profile.profile,
            product__stores__employeeprofile=employee_profile
            )
        queryset = queryset.annotate(
            receiptline_count=Count('product__receiptline', distinct=True),
            total=Sum('product__receiptline__price')
        )
        queryset = queryset.exclude(receiptline_count=0)
        queryset = queryset.order_by('-total', '-id').distinct()
        
        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', ''),
            user_reg_no=self.request.GET.get('user_reg_no', ''),
        )

class EpDiscountReportIndexView(generics.ListCreateAPIView):
    queryset = Discount.objects.all()
    serializer_class = DiscountReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportResultsSetPagination
    filterset_class=DiscountReportFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpDiscountReportIndexView, self).get_queryset()
        
        employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        
        queryset = queryset.filter(stores__employeeprofile=employee_profile)
        queryset = queryset.annotate(
            receipt_count=Count('receipt', distinct=True),
            total=Sum('receipt__discount_amount')
        )
        queryset = queryset.exclude(receipt_count=0)
        queryset = queryset.order_by('-total', '-id').distinct() 

        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', ''),
            user_reg_no=self.request.GET.get('user_reg_no', ''),
        )

class EpTaxReportIndexView(generics.ListCreateAPIView):
    queryset = Tax.objects.all()
    serializer_class = TaxReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportResultsSetPagination
    filterset_class=TaxReportFilter
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpTaxReportIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        
        queryset = queryset.filter(stores__employeeprofile=employee_profile)
        queryset = queryset.annotate(
            receipt_count=Count('receipt', distinct=True),
            total=Sum('receipt__tax_amount')
        )
        queryset = queryset.exclude(receipt_count=0)
        queryset = queryset.order_by('-total', '-id').distinct()

        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', ''),
            user_reg_no=self.request.GET.get('user_reg_no', ''),
        )

class EpProductReportIndexView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportResultsSetPagination
    filterset_class= ProductReportFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpProductReportIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            stores__employeeprofile__user=self.request.user,
            is_variant_child=False,
            is_bundle=False,
        )
        queryset = queryset.annotate(
            receiptline_count=Count(
                Case(
                    When(variant_count=0, then='receiptline'),
                    default='variants__product_variant__receiptline',
                ), 
                distinct=True
            ),
            total=Sum('receiptline__price')
        )
        queryset = queryset.exclude(receiptline_count=0)
        queryset = queryset.order_by('-total', '-id').distinct()

        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', ''),
            user_reg_no=self.request.GET.get('user_reg_no', ''),
        )

class EpModifierReportIndexView(generics.ListCreateAPIView):
    queryset = Modifier.objects.all()
    serializer_class = ModifierReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportResultsSetPagination
    filterset_class = ModifierReportFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpModifierReportIndexView, self).get_queryset()
        
        queryset = queryset.filter(stores__employeeprofile__user=self.request.user)
        queryset = queryset.annotate(
            receiptline_count=Count('modifieroption__receiptline', distinct=True),
            total=Sum('modifieroption__price')
        )
        queryset = queryset.exclude(receiptline_count=0)
        queryset = queryset.order_by('-total', '-id').distinct()

        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', ''),
            user_reg_no=self.request.GET.get('user_reg_no', ''),
        )

class EpStorePaymentMethodReportIndexView(generics.ListCreateAPIView):
    queryset = StorePaymentMethod.objects.all()
    serializer_class = StorePaymentMethodReportListSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = ReportStorePaymentMethodResultsSetPagination
    filterset_class = StorePaymentMethodReportFilter

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpStorePaymentMethodReportIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            receiptpayment__receipt__store__employeeprofile__user=self.request.user)
        queryset = queryset.annotate(
            receiptpayment_count=Count('receiptpayment', distinct=True),
            total=Sum('receiptpayment__amount')
        )
        queryset = queryset.exclude(receiptpayment_count=0)
        queryset = queryset.order_by('-total', '-id').distinct()

        return queryset
    
    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(
            *args, 
            **kwargs, 
            date_after=self.request.GET.get('date_after', ''),
            date_before=self.request.GET.get('date_before', ''),
            store_reg_no=self.request.GET.get('store_reg_no', ''),
            user_reg_no=self.request.GET.get('user_reg_no', ''),
        )
