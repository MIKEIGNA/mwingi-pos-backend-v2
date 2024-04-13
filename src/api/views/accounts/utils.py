
from django.db.models.query_utils import Q
from rest_framework.authtoken.models import Token
from accounts.utils.user_type import TOP_USER
from api.utils.permission_helpers.api_view_user_perms import UserViewPermissionUtils

from profiles.models import LoyaltySetting, UserGeneralSetting


class LoginUtils:

    @staticmethod
    def get_user_login_payload(user):
        """
        Returns a payload that should be sent the moment a user has been logged in
        """
        token = Token.objects.get(user=user)

        print(user)

        if user.user_type == TOP_USER:
            profile = user.profile
        else:
            profile = user.employeeprofile.profile

        # We use use first since these queries return duplicates
        loyalty_value = LoyaltySetting.objects.filter(
            Q(profile__user=user) | 
            Q(profile__employeeprofile__user=user)
        ).first().value
        genral_setting = UserGeneralSetting.objects.filter(
            Q(profile__user=user) | 
            Q(profile__employeeprofile__user=user)
        ).first()

        # user.employeeprofile.profile.user

        payload = {
            'email': user.email,
            'name': user.get_full_name(),
            'token': token.key,
            'user_type': user.user_type,
            'reg_no': user.reg_no,
            'profile_image_url': user.get_profile_image_url(),
            'loyalty_value': loyalty_value,
            'general_setting':  genral_setting.get_settings_dict(),
            'payment_types': profile.get_store_payments()
        }
        # Get and insert user permissions
        payload.update(
            UserViewPermissionUtils.get_user_token_view_permission_dict(user)
        )

        return payload