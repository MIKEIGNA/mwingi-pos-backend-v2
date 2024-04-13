from rest_framework import generics
from rest_framework import permissions

from api.utils.api_web_pagination import TaxWebResultsSetPagination
from api.utils.permission_helpers.api_view_permissions import CanViewUserSettingsPermission, IsEmployeeUserPermission
from api.serializers import TaxListSerializer

from profiles.models import EmployeeProfile
from stores.models import Tax


class EpTaxIndexView(generics.ListAPIView):
    queryset = Tax.objects.all()
    serializer_class = TaxListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsEmployeeUserPermission,
        CanViewUserSettingsPermission
    )
    pagination_class = TaxWebResultsSetPagination
    filterset_fields = ['stores__reg_no']
    
    def get_queryset(self):
        """
        Make sure only the owner can view his/her objects
        """
        queryset = super(EpTaxIndexView, self).get_queryset()

        employee_profile = EmployeeProfile.objects.get(user=self.request.user)

        queryset = queryset.filter(stores__employeeprofile=employee_profile)
        queryset = queryset.order_by('-id')

        return queryset
    
    