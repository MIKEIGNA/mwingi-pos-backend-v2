
import os
from django.utils import timezone

from core.test_utils.create_store_models import create_new_tax
from profiles.models import Profile
from stores.models import Store, Tax, TaxCount

def bulk_tax_creator(profile, num, ident):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()

    for i in range(num):

        name = f'{ident} Tax{i+1}'

        if not Tax.objects.filter(profile=profile, name=name).exists():

            if i > 1:

                if (num % i) == 0:
                    create_new_tax(profile, store1, name, created_date=timezone.now())
                else:
                    create_new_tax(profile, store2, name, created_date=timezone.now())
            else:
                create_new_tax(profile, store1, name, created_date=timezone.now())


            print(f'Creating {name}')
        else:
            print(f'{name} already exists')

    print(f'Created {i+1} taxes for {profile}')



def create_taxes(delete_models, count=10):

    if delete_models:
        TaxCount.objects.all().delete()
        Tax.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_tax_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_tax_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Categories cant be created since ", e)