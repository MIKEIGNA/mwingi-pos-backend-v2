from django.conf import settings
from rest_framework import permissions
from rest_framework import generics
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status

from accounts.utils.user_type import TOP_USER
from clusters.models import StoreCluster

from core.my_throttle import ratelimit
from core.my_settings import MySettingClass

from profiles.models import Customer

from api.utils.api_pagination import StandardResultsSetPagination_200
from api.serializers import CustomerPosListSerializer, CustomerPosViewSerializer

class TpPosCustomerIndexView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerPosListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination_200

    # Custom fields
    top_profile = None
    cluster = None
    
    def get(self, request, *args, **kwargs):
        
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.top_profile=self.request.user.profile
        
        return super(TpPosCustomerIndexView, self).get(request, *args, **kwargs)

    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_customer_rate'], 
        alt_name='api_customer_create'
    )
    def post(self, request, *args, **kwargs):
        
        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)

            return self.response

        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        allow_customer = MySettingClass.allow_new_customer()

        if not allow_customer:
            return Response(status=status.HTTP_423_LOCKED)

        self.top_profile=self.request.user.profile
        
        return super(TpPosCustomerIndexView, self).post(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TpPosCustomerIndexView, self).get_queryset()
        
        queryset = queryset.filter(profile=self.top_profile)
        queryset = queryset.order_by('id')

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
            current_user_profile=self.top_profile
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.cluster = StoreCluster.objects.get(
            reg_no=serializer.validated_data['cluster_reg_no']
        )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    def perform_create(self, serializer):

        serializer.validated_data.pop('cluster_reg_no')

        # Add profile
        serializer.save(
            profile=self.top_profile,
            cluster=self.cluster
        )



class TpPosCustomerView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerPosViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'reg_no'

    # Custom fields
    cluster = None

    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(TpPosCustomerView, self).get_queryset()
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
            customer_reg_no=self.kwargs['reg_no']
        )
    
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.cluster = StoreCluster.objects.get(
            reg_no=serializer.validated_data['cluster_reg_no']
        )
        
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)
    
    def perform_update(self, serializer):

        serializer.validated_data.pop('cluster_reg_no')

        # Add profile
        serializer.save(
            cluster=self.cluster
        )