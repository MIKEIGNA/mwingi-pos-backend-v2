import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from mysettings.models import MySetting
from profiles.models import Profile

User = get_user_model()


class Command(BaseCommand):
    """
    Should be only called in a docker env

    To call this command,

    python manage.py manage_docker_superuser

    Used to create a 1 superuser and 1 normal user 
    """
    help = 'Used to create a 1 superuser and 1 normal user'

    def create_superuser(self):

        try:

            email = os.environ["SUPERUSER_EMAIL"]
            password = os.environ["SUPERUSER_PASSWORD"]

            profile_exists = Profile.objects.filter(user__email=email).exists()

            if not profile_exists:
                print("Creating superuser")

                User.objects.create_superuser(
                    email=email,
                    first_name='Dolla',
                    last_name='Bucks',
                    phone='254718371899',
                    gender=0,
                    password=password
                )

                profile = Profile.objects.get(user__email=email)
                profile.location = "Nairobi"
                profile.about = "I am a king"
                profile.save()

            else:
                print("We already have a docker superuser")

        except Exception as e:
            print('Error ', e)

    def create_nomral_user(self):

        try:

            email = os.environ["NORMALUSER_EMAIL"]
            password = os.environ["NORMALUSER_PASSWORD"]

            profile_exists = Profile.objects.filter(user__email=email).exists()

            if not profile_exists:
                print("Creating normal user")

                User.objects.create(
                    email=email,
                    first_name='Jack',
                    last_name='Shephard',
                    phone='254718371891',
                    gender=0,
                    password=password
                )

                profile = Profile.objects.get(user__email=email)
                profile.location = "Nairobi"
                profile.about = "I am a king"
                profile.save()

            else:
                print("We already have a docker normal user")

        except Exception as e:
            print('Error ', e)

    def handle(self, *args, **options):

        self.create_superuser()
        self.create_nomral_user()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        self.stdout.write(self.style.SUCCESS('Successfully created a production supersuer')) 



