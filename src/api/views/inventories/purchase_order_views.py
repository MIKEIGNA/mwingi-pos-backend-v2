from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from django.conf import settings
from django.db.models.functions import Coalesce
from django.db.models.aggregates import Sum

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework import filters
from api.utils.api_filters import PurchaseOrderFilter
from api.utils.api_purchase_order_formset_helper import PurchaseOrderLineFormestHelpers
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission

from core.my_throttle import ratelimit

from api.serializers import (
    PurchaseOrderListSerializer, 
    PurchaseOrderViewSerializer,
    PurchaseOrderViewStatusSerializer
)
from api.utils.api_web_pagination import PurchaseOrderWebResultsSetPagination
from products.models import Product
from profiles.models import EmployeeProfile, Profile

from stores.models import Store
from inventories.models import PurchaseOrder, PurchaseOrderAdditionalCost, PurchaseOrderLine, Supplier
from accounts.utils.user_type import TOP_USER 

# pylint: disable=unsupported-binary-operation

class PurchaseOrderIndexView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = PurchaseOrderWebResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = PurchaseOrderFilter
    search_fields = ['reg_no',] 

    product_error_desc = "product_error"
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(PurchaseOrderIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(user__employeeprofile__profile__user=self.request.user)
            )
        else:
            top_user = EmployeeProfile.objects.get(user=self.request.user).profile.user
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(user__profile__employeeprofile__user=self.request.user) |
                Q(user__employeeprofile__profile__user=top_user)
            )

        queryset = queryset.order_by('-id')

        return queryset
    
    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)
            
    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_purchase_order_rate'], 
        alt_name='api_purchase_order_create'
    )
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            self.profile = self.get_profile()
            self.supplier = None
            self.store = None

            try:
                self.supplier = Supplier.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['supplier_reg_no']
                ) 
            
                self.store = Store.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['store_reg_no']
                )           

            except Exception as e: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)
            
        return self.create(request, *args, **kwargs)
    
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Start our stuff here do our stuff here
        result = self.perform_create(serializer)

        if result == self.product_error_desc:
            return Response(
                {'non_field_errors': 'Product error.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return self.create_purchase_order(serializer)


        try:
            return self.create_purchase_order(serializer)
        except Exception as e: # pylint: disable=bare-except
            """ log here """

        return True
        
    def get_product(self, product_reg_no):

        product_model = None

        try:
            product_model = Product.objects.get(
                profile=self.profile, 
                reg_no=product_reg_no
            ) 

        except Exception: # pylint: disable=bare-except
            " Do nothing "

        return product_model

    def verify_purchase_order_lines(self, serializer):

        lines = serializer.validated_data['purchase_order_lines']

        total_amount = 0
        lineData = []
        for line in lines:

            product = self.get_product(line['product_reg_no'])

            if not product:
                return None, None

            lineData.append({
                'product': product,
                'quantity': line['quantity'],
                'purchase_cost': line['purchase_cost'],
            })

            total_amount += line['purchase_cost'] * line['quantity']

        return lineData, total_amount

    def verify_purchase_orider_additional_cost(self, serializer):

        lines = serializer.validated_data['purchase_order_additional_cost']

        total_amount = 0
        lineData = []
        for line in lines:

            lineData.append({
                'name': line['name'],
                'amount': line['amount'],
            })

            total_amount += line['amount']

        return lineData, total_amount
        
    def create_purchase_order(self, serializer):

        # Verify and collect purchase order lines
        order_line, lines_amount = self.verify_purchase_order_lines(serializer)

        if order_line == None:
            return self.product_error_desc

        # Verify and collect purchase order additional costs
        cost_line, costs_amount = self.verify_purchase_orider_additional_cost(serializer)

        # Only edit created date if the user has the required permission
        created_date_timestamp=0
        if self.request.user.has_perm('accounts.can_edit_purchase_order_date'):
            created_date_timestamp=serializer.validated_data['created_date_timestamp']

        purchase_order = PurchaseOrder.objects.create(
            user=self.request.user,
            supplier=self.supplier,
            store=self.store,
            notes=serializer.validated_data['notes'],
            total_amount=lines_amount + costs_amount,
            created_date_timestamp=created_date_timestamp
        )

        for line in order_line:

            PurchaseOrderLine.objects.create(
                purchase_order = purchase_order,
                product= line['product'],
                quantity = line['quantity'],
                purchase_cost = line['purchase_cost'],
            )

        for line in cost_line:

            PurchaseOrderAdditionalCost.objects.create(
                purchase_order = purchase_order,
                name = line['name'],
                amount = line['amount'],
            )

        if serializer.validated_data['status']:
            purchase_order.status = serializer.validated_data['status']
            purchase_order.save()

        return True

        
class PurchaseOrderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no' 

    # Custom variables
    supplier = None
    store = None
    po_total_amount = 0
    purchase_order_model = None

    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(PurchaseOrderView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(user__employeeprofile__profile__user=self.request.user)
            )
        else:
            top_user = EmployeeProfile.objects.get(user=self.request.user).profile.user
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(user__profile__employeeprofile__user=self.request.user) |
                Q(user__employeeprofile__profile__user=top_user)
            )

        queryset = queryset.filter(
            reg_no=self.kwargs['reg_no'],
        ) 

        return queryset
    
    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)

    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        
        # Don't edit if the purchase order has been received already
        if self.get_object().status == PurchaseOrder.PURCHASE_ORDER_RECEIVED:
            return Response(status=status.HTTP_200_OK)

        if serializer.is_valid(raise_exception=True):

            self.purchase_order_model = self.get_object()
            # store = purchase_order.store

            lines_info = serializer.validated_data['lines_info']
            lines_to_add = serializer.validated_data['lines_to_add']
            lines_to_remove = serializer.validated_data['lines_to_remove']

            # Update purchase order lines
            success = PurchaseOrderLineFormestHelpers.update_store_delivery_lines(
                lines_info=lines_info,
                lines_to_remove=lines_to_remove
            )

            PurchaseOrderLineFormestHelpers.lines_to_add(
                purchase_order=self.purchase_order_model,
                products_to_add=lines_to_add
            )

            try:

                profile = self.get_profile()

                self.supplier = Supplier.objects.get(
                profile=profile, 
                    reg_no=serializer.validated_data['supplier_reg_no']
                )

                self.store = Store.objects.get(
                    profile=profile, 
                    reg_no=serializer.validated_data['store_reg_no']
                ) 

            except: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)

            if not success:
                error_data = {'non_field_errors': 'Lines error.'}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
    
    def perform_update(self, serializer):

        # Only edit created date if the user has the required permission
        created_date_timestamp=0
        if self.request.user.has_perm('accounts.can_edit_purchase_order_date'):
            created_date_timestamp=serializer.validated_data['created_date_timestamp']
        
        # Calculate PO total amount
        self.po_total_amount = self.purchase_order_model.purchaseorderline_set.all().aggregate(
            total_amount=Coalesce(Sum('amount'), Decimal(0.00)),
        )['total_amount']

        serializer.save(
            store=self.store,
            supplier=self.supplier,
            total_amount=self.po_total_amount,
            created_date_timestamp = created_date_timestamp
        ) 

class PurchaseOrderViewStatus(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderViewStatusSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'

    # Custom variables
    supplier = None
    store = None
    po_total_amount = 0
    purchase_order_model = None

    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(PurchaseOrderViewStatus, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(user__employeeprofile__profile__user=self.request.user)
            )
        else:
            top_user = EmployeeProfile.objects.get(user=self.request.user).profile.user
            queryset = queryset.filter(
                Q(user=self.request.user) | 
                Q(user__profile__employeeprofile__user=self.request.user) |
                Q(user__employeeprofile__profile__user=top_user)
            )

        queryset = queryset.filter(reg_no=self.kwargs['reg_no']) 

        return queryset