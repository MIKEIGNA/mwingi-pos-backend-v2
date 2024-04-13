from rest_framework import generics
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status

from core.mixins.log_entry_mixin import UserActivityLogMixin

from api.utils.api_pagination import LeanResultsSetPagination
from api.serializers import PosModifierListSerializer

from products.models import Modifier
from accounts.utils.user_type import TOP_USER


class TpModifierPosIndexView(UserActivityLogMixin, generics.ListAPIView):
    queryset = Modifier.objects.all()
    serializer_class = PosModifierListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LeanResultsSetPagination
    lookup_field = 'store_reg_no'

    def get(self, request, *args, **kwargs):
        
        # Make sure is top user
        if not self.request.user.user_type == TOP_USER:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        return super(TpModifierPosIndexView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Make sure only the owner can view his/her store
        """
        queryset = super(TpModifierPosIndexView, self).get_queryset()
        queryset = queryset.filter(
            stores__reg_no=self.kwargs['store_reg_no'],
        ).order_by('id')

        return queryset.filter(profile__user__email=self.request.user)