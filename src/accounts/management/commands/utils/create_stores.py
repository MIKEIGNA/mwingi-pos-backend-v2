import os
from django.utils import timezone

from profiles.models import Profile

from stores.models import (
    StoreCount, 
    Store
) 

from core.test_utils.create_store_models import create_new_store


def bulk_store_creator(profile, num, ident):

    for i in range(num):

        name = f'{ident} Store{i+1}'

        if not Store.objects.filter(profile=profile, name=name).exists():
            create_new_store(profile, name,  created_date=timezone.now())

            print(f'Creating {name}')
        else:
            print(f'{name} already exists')

    print(f'Created {i+1} stores for {profile}')


def create_stores(delete_models, count=10):

    print('------------------------ Creating stores')

    if delete_models:
        StoreCount.objects.all().delete()
        Store.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_store_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_store_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Stores cant be created since ", e)