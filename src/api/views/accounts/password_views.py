from datetime import timedelta

from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.password_validation import validate_password, get_password_validators
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.core.exceptions import ValidationError

from rest_framework import permissions
from rest_framework.generics import GenericAPIView
from rest_framework import status, exceptions
from rest_framework.response import Response

from core.my_throttle import ratelimit
from core.my_settings import MySettingClass
from accounts.utils.logout_users import logout_user_everywhere

from api.serializers import (
    PasswordResetSerializer, 
    PasswordTokenSerializer, 
    ResetTokenSerializer, 
    PasswordChangeSerializer
)

from accounts.models import ResetPasswordToken, clear_expired


User = get_user_model()
RESET_TOKEN_EXPIRY_TIME = settings.DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME
FRONTEND_SITE_NAME = settings.FRONTEND_SITE_NAME


sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'password', 'old_password', 'new_password1', 'new_password2'
    )
)

# The PasswordChangeView solution was inspired by django-rest-auth package
class PasswordChangeView(GenericAPIView):
    """
    Calls Django Auth SetPasswordForm save method.

    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(PasswordChangeView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Even though user sessions are deleted by django when a password is
        # changed, we call 'logout_user_everywhere' to regenerate user's token
        logout_user_everywhere(request.user)

        return Response({"detail": "New password has been saved."})


class ResetPasswordRequestToken(GenericAPIView):
    """
    An Api View which provides a method to request a password reset token based on an e-mail address

    Sends a signal reset_password_token_created when a reset token was created
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = PasswordResetSerializer

    @ratelimit(
        scope='api_ip', 
        rate=settings.THROTTLE_RATES['password_reset_rate'], 
        alt_name='password_reset_request')
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Check if request has been throttled
        if kwargs.get('request_throttled', None):
            return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Check if we are in maintenance mode
        if MySettingClass.maintenance_mode():
            serializer.is_valid()
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # before we continue, delete all existing expired tokens
        password_reset_token_validation_time = RESET_TOKEN_EXPIRY_TIME

        # datetime.now minus expiry hours
        now_minus_expiry_time = timezone.now() - timedelta(hours=password_reset_token_validation_time)

        # delete all tokens where created_date < now - 24 hours
        clear_expired(now_minus_expiry_time)

        # Try to find a user by email address and make sure they are active
        try:
            user = User.objects.get(email=email, is_active=True)

            tokens = ResetPasswordToken.objects.filter(user=user)

            # Check if the user already has a token
            if (tokens.count() > 0):
                token = tokens[0]

            else:
                # No token exists, generate a new token
                token = ResetPasswordToken.objects.create(user=user)

            self.send_token_to_user(token)
        except:
            """ Do nothing """
    
        return Response(status=status.HTTP_200_OK)

    def send_token_to_user(self, token):

        # send an e-mail to the user
        context = {
            'site_name': FRONTEND_SITE_NAME,
            'user': token.user,
            'reset_password_url': f"{FRONTEND_SITE_NAME}/password-reset/confirm/{token.key}"
            }

        # Create and send email  

        subject = f'Password reset on {FRONTEND_SITE_NAME}'
        message = render_to_string('accounts/rest_password_reset_email.html', context)
        # from_email: A string. If None, Django will use the value of the 
        # DEFAULT_FROM_EMAIL setting 
        from_email = None
        recipient_list = [token.user.email]

        send_mail(subject, message, from_email, recipient_list, fail_silently=False,)


class ResetPasswordValidateToken(GenericAPIView):
    """
    An Api View which provides a method to verify that a token is valid
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = ResetTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if we are in maintenance mode
        if MySettingClass.maintenance_mode():
            serializer.is_valid()
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(status=status.HTTP_200_OK)


class ResetPasswordConfirm(GenericAPIView):
    """
    An Api View which provides a method to reset a password based on a unique token
    """
    throttle_classes = ()
    permission_classes = ()
    serializer_class = PasswordTokenSerializer

    def post(self, request, *args, **kwargs):
        
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        token = serializer.validated_data['token']

        # find token
        reset_password_token = ResetPasswordToken.objects.filter(key=token).first()

        # Proceed in changing password if we have valid token and user
        if reset_password_token and reset_password_token.user.is_active:
        
            # validate the password against existing validators
            try:
                # validate the password against existing validators
                validate_password(
                    password,
                    user=reset_password_token.user,
                    password_validators=get_password_validators(settings.AUTH_PASSWORD_VALIDATORS)
                )
            except ValidationError as e:

                # raise a validation error for the serializer
                raise exceptions.ValidationError({
                    'password': e.messages
                })

            reset_password_token.user.set_password(password)
            reset_password_token.user.save()

        # Delete all password reset tokens for this user
        ResetPasswordToken.objects.filter(user=reset_password_token.user).delete()

        return Response(status=status.HTTP_200_OK)