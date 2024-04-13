import django_filters.rest_framework

from django.conf import settings

from rest_framework import permissions
from rest_framework import generics
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

from accounts.utils.user_type import TOP_USER
from api.utils.permission_helpers.api_view_permissions import CanViewInventoryPermission

from core.my_throttle import ratelimit
from core.my_settings import MySettingClass

from inventories.models import Supplier

from api.utils.api_pagination import (
    StandardResultsSetPagination_10, 
    LeanResultsSetPagination
)
from api.serializers import (
    LeanSupplierListSerializer,
    SupplierListSerializer, 
    SupplierViewSerializer
)
from profiles.models import Profile 

class LeanSupplierIndexView(generics.ListAPIView):
    queryset = Supplier.objects.all()
    serializer_class = LeanSupplierListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email']

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(LeanSupplierIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )
        queryset = queryset.order_by('-id')

        return queryset

class SupplierIndexView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierListSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    pagination_class = StandardResultsSetPagination_10
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email']

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
        rate=settings.THROTTLE_RATES['api_supplier_rate'], 
        alt_name='api_supplier_create'
    )
    def post(self, request, *args, **kwargs):
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)

            return self.response

        return super(SupplierIndexView, self).post(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(SupplierIndexView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )
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
            current_user_profile=self.get_profile()
        )

    def perform_create(self, serializer):
        
        # Add profile
        serializer.save(profile=self.get_profile())


class SupplierView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierViewSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        CanViewInventoryPermission
    )
    lookup_field = 'reg_no'

    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(SupplierView, self).get_queryset()

        if self.request.user.user_type == TOP_USER:
            queryset = queryset.filter(profile__user=self.request.user)
        else:
            queryset = queryset.filter(
                profile__employeeprofile__user=self.request.user
            )

        queryset = queryset.filter(reg_no=self.kwargs['reg_no'])

        return queryset
    
    def get_profile(self):
        """
        Returns the top profile
        """
        if self.request.user.user_type == TOP_USER:
            return self.request.user.profile
        
        else:
            return Profile.objects.get(employeeprofile__user=self.request.user)
    
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
            current_user_profile=self.get_profile(),
            supplier_reg_no=self.kwargs['reg_no']
        )