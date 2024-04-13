from decimal import Decimal
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from django.conf import settings
from django.db.models.functions import Coalesce
from django.db.models.aggregates import Sum

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework import filters
from api.utils.api_filters import ProductTransformFilter
from api.utils.api_product_transform_formset_helper import ProductTransformLineFormestHelpers
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission
from core.logger_manager import LoggerManager 

from core.my_throttle import ratelimit

from api.serializers import ProductTransformListSerializer, ProductTransformViewSerializer
from api.utils.api_web_pagination import ProductTransformWebResultsSetPagination
from products.models import Product
from profiles.models import EmployeeProfile, Profile

from stores.models import Store
from inventories.models import ProductTransform, ProductTransformLine
from accounts.utils.user_type import TOP_USER 

# pylint: disable=unsupported-binary-operation

class ProductTransformIndexView(generics.ListCreateAPIView):
    queryset = ProductTransform.objects.all()
    serializer_class = ProductTransformListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = ProductTransformWebResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = ProductTransformFilter
    search_fields = ['reg_no',]

    product_error_desc = "product_error"
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(ProductTransformIndexView, self).get_queryset()
        
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
        rate=settings.THROTTLE_RATES['api_10_per_minute_create_rate'], 
        alt_name='api_product_transform_create'
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
                self.store = Store.objects.get(
                    profile=self.profile, 
                    reg_no=serializer.validated_data['store_reg_no']
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
        
        try:
            return self.create_product_transform(serializer)
        except: # pylint: disable=bare-except
            LoggerManager.log_critical_error() 
            
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

    def create_product_transform(self, serializer):

        lineData = []
        lines = serializer.validated_data['product_transform_lines']

        total_quantity = 0
        for line in lines:

            source_product = self.get_product(line['source_product_reg_no'])
            target_product = self.get_product(line['target_product_reg_no'])

            if not source_product or not target_product:
                return self.product_error_desc
    
            lineData.append({
                'source_product': source_product,
                'target_product': target_product,
                'quantity': line['quantity'],
                'added_quantity': line['added_quantity'],
                'cost': line['cost'],
            })

            total_quantity += line['quantity']

        product_transform = ProductTransform.objects.create(
            user=self.request.user,
            store=self.store,
            total_quantity=total_quantity,
        ) 

        for line in lineData:
            ProductTransformLine.objects.create(
                product_transform=product_transform,
                source_product=line['source_product'],
                target_product=line['target_product'],
                quantity=line['quantity'],
                added_quantity=line['added_quantity'],
                cost=line['cost'],
            )

        if serializer.validated_data['status']:
            product_transform.status = serializer.validated_data['status']
            product_transform.save()

        return True

class ProductTransformView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductTransform.objects.all()
    serializer_class = ProductTransformViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(ProductTransformView, self).get_queryset()

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
        if self.get_object().status == ProductTransform.PRODUCT_TRANSFORM_RECEIVED:
            return Response(status=status.HTTP_200_OK)
    
        if serializer.is_valid(raise_exception=True):

            try:

                profile = self.get_profile()

                self.store = Store.objects.get(
                    profile=profile, 
                    reg_no=serializer.validated_data['store_reg_no']
                ) 

            except Exception as e: # pylint: disable=bare-except
                return Response(status=status.HTTP_404_NOT_FOUND)

            self.product_transform_model = self.get_object()
            # store = product_transform.store

            lines_info = serializer.validated_data['lines_info']
            lines_to_add = serializer.validated_data['lines_to_add']
            lines_to_remove = serializer.validated_data['lines_to_remove']

            # Update purchase order lines
            success = ProductTransformLineFormestHelpers.update_store_delivery_lines(
                lines_info=lines_info,
                lines_to_remove=lines_to_remove
            )

            ProductTransformLineFormestHelpers.lines_to_add(
                product_transform=self.product_transform_model,
                products_to_add=lines_to_add
            )

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

        # Calculate PT total_quantity
        self.pt_total_quantity = self.product_transform_model.producttransformline_set.all().aggregate(
            total_quantity=Coalesce(Sum('quantity'), Decimal(0.00)),
        )['total_quantity']

        serializer.save(
            store=self.store,
            total_quantity=self.pt_total_quantity,
        ) 
