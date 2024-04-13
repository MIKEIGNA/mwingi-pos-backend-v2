import os
from profiles.models import Profile
from inventories.models import Supplier, SupplierCount

from core.test_utils.create_user import create_new_random_supplier_user


def create_suppliers(delete_models, count=50):

    print('------------------------ Creating stores')

    if delete_models:
        SupplierCount.objects.all().delete()
        Supplier.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        create_new_random_supplier_user(profile1, count)

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        create_new_random_supplier_user(profile2, count)
        
    except Exception as e:
        print("Stores cant be created since ", e)