import django_filters.rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from django.conf import settings

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework import filters
from api.serializers.inventories.transfer_order_serializers import TransferOrderCompletedListSerializer
from api.utils.api_filters import TransferOrderFilter
from api.utils.api_transfer_order_formset_helper import TransferOrderLineFormestHelpers
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission

from core.my_throttle import ratelimit

from api.serializers import (
    TransferOrderListSerializer, 
    TransferOrderViewSerializer,
    TransferOrderViewStatusSerializer
)
from api.utils.api_web_pagination import StandardWebResultsAndStoresSetPagination
from products.models import Product, ProductProductionMap
from profiles.models import EmployeeProfile, Profile

from stores.models import Store
from inventories.models import TransferOrder, TransferOrderLine
from accounts.utils.user_type import TOP_USER 

# pylint: disable=unsupported-binary-operation

class TransferOrderIndexView(generics.ListCreateAPIView):
    queryset = TransferOrder.objects.all()
    serializer_class = TransferOrderListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = StandardWebResultsAndStoresSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = TransferOrderFilter
    search_fields = ['reg_no',]

    # Custom variables
    product_error_desc = "product_error"
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TransferOrderIndexView, self).get_queryset()
        
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
        rate=settings.THROTTLE_RATES['api_transfer_order_rate'], 
        alt_name='api_transfer_order_create'
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
            self.store = None

            try:
                self.source_store = Store.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['source_store_reg_no']
                )

                self.destination_store = Store.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['destination_store_reg_no']
                )           

            except: # pylint: disable=bare-except
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

        return self.create_transfer_order(serializer)
        
        # try:
        #     return self.create_transfer_order(serializer)
        # except Exception as e: # pylint: disable=bare-except
        #     """ log here """
        #     print(e)

        return True

    def get_product(self, product_reg_no):

        product_model = None

        try:
            product_model = Product.objects.get(
                profile=self.profile, 
                reg_no=product_reg_no
            ) 

        except: # pylint: disable=bare-except
            " Do nothing "

        return product_model
        
    def create_transfer_order(self, serializer):

        lineData = []
        lines = serializer.validated_data['transfer_order_lines']
        
        total_quantity = 0
        for line in lines:

            product = self.get_product(line['product_reg_no'])

            if not product:
                return self.product_error_desc

            lineData.append({
                'product': product,
                'quantity': line['quantity'],
            })

            total_quantity += line['quantity']

        transfer_order = TransferOrder.objects.create(
            user=self.request.user,
            source_store=self.source_store,
            destination_store=self.destination_store,
            notes=serializer.validated_data['notes'],
            quantity=total_quantity,
            source_description=serializer.validated_data['source_description'],

        )

        for line in lineData:

            TransferOrderLine.objects.create(
                transfer_order = transfer_order,
                product= line['product'],
                quantity = line['quantity'],
            )

        if serializer.validated_data['status']:
            transfer_order.status = serializer.validated_data['status']
            transfer_order.save()

        return True
    

class TransferOrderCompletedView(generics.ListCreateAPIView):
    queryset = TransferOrder.objects.all()
    serializer_class = TransferOrderCompletedListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = StandardWebResultsAndStoresSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = TransferOrderFilter
    search_fields = ['reg_no',]

    # Custom variables
    product_error_desc = "product_error"
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TransferOrderCompletedView, self).get_queryset()
        
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
        rate=settings.THROTTLE_RATES['api_transfer_order_rate'], 
        alt_name='api_transfer_order_create'
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
            self.store = None

            try:
                self.source_store = Store.objects.get(
                    profile=self.profile, 
                    loyverse_store_id=serializer.validated_data['source_store_id']
                )

                self.destination_store = Store.objects.get(
                    profile=self.profile, 
                    loyverse_store_id=serializer.validated_data['destination_store_id']
                )           

            except: # pylint: disable=bare-except
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
        return self.create_transfer_order(serializer)

    def get_product(self, loyverse_variant_id):

        product_model = None

        try:
            product_model = Product.objects.get(
                profile=self.profile, 
                loyverse_variant_id=loyverse_variant_id
            ) 

        except: # pylint: disable=bare-except
            " Do nothing "

        return product_model
        
    def create_transfer_order(self, serializer):

        lineData = []
        lines = serializer.validated_data['transfer_order_lines']
        
        total_quantity = 0
        for line in lines:

            line_product = self.get_product(line['loyverse_variant_id'])
            line_quantity = line['quantity']

            if not line_product:
                return self.product_error_desc
            
            # First check if the product is mapped to another product
            product_map = ProductProductionMap.objects.filter(
                product_map=line_product
            ).first()

            if product_map:
                master_product = Product.objects.filter(productions__product_map=line_product).first()

                if master_product:
                    master_product_quantity = line_quantity/product_map.quantity

                    line_product = master_product
                    line_quantity = master_product_quantity
            
            lineData.append({
                'product': line_product,
                'quantity': line_quantity,
            })

            total_quantity += line_quantity

        transfer_order = TransferOrder.objects.create(
            user=self.request.user,
            source_store=self.source_store,
            destination_store=self.destination_store,
            notes=serializer.validated_data['notes'],
            quantity=total_quantity,
            is_auto_created=True,
            source_description=serializer.validated_data['source_description'],
        )

        for line in lineData:
            TransferOrderLine.objects.create(
                transfer_order = transfer_order,
                product= line['product'],
                quantity = line['quantity'],
            ) 

        return True

        
class TransferOrderView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransferOrder.objects.all()
    serializer_class = TransferOrderViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'

    # Custom variables
    source_store = None
    destination_store = None
    to_total_amount = 0
    transfer_order_model = None
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(TransferOrderView, self).get_queryset()

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
        
        # Don't edit if the transfer order has been received already
        if self.get_object().status == TransferOrder.TRANSFER_ORDER_RECEIVED:
            return Response(status=status.HTTP_200_OK)

        if serializer.is_valid(raise_exception=True):

            self.transfer_order_model = self.get_object()
            # store = transfer_order.store

            lines_info = serializer.validated_data['lines_info']
            lines_to_add = serializer.validated_data['lines_to_add']
            lines_to_remove = serializer.validated_data['lines_to_remove']

            # Update transfer order lines
            success = TransferOrderLineFormestHelpers.update_store_delivery_lines(
                lines_info=lines_info,
                lines_to_remove=lines_to_remove
            )

            TransferOrderLineFormestHelpers.lines_to_add(
                transfer_order=self.transfer_order_model,
                products_to_add=lines_to_add
            )

            try:

                profile = self.get_profile()

                self.source_store = Store.objects.get(
                    profile=profile, 
                    reg_no=serializer.validated_data['source_store_reg_no']
                ) 

                self.destination_store = Store.objects.get(
                    profile=profile, 
                    reg_no=serializer.validated_data['destination_store_reg_no']
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

        total_quantity = 0
        for line in serializer.validated_data['lines_info']:
            total_quantity += line['quantity']

        serializer.instance.source_store=self.source_store
        serializer.instance.destination_store=self.destination_store
        serializer.instance.quantity = total_quantity
        serializer.save()
    

class TransferOrderViewStatus(generics.RetrieveUpdateDestroyAPIView):
    queryset = TransferOrder.objects.all()
    serializer_class = TransferOrderViewStatusSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'

    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(TransferOrderViewStatus, self).get_queryset()

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
    
    
