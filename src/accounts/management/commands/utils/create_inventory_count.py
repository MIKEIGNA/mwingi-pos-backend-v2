
import os
from inventories.models import InventoryCount, InventoryCountLine
from profiles.models import Profile
from stores.models import Store
from products.models import Product

def bulk_inventory_count_creator(profile, num, ident):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()

    num = num//2

    for i in range(num):

        # ----------------- Stock adjustment 1

        note1 = f'{ident} note{i+1} 1'

        if InventoryCount.objects.filter(notes=note1).exists():
            print(f'{note1} already exists')
            return

        print(f'Creating {note1}')
       
    
        product1 = Product.objects.filter(stores=store1).order_by('id').first()
        product2 = Product.objects.filter(stores=store1).order_by('id').last()

        inventory_count1 = InventoryCount.objects.create(
            user=profile.user,
            store=store1,
            notes=note1,
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=inventory_count1,
            product=product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=inventory_count1,
            product=product2,
            expected_stock=155,
            counted_stock=160,
        )

        # ----------------- Stock adjustment 1

        note2 = f'{ident} note{i+1} 2'

        if InventoryCount.objects.filter(notes=note2).exists():
            print(f'{note2} already exists')
            return

        print(f'Creating {note2}')

        product1 = Product.objects.filter(stores=store2).order_by('id').first()
        product2 = Product.objects.filter(stores=store2).order_by('id').last()


        inventory_count2 = InventoryCount.objects.create(
            user=profile.user,
            store=store2,
            notes=note2,
        )

        # Create inventory_count1
        InventoryCountLine.objects.create(
            inventory_count=inventory_count2,
            product=product1,
            expected_stock=100,
            counted_stock=77,
        )
    
        # Create inventory_count2
        InventoryCountLine.objects.create(
            inventory_count=inventory_count2,
            product=product2,
            expected_stock=155,
            counted_stock=160,
        )

    print(f'Created {i+1} inventory counts for {profile}')


def create_inventory_counts(delete_models, count=10):

    if delete_models:
        InventoryCountLine.objects.all().delete()
        InventoryCount.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_inventory_count_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_inventory_count_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Inventory counts cant be created since ", e)