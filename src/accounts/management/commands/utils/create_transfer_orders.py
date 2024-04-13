
import os
from inventories.models import TransferOrder, TransferOrderLine
from profiles.models import Profile
from stores.models import Store
from products.models import Product

def bulk_transfer_order_creator(profile, num, ident):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()

    num = num//2

    for i in range(num):

        # ----------------- Transfer order 1

        note1 = f'{ident} note{i+1} 1'

        if TransferOrder.objects.filter(notes=note1).exists():
            print(f'{note1} already exists')
            return

        print(f'Creating {note1}')
       
    
        product1 = Product.objects.filter(stores=store1).order_by('id').first()
        product2 = Product.objects.filter(stores=store1).order_by('id').last()

        transfer_order1 = TransferOrder.objects.create(
            user=profile.user,
            source_store=store1,
            destination_store=store2,
            notes=note1,
            quantity=24,
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=transfer_order1,
            product=product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=transfer_order1,
            product=product2,
            quantity=14,
        )




        # ----------------- Transfer order 1

        note2 = f'{ident} note{i+1} 2'

        if TransferOrder.objects.filter(notes=note2).exists():
            print(f'{note2} already exists')
            return

        print(f'Creating {note2}')

        product1 = Product.objects.filter(stores=store2).order_by('id').first()
        product2 = Product.objects.filter(stores=store2).order_by('id').last()


        transfer_order2 = TransferOrder.objects.create(
            user=profile.user,
            source_store=store2,
            destination_store=store1,
            notes=note2,
            quantity=14,
        )

        # Create transfer_order1
        TransferOrderLine.objects.create(
            transfer_order=transfer_order2,
            product=product1,
            quantity=10,
        )
    
        # Create transfer_order2
        TransferOrderLine.objects.create(
            transfer_order=transfer_order2,
            product=product2,
            quantity=14,
        )

    print(f'Created {i+1} transfer orders for {profile}')


def create_transfer_orders(delete_models, count=10):

    if delete_models:
        TransferOrderLine.objects.all().delete()
        TransferOrder.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_transfer_order_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_transfer_order_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Transfer orders cant be created since ", e)