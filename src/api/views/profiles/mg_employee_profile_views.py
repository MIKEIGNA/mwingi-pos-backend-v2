import django_filters.rest_framework

from rest_framework import permissions
from rest_framework import generics
from rest_framework import filters

from api.serializers.profiles.mg_employee_serializers import MgLeanEmployeeProfileIndexViewSerializer
from api.utils.api_pagination import LeanResultsSetPagination, StandardResultsSetPagination_10
from api.utils.api_web_pagination import EmployeeWebResultsSetPagination, StandardWebResultsAndStoresSetPagination
from api.utils.permission_helpers.api_view_permissions import CanViewEmployeesPermission, IsEmployeeUserPermission

from core.mixins.log_entry_mixin import UserActivityLogMixin

from profiles.models import EmployeeProfile
from api.serializers import (
    MgEmployeeProfileIndexViewSerializer,
)

class MgLeanEmployeeProfileIndexView(generics.ListAPIView):
    queryset = EmployeeProfile.objects.all().select_related('user')
    serializer_class = MgLeanEmployeeProfileIndexViewSerializer
    permission_classes = (permissions.IsAuthenticated, IsEmployeeUserPermission)
    pagination_class = EmployeeWebResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
   
    def get_queryset(self):
        """
        Make sure only the owner can view his/her employee
        """
        queryset = super(MgLeanEmployeeProfileIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        
        queryset = queryset.filter(
            stores__employeeprofile=employee_profile
        ).order_by('-id'
        ).exclude(reg_no=employee_profile.reg_no)

        # Use distinct to prevent unwanted dupblicates when using many to many
        queryset = queryset.distinct()

        return queryset

class MgEmployeeProfileIndexView(UserActivityLogMixin, generics.ListCreateAPIView):
    queryset = EmployeeProfile.objects.all().select_related('profile', 'user')
    serializer_class = MgEmployeeProfileIndexViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsEmployeeUserPermission,
        CanViewEmployeesPermission
    )
    pagination_class = StandardWebResultsAndStoresSetPagination
    filter_backends = [
        filters.SearchFilter, 
        django_filters.rest_framework.DjangoFilterBackend
    ]
    filterset_fields = ['stores__reg_no']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def get_queryset(self):
        """
        Make sure only the owner can view his/her employee
        """
        queryset = super(MgEmployeeProfileIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)
        
        queryset = queryset.filter(
            stores__employeeprofile=employee_profile
        ).order_by('-id'
        ).select_related('user', 'subscription'
        ).exclude(reg_no=employee_profile.reg_no)

        # Use distinct to prevent unwanted dupblicates when using many to many
        queryset = queryset.distinct()

        return queryset

