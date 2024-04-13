
import os
from django.utils import timezone

from core.test_utils.create_store_models import create_new_category
from profiles.models import Profile
from stores.models import Category, CategoryCount


def bulk_store_creator(profile, num, ident):

    for i in range(num):

        name = f'{ident} Category{i+1}'

        if not Category.objects.filter(profile=profile, name=name).exists():
            create_new_category(profile, name, created_date=timezone.now())

            print(f'Creating {name}')
        else:
            print(f'{name} already exists')

    print(f'Created {i+1} stores for {profile}')



def create_categories(delete_models, count=10):

    if delete_models:
        CategoryCount.objects.all().delete()
        Category.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_store_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_store_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Categories cant be created since ", e)