
import os
from inventories.models import StockAdjustment, StockAdjustmentLine
from profiles.models import Profile
from stores.models import Store
from products.models import Product

def bulk_stock_adjustment_creator(profile, num, ident):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()

    num = num//2

    for i in range(num):

        # ----------------- Stock adjustment 1

        note1 = f'{ident} note{i+1} 1'

        if StockAdjustment.objects.filter(notes=note1).exists():
            print(f'{note1} already exists')
            return

        print(f'Creating {note1}')
       
    
        product1 = Product.objects.filter(stores=store1).order_by('id').first()
        product2 = Product.objects.filter(stores=store1).order_by('id').last()

        stock_adjustment1 = StockAdjustment.objects.create(
            user=profile.user,
            store=store1,
            notes=note1,
            reason=StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            quantity=24,
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=stock_adjustment1,
            product=product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=stock_adjustment1,
            product=product2,
            add_stock=14,
            cost=100,
        )




        # ----------------- Stock adjustment 1

        note2 = f'{ident} note{i+1} 2'

        if StockAdjustment.objects.filter(notes=note2).exists():
            print(f'{note2} already exists')
            return

        print(f'Creating {note2}')

        product1 = Product.objects.filter(stores=store2).order_by('id').first()
        product2 = Product.objects.filter(stores=store2).order_by('id').last()


        stock_adjustment2 = StockAdjustment.objects.create(
            user=profile.user,
            store=store2,
            notes=note2,
            reason=StockAdjustment.STOCK_ADJUSTMENT_LOSS,
            quantity=14,
        )

        # Create stock_adjustment1
        StockAdjustmentLine.objects.create(
            stock_adjustment=stock_adjustment2,
            product=product1,
            add_stock=10,
            cost=150,
        )
    
        # Create stock_adjustment2
        StockAdjustmentLine.objects.create(
            stock_adjustment=stock_adjustment2,
            product=product2,
            add_stock=14,
            cost=100,
        )

    print(f'Created {i+1} stock adjustments for {profile}')


def create_stock_adjustments(delete_models, count=10):

    if delete_models:
        StockAdjustmentLine.objects.all().delete()
        StockAdjustment.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_stock_adjustment_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_stock_adjustment_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Stock adjustments cant be created since ", e)