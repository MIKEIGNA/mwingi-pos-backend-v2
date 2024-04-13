import os
from django.utils import timezone

from products.models import Modifier, ModifierOption
from profiles.models import Profile
from stores.models import Store


def bulk_modifier_creator(profile, num, ident):

    store = Store.objects.filter(profile=profile).order_by('id').first()

    for i in range(num):

        modifier_name = f'{ident} Modifier{i+1}'

        if not Modifier.objects.filter(profile=profile, name=modifier_name).exists():

            modifier = Modifier.objects.create(
                profile=profile, 
                name=modifier_name,
            )

            modifier.stores.add(store)

            for k in range(10):

                ModifierOption.objects.create(
                    modifier=modifier,
                    name=f'{modifier_name} Comb {k}',
                    price=1000,
                )




            print(f'Creating {modifier_name}')
        else:
            print(f'{modifier_name} already exists')

    print(f'Created {i+1} stores for {profile}')


def create_modifiers(delete_models, count=10):

    print('------------------------ Creating modifiers')

    if delete_models:
        Modifier.objects.all().delete()
        ModifierOption.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_modifier_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_modifier_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Modifiers cant be created since ", e)