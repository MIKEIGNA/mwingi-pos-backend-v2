from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from django.conf import settings

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework import filters
from api.utils.api_filters import StockAdjustmentFilter
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission

from core.my_throttle import ratelimit

from api.serializers import StockAdjustmentListSerializer, StockAdjustmentViewSerializer
from api.utils.api_web_pagination import StandardWebResultsAndStoresSetPagination
from products.models import Product
from profiles.models import EmployeeProfile, Profile

from stores.models import Store
from inventories.models import StockAdjustment, StockAdjustmentLine
from accounts.utils.user_type import TOP_USER 

# pylint: disable=unsupported-binary-operation

class StockAdjustmentIndexView(generics.ListCreateAPIView):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = StandardWebResultsAndStoresSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_class = StockAdjustmentFilter
    search_fields = ['reg_no',]

    product_error_desc = "product_error"
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(StockAdjustmentIndexView, self).get_queryset()
        
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
        alt_name='api_stock_adjustment_create'
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
        return self.create_stock_adjustment(serializer)
        
        # try:
        #     return self.create_stock_adjustment(serializer)
        # except: # pylint: disable=bare-except
        #     """ log here """
            
        # return True

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

    def create_stock_adjustment_for_received_items(self, serializer):
        
        lineData = []
        lines = serializer.validated_data['stock_adjustment_lines']
        
        total_quantity = 0
        for line in lines:

            product = self.get_product(line['product_reg_no'])

            if not product:
                return self.product_error_desc

            lineData.append({
                'product': product,
                'add_stock': line['add_stock'],
                'cost': line['cost'],
            })

            total_quantity += line['add_stock']

        stock_adjustment = StockAdjustment.objects.create(
            user=self.request.user,
            store=self.store,
            notes=serializer.validated_data['notes'],
            reason=serializer.validated_data['reason'],
            quantity=total_quantity,
        )

        for line in lineData:

            StockAdjustmentLine.objects.create(
                stock_adjustment = stock_adjustment,
                product= line['product'],
                add_stock = line['add_stock'],
                cost = line['cost'],
            )

        return True

    def create_stock_adjustment_for_substracting(self, serializer):
        
        lineData = []
        lines = serializer.validated_data['stock_adjustment_lines']
        
        total_quantity = 0
        for line in lines:

            product = self.get_product(line['product_reg_no'])

            if not product:
                return self.product_error_desc

            lineData.append({
                'product': product,
                'remove_stock': line['remove_stock'],
            }) 

            total_quantity += line['remove_stock']

        stock_adjustment = StockAdjustment.objects.create(
            user=self.request.user,
            store=self.store,
            notes=serializer.validated_data['notes'],
            reason=serializer.validated_data['reason'],
            quantity=total_quantity,
        )

        for line in lineData:

            StockAdjustmentLine.objects.create(
                stock_adjustment = stock_adjustment,
                product= line['product'],
                remove_stock = line['remove_stock']
            )

        return True

    def create_stock_adjustment(self, serializer):

        reason = serializer.validated_data['reason']

        if reason == StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS:
            return self.create_stock_adjustment_for_received_items(serializer)

        elif reason == StockAdjustment.STOCK_ADJUSTMENT_LOSS or \
            reason == StockAdjustment.STOCK_ADJUSTMENT_DAMAGE or \
            reason == StockAdjustment.STOCK_ADJUSTMENT_EXPIRY:
            return self.create_stock_adjustment_for_substracting(serializer)

        return False

class StockAdjustmentView(generics.RetrieveDestroyAPIView):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(StockAdjustmentView, self).get_queryset()

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


    
    
