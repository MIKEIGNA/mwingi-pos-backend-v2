from django.conf import settings

from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from api.utils.permission_helpers.api_view_permissions import CanViewStoresPermission

from core.my_throttle import ratelimit

from api.serializers.stores.store_serializers import (
    LeanStoreWithReceiptSettingListSerializer,
    StoreEditViewSerializer,
    StoreListCreateSerializer,
    LeanStoreListSerializer
)
from api.utils.api_pagination import (
    LeanResultsSetPagination,
    StandardResultsSetPagination_200
)

from stores.models import Store
from accounts.utils.user_type import TOP_USER


class TpLeanStoreIndexView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = LeanStoreListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',] 
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpLeanStoreIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(TpLeanStoreIndexView, self).get_queryset()
        queryset = queryset.order_by('name')

        return queryset.filter(
            profile__user__email=self.request.user,
            is_deleted=False
        ) 

class TpLeanStoreWithReceiptSettingIndexView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = LeanStoreWithReceiptSettingListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpLeanStoreWithReceiptSettingIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(TpLeanStoreWithReceiptSettingIndexView, self).get_queryset()
        queryset = queryset.order_by('name')

        return queryset.filter(
            profile__user__email=self.request.user,
            is_deleted=False
        )

class TpStoreIndexView(generics.ListCreateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreListCreateSerializer
    permission_classes = (permissions.IsAuthenticated, CanViewStoresPermission)
    pagination_class = StandardResultsSetPagination_200
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpStoreIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TpStoreIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            profile__user__email=self.request.user,
            is_deleted=False
        )
        queryset = queryset.order_by('name')

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
            current_user_profile=self.request.user.profile)
        
    
    @ratelimit(scope='api_ip', rate=settings.THROTTLE_RATES['api_store_rate'], alt_name='api_store_create')
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return self.create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        
        try:
            self.create_store(serializer)
        except: # pylint: disable=bare-except
            " log this "
        
    def create_store(self, serializer):
                
        Store.objects.create(
            profile=self.request.user.profile,
            name=serializer.validated_data['name'],
            address=serializer.validated_data['address'],
        )

        
class TpStoreEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreEditViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        CanViewStoresPermission
    )
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(TpStoreEditView, self).get_queryset()
        queryset = queryset.filter(
            profile__user__email=self.request.user, 
            reg_no=self.kwargs['reg_no']
        )

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
            current_user_profile=self.request.user.profile,
            store_reg_no=self.kwargs['reg_no']
        )
    
    def perform_destroy(self, instance):
        instance.soft_delete()