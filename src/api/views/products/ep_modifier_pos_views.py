from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from core.mixins.log_entry_mixin import UserActivityLogMixin

from api.utils.api_pagination import LeanResultsSetPagination
from api.serializers import PosModifierListSerializer

from products.models import Modifier
from profiles.models import EmployeeProfile
from accounts.utils.user_type import TOP_USER


class EpModifierPosIndexView(UserActivityLogMixin, generics.ListAPIView):
    queryset = Modifier.objects.all()
    serializer_class = PosModifierListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    lookup_field = 'store_reg_no'

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
                user=self.request.user,
                stores__reg_no=self.kwargs['store_reg_no'],
            ).profile

        except: # pylint: disable=bare-except
            return False

        return True

    def get(self, request, *args, **kwargs):
        
        # Verify employee
        if not self.verify_user_and_get_top_profile():
            return Response(status=status.HTTP_404_NOT_FOUND)

        return super(EpModifierPosIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(EpModifierPosIndexView, self).get_queryset()
        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store_reg_no'],
        ).order_by('id')

        return queryset.filter(profile=self.top_profile)