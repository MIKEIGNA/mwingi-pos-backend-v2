from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework import filters
from rest_framework.views import APIView

from api.serializers.clusters.serializers import StoreClusterViewSerializer
from api.utils.api_pagination import StandardResultsSetPagination_50
from api.utils.api_view_formset_utils import ApiWebStoreFormestHelpers
from api.utils.permission_helpers.api_view_permissions import CanViewClustersPermission, IsTopUserPermission
from api.serializers import (
    StoreClusterListSerializer, 
    StoreClusterLeanListSerializer, 
    StoreClusterCreateSerializer
)

from clusters.models import StoreCluster
from stores.models import Store
from accounts.utils.user_type import TOP_USER

class StoreClusterLeanIndexView(generics.ListAPIView):
    queryset = StoreCluster.objects.all()
    permission_classes = (
        permissions.IsAuthenticated,
    )
    pagination_class = StandardResultsSetPagination_50
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    show_stock=False

    def get_serializer_class(self):
            return StoreClusterLeanListSerializer
    
    def get_queryset(self):

        queryset = super(StoreClusterLeanIndexView, self).get_queryset()

        current_user = self.request.user

        if (current_user.user_type == TOP_USER):
            queryset = queryset.filter(profile__user__email=current_user)
        else:
            employee_profile = current_user.employeeprofile
            queryset = queryset.filter(profile=employee_profile.profile)

        # queryset = queryset.filter(profile__user=self.request.user)
        # queryset = queryset.order_by('name')

        return queryset


class StoreClusterIndexView(generics.ListAPIView):
    queryset = StoreCluster.objects.all()
    permission_classes = (
        permissions.IsAuthenticated, 
        # IsTopUserPermission,
        CanViewClustersPermission
        
    )
    pagination_class = StandardResultsSetPagination_50
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    show_stock=False

    def get_serializer_class(self):
            return StoreClusterListSerializer
    
    def get_queryset(self):

        queryset = super(StoreClusterIndexView, self).get_queryset()
        queryset = queryset.filter(profile__user=self.request.user)
        queryset = queryset.order_by('name')

        return queryset

class StoreClusterCreateView(APIView):
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewClustersPermission
    )

    def post(self, request, *args, **kwargs):

        serializer = StoreClusterCreateSerializer(data=request.data)

        if serializer.is_valid():

            self.create_cluster(serializer)
            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create_cluster(self, serializer):

        name = serializer.validated_data['name']
        stores_info = serializer.validated_data['stores_info']

        cluster = StoreCluster.objects.create(profile=self.request.user.profile, name=name)

        stores_reg_no = [store['reg_no'] for store in stores_info]

        store_ids = Store.objects.filter(
            reg_no__in=stores_reg_no
        ).values_list('id', flat=True)

        cluster.stores.add(*store_ids)

class StoreClusterView(generics.RetrieveUpdateDestroyAPIView):
    queryset = StoreCluster.objects.all()
    serializer_class = StoreClusterViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission,
        CanViewClustersPermission
    )
    lookup_field = 'reg_no'

    def get_object(self):

        reg_no = self.kwargs['reg_no']

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000:
            raise Http404
     
        self.obj = super(StoreClusterView, self).get_object()
        return self.obj
    
    def get_queryset(self):
 
        queryset = super(StoreClusterView, self).get_queryset()
        queryset = queryset.filter(profile__user=self.request.user)
        queryset = queryset.filter(reg_no=self.kwargs['reg_no'])

        return queryset

    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid(raise_exception=True):

            # Confirm if stores belongs to the store
            self.collected_stores = ApiWebStoreFormestHelpers.validate_store_reg_nos(
                stores_info=serializer.validated_data['stores_info'],
            )

            if not type(self.collected_stores) == dict:
                error_data = {'stores_info': "You provided wrong stores."}
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST) 

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer): 
        
        # Adds or removes stores from the passed model
        ApiWebStoreFormestHelpers.add_or_remove_stores(
            model=serializer.instance, 
            collected_stores=self.collected_stores['collected_stores_ids']
        )

        serializer.save()