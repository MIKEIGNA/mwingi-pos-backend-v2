from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from api.serializers import TaxPosListSerializer
from api.utils.api_pagination import LeanResultsSetPagination

from profiles.models import EmployeeProfile

from stores.models import Tax
from accounts.utils.user_type import TOP_USER


class EpTaxPosIndexView(generics.ListAPIView):
    queryset = Tax.objects.all()
    serializer_class = TaxPosListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination

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
        
        return super(EpTaxPosIndexView, self).get(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpTaxPosIndexView, self).get_queryset()

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
            current_user_profile=self.top_profile)
        