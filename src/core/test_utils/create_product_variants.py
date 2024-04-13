from inventories.models import StockLevel
from products.models import (
    Product, 
    ProductVariant, 
    ProductVariantOption, 
    ProductVariantOptionChoice
)

def create_1d_variants(master_product, profile, store1, store2):
    """
    Args:
        master_product (Product): A product which variants with be made for
        profile (Profile): Top profile
        category (Category): Category modoel that will be used with the variants
        tax (Tax): Tax model that will be used with the variants
        store1 (Store)
        store1 (Store) 

    Creates the following:
    * 1 ProductVariantOption (Size)


    * 3 variant products for master product with the following names
        - Small
        - Medium
        - Large
    """

    # Create product variant option
    product_variant_option = ProductVariantOption.objects.create(
        product=master_product,
        name='Size'
    )

    # Create product variant option choices
    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option,
        name='Small'
    )

    # Create product variant option choices
    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option,
        name='Medium'
    )

    # Create product variant option choices
    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option,
        name='Large'
    )

    choices = product_variant_option.productvariantoptionchoice_set.all().order_by('id')

    for choice in choices:
        # Add variant to product
        product = Product.objects.create(
            profile=profile,
            name=choice.name,
            price=1500,
            cost=800,
            barcode='code123',
            is_variant_child=True
        )
        product.stores.add(store1, store2)

        variant = ProductVariant.objects.create(product_variant=product)

        master_product.variants.add(variant)

    # Update store1 variants' stock level
    level = StockLevel.objects.get(product__name='Small', store=store1)
    level.minimum_stock_level = 50
    level.units = 100
    level.save()

    level = StockLevel.objects.get(product__name='Medium', store=store1)
    level.minimum_stock_level = 60
    level.units = 120
    level.save()

    level = StockLevel.objects.get(product__name='Large', store=store1)
    level.minimum_stock_level = 65
    level.units = 130
    level.save()

    # Update store2 variants' stock level
    level = StockLevel.objects.get(
        product__name='Small', store=store2)
    level.minimum_stock_level = 100
    level.units = 200
    level.save()

    level = StockLevel.objects.get(
        product__name='Medium', store=store2)
    level.minimum_stock_level = 110
    level.units = 220
    level.save()

    level = StockLevel.objects.get(
        product__name='Large', store=store2)
    level.minimum_stock_level = 115
    level.units = 230
    level.save()

def create_2d_variants(master_product, profile, store1, store2):
    """
    Args:
        master_product (Product): A product which variants with be made for
        profile (Profile): Top profile
        category (Category): Category modoel that will be used with the variants
        tax (Tax): Tax model that will be used with the variants
        store1 (Store)
        store1 (Store) 

    Creates the following:
    * 2 ProductVariantOption (Size) and (Color)


    * 9 variant products for master product with the following names
        - Small / White
        - Small / Black
        - Small / Red
        - Small / Green
        - Medium / White
        - Medium / Black
        - Medium / Red
        - Medium / Green
        - Large / White
        - Large / Black
        - Large / Red
        - Large / Green
    """

    # Create product variant option 1 and choices
    product_variant_option1 = ProductVariantOption.objects.create(
        product=master_product, name='Size')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option1, name='Small')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option1, name='Medium')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option1, name='Large')

    # Create product variant option 2 and choices
    product_variant_option2 = ProductVariantOption.objects.create(
        product=master_product, name='Color')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option2, name='White')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option2, name='Black')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option2, name='Red')

    ProductVariantOptionChoice.objects.create(
        product_variant_option=product_variant_option2, name='Green')

    # Create variants
    options1 = product_variant_option1.productvariantoptionchoice_set.all().order_by('id')
    options2 = product_variant_option2.productvariantoptionchoice_set.all().order_by('id')

    for opt1 in options1:
        for opt2 in options2:

            # Add variant to product
            product = Product.objects.create(
                profile=profile,
                name=f'{opt1.name} / {opt2.name}',
                price=1500,
                cost=800,
                barcode='code123'
            )
            product.stores.add(store1, store2)

            variant = ProductVariant.objects.create(product_variant=product)

            master_product.variants.add(variant)
