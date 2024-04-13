from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import filters

from api.serializers.stores.store_serializers import (
    LeanStoreWithReceiptSettingListSerializer,
    StoreListSerializer,
    LeanStoreListSerializer
)
from api.utils.api_pagination import (
    LeanResultsSetPagination,
    StandardResultsSetPagination_200
)
from api.utils.permission_helpers.api_view_permissions import CanViewStoresPermission

from stores.models import Store
from accounts.utils.user_type import TOP_USER


class EpLeanStoreIndexView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = LeanStoreListSerializer
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpLeanStoreIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpLeanStoreIndexView, self).get_queryset()
        queryset = queryset.order_by('name')

        return queryset.filter(employeeprofile__user__email=self.request.user)

class EpLeanStoreWithReceiptSettingIndexView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = LeanStoreWithReceiptSettingListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpLeanStoreWithReceiptSettingIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpLeanStoreWithReceiptSettingIndexView, self).get_queryset()
        queryset = queryset.order_by('name')

        return queryset.filter(employeeprofile__user__email=self.request.user)

class EpStoreIndexView(generics.ListAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreListSerializer
    permission_classes = (permissions.IsAuthenticated, CanViewStoresPermission)
    pagination_class = StandardResultsSetPagination_200
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpStoreIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpStoreIndexView, self).get_queryset()
        
        queryset = queryset.filter(employeeprofile__user__email=self.request.user)
        queryset = queryset.order_by('name')

        return queryset
    
  
        
    

        