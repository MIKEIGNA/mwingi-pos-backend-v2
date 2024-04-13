from django.conf import settings

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled

from core.my_throttle import ratelimit

from api.serializers import TaxPosEditViewSerializer, TaxPosListSerializer
from api.utils.api_pagination import LeanResultsSetPagination

from stores.models import Store, Tax
from accounts.utils.user_type import TOP_USER


class TpTaxPosIndexView(generics.ListCreateAPIView):
    queryset = Tax.objects.all()
    serializer_class = TaxPosListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpTaxPosIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TpTaxPosIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            profile__user__email=self.request.user,
            stores__reg_no=self.kwargs['store_reg_no']
        )
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
            current_user_profile=self.request.user.profile)
        
    
    @ratelimit(scope='api_ip', rate=settings.THROTTLE_RATES['api_tax_rate'], alt_name='api_tax_create')
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            self.store = Store.objects.get(
                profile__user=self.request.user, 
                reg_no=self.kwargs['store_reg_no']
            )           

        except: # pylint: disable=bare-except
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return self.create(request, *args, **kwargs)
            
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)

        tax = serializer.instance
        tax.stores.add(self.store)

        
class TaxPosEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tax.objects.all()
    serializer_class = TaxPosEditViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(TaxPosEditView, self).get_queryset()
        queryset = queryset.filter(
            profile__user__email=self.request.user, 
            reg_no=self.kwargs['reg_no'],
            stores__reg_no=self.kwargs['store_reg_no']
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
            tax_reg_no=self.kwargs['reg_no']
        )