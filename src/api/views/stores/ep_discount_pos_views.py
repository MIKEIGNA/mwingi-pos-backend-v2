from django.conf import settings

from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import Throttled
from api.utils.permission_helpers.api_view_permissions import ItemPermission

from core.my_throttle import ratelimit

from api.serializers import DiscountPosEditViewSerializer, DiscountPosListSerializer
from api.utils.api_pagination import StandardResultsSetPagination_10

from profiles.models import EmployeeProfile
from stores.models import Discount, Store
from accounts.utils.user_type import TOP_USER

class EpDiscountPosIndexView(generics.ListCreateAPIView):
    queryset = Discount.objects.all()
    serializer_class = DiscountPosListSerializer
    permission_classes = (permissions.IsAuthenticated, ItemPermission)
    pagination_class = StandardResultsSetPagination_10

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
        
        return super(EpDiscountPosIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpDiscountPosIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        
        queryset = queryset.filter(
            profile=self.top_profile,
            stores__employeeprofile=employee_profile,
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
            current_user_profile=self.top_profile
        )
        
    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['api_discount_rate'], 
        alt_name='api_discount_create'
    )
    def post(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view 
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(request, response, *args, **kwargs)
            
            return self.response
        
        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            self.store = Store.objects.get(
                profile=self.top_profile, 
                reg_no=self.kwargs['store_reg_no']
            )           

        except: # pylint: disable=bare-except
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return self.create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.employeeprofile.profile)

        discount = serializer.instance
        discount.stores.add(self.store)

        
class EpDiscountPosEditView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Discount.objects.all()
    serializer_class = DiscountPosEditViewSerializer
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
        
        return super(EpDiscountPosEditView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her object
        """
        queryset = super(EpDiscountPosEditView, self).get_queryset()
        queryset = queryset.filter(
            profile=self.top_profile, 
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
            current_user_profile=self.top_profile,
            discount_reg_no=self.kwargs['reg_no']
        )

    def put(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpDiscountPosEditView, self).put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):

        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(EpDiscountPosEditView, self).delete(request, *args, **kwargs)