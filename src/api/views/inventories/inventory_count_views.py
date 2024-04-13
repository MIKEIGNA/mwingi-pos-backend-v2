from decimal import Decimal
import django_filters.rest_framework
from django_filters.rest_framework import DjangoFilterBackend

from django.conf import settings
from django.db.models.functions import Coalesce
from django.db.models.aggregates import Sum
from django.db.models import Q

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework import filters
from api.serializers.inventories.inventory_count_serializers import InventoryCountViewStatusSerializer
from api.utils.api_filters import InventoryCountFilter
from api.utils.api_inventory_count_formset_helper import InventoryCountLineFormestHelpers
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission

from core.my_throttle import ratelimit

from api.serializers import InventoryCountListSerializer, InventoryCountViewSerializer
from api.utils.api_web_pagination import StandardWebResultsAndStoresSetPagination
from products.models import Product
from profiles.models import EmployeeProfile, Profile

from stores.models import Store
from inventories.models import InventoryCount, InventoryCountLine
from accounts.utils.user_type import TOP_USER 

class InventoryCountIndexView(generics.ListCreateAPIView):
    queryset = InventoryCount.objects.all()
    serializer_class = InventoryCountListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = StandardWebResultsAndStoresSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = InventoryCountFilter
    search_fields = ['reg_no',]

    product_error_desc = "product_error"
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(InventoryCountIndexView, self).get_queryset()
        
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
        rate=settings.THROTTLE_RATES['api_inventory_count_rate'], 
        alt_name='api_inventory_count_create'
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
            return self.create_inventory_count(serializer)
        except: # pylint: disable=bare-except
            """ log here """

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
        
    def create_inventory_count(self, serializer):

        lineData = []
        lines = serializer.validated_data['inventory_count_lines']
        
        for line in lines:

            product = self.get_product(line['product_reg_no'])

            if not product:
                return self.product_error_desc

            lineData.append({
                'product': product,
                'expected_stock': line['expected_stock'],
                'counted_stock': line['counted_stock'],
            })

        inventory_count = InventoryCount.objects.create(
            user=self.request.user,
            store=self.store,
            notes=serializer.validated_data['notes'],
        )

        for line in lineData:

            InventoryCountLine.objects.create(
                inventory_count = inventory_count,
                product= line['product'],
                expected_stock = line['expected_stock'],
                counted_stock = line['counted_stock'],
            )

        return True

        
class InventoryCountView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryCount.objects.all()
    serializer_class = InventoryCountViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(InventoryCountView, self).get_queryset()
        
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
    
    """ 
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        
        # Don't edit if the inventory count has been received already
        if self.get_object().status == InventoryCount.INVENTORY_COUNT_COMPLETED:
            return Response(status=status.HTTP_200_OK)

        if serializer.is_valid(raise_exception=True):

            self.inventory_count_model = self.get_object()
            # store = inventory_count.store

            lines_info = serializer.validated_data['lines_info']
            lines_to_add = serializer.validated_data['lines_to_add']
            lines_to_remove = serializer.validated_data['lines_to_remove']

            # Update inventory count lines
            InventoryCountLineFormestHelpers.update_store_delivery_lines(
                lines_info=lines_info,
                lines_to_remove=lines_to_remove
            )

            InventoryCountLineFormestHelpers.lines_to_add(
                inventory_count=self.inventory_count_model,
                products_to_add=lines_to_add
            )

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
    
    def perform_update(self, serializer):

        serializer.save() 
    

class InventoryCountViewStatus(generics.RetrieveUpdateDestroyAPIView):
    queryset = InventoryCount.objects.all()
    serializer_class = InventoryCountViewStatusSerializer
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
        queryset = super(InventoryCountViewStatus, self).get_queryset()

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
            user=self.request.user, 
            reg_no=self.kwargs['reg_no'],
        ) 

        return queryset
    
    

    



    
    
