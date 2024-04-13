from django.conf import settings
import django_filters

from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled

from api.utils.api_view_formset_utils import ApiEmployeeStoreFormestHelpers
from api.utils.api_web_pagination import DiscountWebResultsSetPagination
from api.utils.permission_helpers.api_view_permissions import CanViewItemsPermission, IsEmployeeUserPermission, ItemPermission

from core.my_throttle import ratelimit

from api.serializers import DiscountEditViewSerializer, DiscountListSerializer
from profiles.models import EmployeeProfile

from stores.models import Discount, Store

class EpDiscountIndexView(generics.ListCreateAPIView):
    queryset = Discount.objects.all()
    serializer_class = DiscountListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission, 
        IsEmployeeUserPermission, 
        CanViewItemsPermission
    )
    pagination_class = DiscountWebResultsSetPagination
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_fields = ['stores__reg_no']
    search_fields = ['name',]
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpDiscountIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)

        queryset = queryset.filter(stores__employeeprofile=employee_profile)
        queryset = queryset.order_by('-id')

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
            current_user_profile=self.request.user.employeeprofile.profile)
        
    @ratelimit(scope='api_ip', rate=settings.THROTTLE_RATES['api_discount_rate'], alt_name='api_discount_create')
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            
            """ Confirm if stores belongs to the store"""
            stores_info = serializer.validated_data['stores_info']

            # Confirm if store belongs to the employee user
            self.manager_employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            self.collected_stores = ApiEmployeeStoreFormestHelpers.validate_store_reg_nos_for_manager_user(
                stores_info, self.manager_employee_profile,
            )

            if not type(self.collected_stores) == list:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        
        try:
            self.create_discount(serializer)
        except: # pylint: disable=bare-except
            """ log here """
        
    def create_discount(self, serializer):

        discount = Discount.objects.create(
            profile=self.manager_employee_profile.profile,
            name=serializer.validated_data['name'],
            amount=serializer.validated_data['amount']
        )

        discount.stores.add(*self.collected_stores)

class EpDiscountEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Discount.objects.all()
    serializer_class = DiscountEditViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        ItemPermission,
        IsEmployeeUserPermission,
        CanViewItemsPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        self.employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        self.profile = self.employee_profile.profile

        queryset = super(EpDiscountEditView, self).get_queryset()

        queryset = queryset.filter(
            reg_no=self.kwargs['reg_no'],
            stores__employeeprofile=self.employee_profile
        ).distinct()

        return queryset

    def get_object(self):
        
        queryset = self.filter_queryset(self.get_queryset())
            
        # Get the single item from the filtered queryset
        self.object = generics.get_object_or_404(queryset)
                   
        # May raise a permission denied
        self.check_object_permissions(self.request, self.object)
            
        return self.object

    def get_store_list(self, queryset):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = queryset.order_by('id')
        stores = [{'name': s.name, 'reg_no': s.reg_no} for s in queryset]

        return stores

    def get_serializer_context(self):
        context = super(EpDiscountEditView, self).get_serializer_context()

        context['available_stores'] = self.get_store_list(
            Store.objects.filter(employeeprofile=self.employee_profile)
        )
        context['registered_stores'] = self.get_store_list(
            self.object.stores.all()
        )
          
        return context
    
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
            current_user_profile=self.profile,
            discount_reg_no=self.kwargs['reg_no']
        )

    def put(self, request, *args, **kwargs):
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():

            """ Confirm if store belongs to the top user"""
            stores_info = serializer.validated_data['stores_info']

            """ Confirm if store belongs to the top user"""
            self.manager_employee_profile = EmployeeProfile.objects.get(user=self.request.user)

            self.collected_stores = ApiEmployeeStoreFormestHelpers.validate_store_reg_nos_for_manager_user(
                stores_info, self.manager_employee_profile
            )

            if not type(self.collected_stores) == list:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

        return self.update(request, *args, **kwargs)

    def perform_update(self, serializer):

        serializer.save()

        """
        Adds or removes stores from the passed model
        """
        ApiEmployeeStoreFormestHelpers.add_or_remove_stores(
            serializer.instance,
            self.manager_employee_profile,
            self.collected_stores
        )
