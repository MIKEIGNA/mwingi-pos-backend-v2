from pprint import pprint
from django.conf import settings

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from core.logging_utils import clean_logging_fields
from core.my_settings import MySettingClass
from core.mixins.log_entry_mixin import UserActivityLogMixin
from core.my_throttle import ratelimit

from api.views.accounts.utils import LoginUtils
from api.serializers import UserSerializer, ContactSerializer

from accounts.models import User, WebSocketTicket
from accounts.utils.user_type import TOP_USER
from accounts.utils.logout_users import logout_user_everywhere

THROTTLE_RATES = settings.THROTTLE_RATES


class TokenView(ObtainAuthToken):

    # A url parameter
    is_pos = False

    @ratelimit(scope='api_ip', rate=THROTTLE_RATES['login_rate'], alt_name='login')
    @ratelimit(scope='api_login', rate=THROTTLE_RATES['api_token_rate'], alt_name='login')
    def post(self, request, *args, **kwargs):
        # lll

        # if api_throttled is in kwargs, throttle the view
        if kwargs.get('request_throttled', None):
            response = self.handle_exception(Throttled(1))
            self.response = self.finalize_response(
                request, response, *args, **kwargs)

            return self.response

        m_mode = MySettingClass.maintenance_mode() 

        if m_mode:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Make sure only one user's pos can be logged in at a time
        if self.is_pos:
            if user.firebasedevice_set.filter(is_current_active=True).exists():
                return Response(status=status.HTTP_412_PRECONDITION_FAILED)

        return Response(LoginUtils.get_user_login_payload(user))

class LogoutView(APIView):
    """
    Calls Django logout method and delete the Token object
    assigned to the current User object.

    Accepts/Returns nothing.
    """
    permission_classes = (permissions.IsAuthenticated,)

    # A url parameter
    logout_everywhere = False
    is_pos = False

    def complete_pos_logout_tasks(self):

        """
        Deactivate pos device
        """
        devices = self.request.user.firebasedevice_set.filter(
            is_current_active=True
        )

        print(devices) 

        for device in devices:
            device.is_current_active = False
            device.save()

    def get(self, request, *args, **kwargs):

        if self.logout_everywhere:
            # Logout user both in api and web
            logout_user_everywhere(request.user)

        if self.is_pos or self.logout_everywhere:
            self.complete_pos_logout_tasks()

        return Response(status=status.HTTP_200_OK)


class SignupView(UserActivityLogMixin, APIView):
    permission_classes = ()
    """
    Creates the user.
    """

    @ratelimit(scope='api_ip', rate=THROTTLE_RATES['signup_rate'], alt_name='signup')
    def post(self, request, *args, **kwargs):

        if kwargs.get('request_throttled', None):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)

        maint, signup = MySettingClass.maintenance_signup()

        if maint:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not signup:
            return Response(status=status.HTTP_423_LOCKED)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():

            user = serializer.save(user_type=TOP_USER)

            if user:

                selializer_data = serializer.data

                """
                This is enclosed in a try statement coz it doesent work in 
                MagicMock's patch in testing
                """

                """ Log that new uer has been created """
                user_obj = User.objects.get(email=selializer_data['email'])
                # Value to be included in the change message
                include_value = selializer_data['email']

                """ Log that a new object was created with api"""
                self.ux_log_new_user_api(user_obj, include_value)

    
                return Response(
                    LoginUtils.get_user_login_payload(user), 
                    status=status.HTTP_201_CREATED
                )

        else:

            data = dict(serializer.data)

            """
            This will remove sensitive info like passwords
            """
            data = clean_logging_fields(data)

            message = '"{}<=>{}{}<=>{}"'.format(
                'login_invalid', 'form_invalid', dict(serializer.errors), data)
            self.request._request.payment_invalid_msg = message

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ContactView(UserActivityLogMixin, APIView):
    permission_classes = ()

    @ratelimit(scope='api_ip', rate=THROTTLE_RATES['contact_rate'], alt_name='signup')
    def post(self, request, *args, **kwargs):

        if kwargs.get('request_throttled', None):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = ContactSerializer(data=request.data)

        maint, allow_contact = MySettingClass.maintenance_allow_contact()

        if maint:
            serializer.is_valid()
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not allow_contact:
            serializer.is_valid()
            return Response(status=status.HTTP_423_LOCKED)

        if serializer.is_valid():

            #            email = request.user.email
            #            message = serializer.validated_data['message']

            return Response({"message": "Message sent succesfully"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebSocketTicketView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):

        websocket_ticket = WebSocketTicket.objects.create(
            user=self.request.user)

        return Response({'token': websocket_ticket.reg_no})
