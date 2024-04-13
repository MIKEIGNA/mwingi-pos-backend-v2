from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import permissions
from rest_framework import generics
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from api.serializers.profiles.user_settings_serializers import (
    ReceiptSettingListSerializer, 
    ReceiptSettingViewSerializer,
    UserGeneralSettingViewSerializer
)
from api.utils.permission_helpers.api_view_permissions import CanViewUserSettingsPermission, IsTopUserPermission

from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_throttle import ratelimit

from profiles.models import LoyaltySetting, ReceiptSetting, UserGeneralSetting

from api.serializers import LoyaltySettingViewSerializer
from api.utils.api_pagination import LeanResultsSetPagination

class LoyaltySettingView(UserActivityLogMixin, generics.RetrieveUpdateAPIView):
    queryset = LoyaltySetting.objects.all()
    serializer_class = LoyaltySettingViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission, 
        CanViewUserSettingsPermission
    )

    def get_queryset(self):

        queryset = super(LoyaltySettingView, self).get_queryset()
        queryset = queryset.filter(profile__user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj


class ReceiptSettingIndexView(UserActivityLogMixin, generics.ListCreateAPIView):
    queryset = ReceiptSetting.objects.all().select_related('store') 
    serializer_class = ReceiptSettingListSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission, 
        CanViewUserSettingsPermission
    )
    pagination_class = LeanResultsSetPagination
    
    def get_queryset(self):
      
        queryset = super(ReceiptSettingIndexView, self).get_queryset()

        queryset = queryset.filter(
            profile__user__email=self.request.user
        )
        queryset = queryset.order_by('-id')

        return queryset


class ReceiptSettingView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReceiptSetting.objects.all().select_related('store')
    serializer_class = ReceiptSettingViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission, 
        CanViewUserSettingsPermission
    )
    lookup_field = 'reg_no'

    def get_queryset(self):
        queryset = super(ReceiptSettingView, self).get_queryset()
        queryset = queryset.filter(
            profile__user__email=self.request.user, 
            reg_no=self.kwargs['reg_no']
        )

        return queryset

    @ratelimit(
        scope='api_user', 
        rate=settings.THROTTLE_RATES['api_receipt_rate'], 
        alt_name='api_receipt_edit'
    )
    def put(self, request, *args, **kwargs):

        # if api_throttled is in kwargs, throttle the view
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(
                request, response, *args, **kwargs)

            return self.response

        return self.update(request, *args, **kwargs)

class UserGeneralSettingView(UserActivityLogMixin, generics.RetrieveUpdateAPIView):
    queryset = UserGeneralSetting.objects.all()
    serializer_class = UserGeneralSettingViewSerializer
    permission_classes = (
        permissions.IsAuthenticated, 
        IsTopUserPermission, 
        CanViewUserSettingsPermission
    )

    def get_queryset(self):

        queryset = super(UserGeneralSettingView, self).get_queryset()
        queryset = queryset.filter(profile__user__email=self.request.user)

        return queryset

    def get_object(self):

        queryset = self.filter_queryset(self.get_queryset())

        # Get the single item from the filtered queryset
        self.obj = get_object_or_404(queryset)

        # May raise a permission denied
        self.check_object_permissions(self.request, self.obj)

        return self.obj