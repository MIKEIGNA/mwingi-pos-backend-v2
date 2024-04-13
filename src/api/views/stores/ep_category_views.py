from rest_framework import filters

from django.conf import settings

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled

from api.utils.permission_helpers.api_view_permissions import ItemPermission

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
from profiles.models import EmployeeProfile

from stores.models import Category
from accounts.utils.user_type import TOP_USER



class EpLeanCategoryIndexView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = LeanCategoryListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    def get(self, request, *args, **kwargs):
        
        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpLeanCategoryIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpLeanCategoryIndexView, self).get_queryset()
      
        queryset = queryset.filter(profile=self.request.user.employeeprofile.profile)
        queryset = queryset.order_by('-id')

        return queryset


class EpPosCategoryIndexView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    permission_classes = (permissions.IsAuthenticated, ItemPermission)
    pagination_class = StandardResultsSetPagination_10
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]

    is_pos = False # A url parameter
    
    def get(self, request, *args, **kwargs):
        
        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpPosCategoryIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpPosCategoryIndexView, self).get_queryset()
        
        queryset = queryset.filter(
            profile=self.request.user.employeeprofile.profile
        )
        
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
            current_user_profile=self.request.user.employeeprofile.profile
        )
        
    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_category_rate'], 
        alt_name='api_category_create'
    )
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return self.create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.employeeprofile.profile)
        
        
class EpCategoryEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryEditViewSerializer
    permission_classes = (permissions.IsAuthenticated, ItemPermission)
    lookup_field = 'reg_no'

    def verify_user_and_get_top_profile(self):
        """
        Returns True if user is not top user and employee has access
        to store

        Also extracts top_profile from employee profile and stores it globally
        """

        # Make sure is not top user
        if self.request.user.user_type == TOP_USER:
            return False

        try:
            self.top_profile = EmployeeProfile.objects.get(
                user=self.request.user
            ).profile

        except: # pylint: disable=bare-except
            return False

        return True

    def get(self, request, *args, **kwargs):
        
        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpCategoryEditView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(EpCategoryEditView, self).get_queryset()
        queryset = queryset.filter(
            profile=self.top_profile, 
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
            current_user_profile=self.top_profile,
            category_reg_no=self.kwargs['reg_no']
        )

    def put(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpCategoryEditView, self).put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpCategoryEditView, self).delete(request, *args, **kwargs)