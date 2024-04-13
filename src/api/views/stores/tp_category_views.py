from pprint import pprint
from django.conf import settings
from django.db.models import F, Value

from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled

from core.my_throttle import ratelimit

from api.serializers import (
    LeanCategoryListSerializer,
    CategoryEditViewSerializer,
    CategoryListSerializer,
)
from api.utils.api_pagination import (
    StandardResultsSetPagination_10,
    LeanResultsSetPagination
)
from sales.models import Receipt

from stores.models import Category
from accounts.utils.user_type import TOP_USER

class TpLeanCategoryIndexView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = LeanCategoryListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpLeanCategoryIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TpLeanCategoryIndexView, self).get_queryset()
        
        queryset = queryset.filter(profile__user__email=self.request.user)
        queryset = queryset.order_by('-id')

        return queryset


class TpPosCategoryIndexView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = StandardResultsSetPagination_10
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    is_pos = False # A url parameter
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpPosCategoryIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(TpPosCategoryIndexView, self).get_queryset()
        
        queryset = queryset.filter(profile__user__email=self.request.user)

        if self.is_pos:
            queryset = queryset.order_by('id')
        else:
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
            current_user_profile=self.request.user.profile
        )
        
    @ratelimit(scope='api_ip', rate=settings.THROTTLE_RATES['api_category_rate'], alt_name='api_category_create')
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
        serializer.save(profile=self.request.user.profile)


class TpCategoryEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryEditViewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'reg_no'
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(TpCategoryEditView, self).get_queryset()
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
            category_reg_no=self.kwargs['reg_no']
        )