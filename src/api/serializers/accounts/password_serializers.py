from datetime import timedelta

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from accounts.models import ResetPasswordToken

User = get_user_model()
RESET_TOKEN_EXPIRY_TIME = settings.DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME

# The password change solution was inspired by django-rest-passwordreset package

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=30, required=True)


class PasswordValidateMixin:
    def validate(self, data):
        token = data.get('token')

        # get token validation time
        password_reset_token_validation_time = RESET_TOKEN_EXPIRY_TIME

        # find token
        try:
            reset_password_token = _get_object_or_404(ResetPasswordToken, key=token)
        except (TypeError, ValueError, ValidationError, Http404,
                ResetPasswordToken.DoesNotExist):
            raise Http404(_("The OTP password entered is not valid. Please check and try again."))

        # check expiry date
        expiry_date = reset_password_token.created_date + timedelta(
            hours=password_reset_token_validation_time)

        if timezone.now() > expiry_date:
            # delete expired token
            reset_password_token.delete()
            raise Http404(_("The token has expired"))
        return data

class ResetTokenSerializer(PasswordValidateMixin, serializers.Serializer):
    token = serializers.CharField(max_length=50)

class PasswordTokenSerializer(PasswordValidateMixin, serializers.Serializer):
    password = serializers.CharField(
        max_length=50, 
        label="Password", 
        #style={'input_type': 'password'}
        )
    token = serializers.CharField()