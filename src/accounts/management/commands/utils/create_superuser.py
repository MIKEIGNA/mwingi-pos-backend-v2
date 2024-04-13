import os
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.utils.user_type import TOP_USER

from profiles.models import Profile

User = get_user_model()


def create_superuser():
    
    email = os.environ.get("FIRST_USER_EMAIL")

    profile_exists = Profile.objects.filter(user__email=email).exists()

    if not profile_exists:

        try:
            
            print(f"Creating {email}")
            User.objects.create_superuser(
                email=email, 
                first_name=os.environ.get("FIRST_USER_FIRST_NAME"), 
                last_name=os.environ.get("FIRST_USER_LAST_NAME"), 
                phone=os.environ.get("FIRST_USER_PHONE_NUMBER"),
                gender=0,
                password=os.environ.get("FIRST_USER_PASSWORD")
            )

            profile = Profile.objects.get(user__email=email)
            profile.business_name = "Skypac"
            profile.location = "Nairobi"
            profile.save()

        except Exception as e:
            print(e)

    else:
        print(f"We already have {email}")


def create_loyverse_owner():
    
    email = os.environ.get("SECOND_USER_EMAIL")

    profile_exists = Profile.objects.filter(user__email=email).exists()

    if not profile_exists:

        try:
            
            print("Creating user")
            User.objects.create_user(
                email=email, 
                first_name=os.environ.get("SECOND_USER_FIRST_NAME"), 
                last_name=os.environ.get("SECOND_USER_LAST_NAME"), 
                phone=os.environ.get("SECOND_USER_PHONE_NUMBER"),
                user_type=TOP_USER,
                password=os.environ.get("SECOND_USER_PASSWORD")
            )

            profile = Profile.objects.get(user__email=email)
            profile.business_name = "Mwingi"
            profile.location = "Bellway business park"
            profile.save()

        except Exception as e:
            print("****")
            print(e)

    else:
        print(f"We already have {email}")
         
    