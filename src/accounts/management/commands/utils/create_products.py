import os
from core.test_utils.create_product_variants import create_1d_variants

from profiles.models import Profile

from products.models import (
    Modifier,
    ProductBundle,
    ProductCount, 
    Product
) 

from stores.models import Store, Tax, Category
from inventories.models import StockLevel


def bulk_product_creator(profile, num, ident):

    store1 = Store.objects.filter(profile=profile).order_by('id').first()
    store2 = Store.objects.filter(profile=profile).order_by('id').last()

    tax = Tax.objects.filter(profile=profile).order_by('id').first()
    category1 = Category.objects.filter(profile=profile).order_by('id').first()
    category2 = Category.objects.filter(profile=profile).order_by('id').last()

    # ------------------------- Product 1 that has nothing fancy
    product = Product.objects.create(
            profile=profile,
            category=category1,
            name=f'{ident} Oil1',
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            show_image=True,
            track_stock=True
        )

    product.stores.add(store1)

    # ------------------------- Product 2 normal product with 0 price
    product = Product.objects.create(
            profile=profile,
            name=f'{ident} Oil2',
            price=0,
            cost=1000,
            sku='sku1',
            barcode='code123',
            show_image=True,
            track_stock=True
        )

    product.stores.add(store1, store2)

    # ------------------------- Product 3 sodl by weight 
    product = Product.objects.create(
            profile=profile,
            name=f'{ident} Oil3',
            price=3500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            sold_by_each=False,
            show_image=True,
            track_stock=True

    )

    product.stores.add(store1, store2)

    # ------------------------- Product 4 sold by weight with 0 price
    product = Product.objects.create(
            profile=profile,
            name=f'{ident} Oil4',
            price=0,
            cost=1000,
            sku='sku1',
            barcode='code123',
            sold_by_each=False,
            show_image=True,
            track_stock=True

        )

    product.stores.add(store1)

    # ------------------------- Product 5 that has tax and and category
    product_shampoo = Product.objects.create(
            profile=profile,
            tax=tax,
            category=category1,
            name=f'{ident} Shampoo',
            price=4500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

    product_shampoo.stores.add(store1)


    # ------------------------- Product 6 that has tax and and category
    shampoo_master = Product.objects.create(
            profile=profile,
            tax=tax,
            category=category2,
            name=f'{ident} Shampoo Bundle',
            price=20000,
            cost=1000,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

    shampoo_master.stores.add(store1)

    # Create master product with 2 bundles
    shampoo_bundle = ProductBundle.objects.create(
        product_bundle=product_shampoo,
        quantity=30
    )

    shampoo_master.bundles.add(shampoo_bundle)



    # ------------------------- Product 7 that has modifiers
    product = Product.objects.create(
            profile=profile,
            tax=tax,
            category=category1,
            name=f'{ident} Gel',
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            show_image=True,
            track_stock=True
        )
    product.stores.add(store1)

    modifiers = Modifier.objects.filter(stores__reg_no=store1.reg_no).order_by('id')

    product.modifiers.add(modifiers[0], modifiers[1])

    level = StockLevel.objects.get(store=store1, product=product)
    level.units = 5000
    level.save()


    # ------------------------- Product 8 that has variants
    product = Product.objects.create(
            profile=profile,
            tax=tax,
            category=category2,
            name=f'{ident} Cream Variants',
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            track_stock=True
        )

    product.stores.add(store1)

    modifiers = Modifier.objects.filter(stores__reg_no=store1.reg_no).order_by('id')

    product.modifiers.add(modifiers[0], modifiers[1])

    # Create 3 variants for master product
    create_1d_variants(
        master_product=product,
        profile=profile,
        store1=store1,
        store2=store2
    )


    # ------------------------- Product 9 that has nothing fancy
    product = Product.objects.create(
            profile=profile,
            category=category2,
            name=f'{ident} Gloss',
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            show_image=True,
            track_stock=True
        )

    product.stores.add(store1)

def create_products(delete_models, count=10):

    print('------------------------ Creating products')

    if delete_models:
        ProductCount.objects.all().delete()
        Product.objects.all().delete()

    try:

        profile1 = Profile.objects.get(user__email=os.environ.get("FIRST_USER_EMAIL"))
        bulk_product_creator(profile1, count, 'b')

        profile2 = Profile.objects.get(user__email='jack@gmail.com')
        bulk_product_creator(profile2, count, 'j')
        
    except Exception as e:
        print("Product cant be created since ", e)