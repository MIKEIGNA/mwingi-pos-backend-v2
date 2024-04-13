
import os
from inventories.models import PurchaseOrder, PurchaseOrderAdditionalCost, PurchaseOrderLine, Supplier
from profiles.models import Profile
from stores.models import Store
from products.models import Product

def bulk_purchase_order_creator(profile, num, ident):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()


    supplier1 = Supplier.objects.filter(profile=profile).order_by('id').first()
    supplier2 = Supplier.objects.filter(profile=profile).order_by('id').last()

    num = num//2

    for i in range(num):

        # ----------------- Stock adjustment 1

        note1 = f'{ident} note{i+1} 1'

        if PurchaseOrder.objects.filter(notes=note1).exists():
            print(f'{note1} already exists')
            return

        print(f'Creating {note1}')
       
    
        product1 = Product.objects.filter(stores=store1).order_by('id').first()
        product2 = Product.objects.filter(stores=store1).order_by('id').last()

        purchase_order1 = PurchaseOrder.objects.create(
            user=profile.user,
            supplier=supplier1,
            store=store1,
            notes=note1,
            status=PurchaseOrder.PURCHASE_ORDER_PENDING,
            total_amount=3400,
        )

        # Create purchase_order1
        PurchaseOrderLine.objects.create(
            purchase_order=purchase_order1,
            product=product1,
            quantity=10,
            purchase_cost=150,
        )
    
        # Create purchase_order2
        PurchaseOrderLine.objects.create(
            purchase_order=purchase_order1,
            product=product2,
            quantity=14,
            purchase_cost=100
        )

        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=purchase_order1,
            name='Transport',
            amount=200
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=purchase_order1,
            name='Labour',
            amount=300
        )






        # ----------------- Stock adjustment 1

        note2 = f'{ident} note{i+1} 2'

        if PurchaseOrder.objects.filter(notes=note2).exists():
            print(f'{note2} already exists')
            return

        print(f'Creating {note2}')

        product1 = Product.objects.filter(stores=store2).order_by('id').first()
        product2 = Product.objects.filter(stores=store2).order_by('id').last()

        purchase_order2 = PurchaseOrder.objects.create(
            user=profile.user,
            supplier=supplier2,
            store=store2,
            notes=note2,
            status=PurchaseOrder.PURCHASE_ORDER_RECEIVED,
            total_amount=6000,
        )

        # Create purchase_order1
        PurchaseOrderLine.objects.create(
            purchase_order=purchase_order2,
            product=product1,
            quantity=20,
            purchase_cost=250,
        )
    
        # Create purchase_order2
        PurchaseOrderLine.objects.create(
            purchase_order=purchase_order2,
            product=product2,
            quantity=144,
            purchase_cost=240,
        )

        # Create purchase order additional cost 1
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=purchase_order2,
            name='Loading',
            amount=250
        )
    
        # Create purchase order additional cost 2
        PurchaseOrderAdditionalCost.objects.create(
            purchase_order=purchase_order2,
            name='Offloading',
            amount=500
        )

    print(f'Created {i+1} inventory counts for {profile}')


def create_purchase_orders(delete_models, count=10):

    if delete_models:
        PurchaseOrderLine.objects.all().delete()
        PurchaseOrder.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_purchase_order_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_purchase_order_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Purchase order cant be created since ", e)