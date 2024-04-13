from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from api.serializers.accounts.hijack_serializers import HijackSerializer
from api.utils.permission_helpers.api_view_permissions import IsSuperUserPermission

from core.my_throttle import ratelimit

from api.views.accounts.utils import LoginUtils

THROTTLE_RATES = settings.THROTTLE_RATES

class HijackView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsSuperUserPermission)

    @ratelimit(scope='api_ip', rate=THROTTLE_RATES['login_rate'], alt_name='login')
    @ratelimit(scope='api_login', rate=THROTTLE_RATES['api_token_rate'], alt_name='login')
    def post(self, request, *args, **kwargs):

        if kwargs.get('request_throttled', None):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = HijackSerializer(data=request.data)

        if serializer.is_valid():

            try:
                user = get_user_model().objects.get(
                    reg_no=serializer.validated_data['reg_no']
                )

                return Response(LoginUtils.get_user_login_payload(user))
            except: # pylint: disable=bare-except
                pass

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)