import os

from django.db.models.signals import post_delete
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from stores.models import Store
from inventories.models import StockLevel
from .models import Product, ProductVariant

@receiver(post_delete, sender=Product)
def delete_product_assests_signal(sender, instance, **kwargs):
    """
    Deletes the the product's image
    """
    try:

        """ Delete the product image """
        # Check if image is not empty
        if instance.image.path:
            # Only delete images that are in the products image path to avoid
            # deleting important images
            if '/images/products/' in instance.image.path:
                os.remove(instance.image.path)

    except:
        pass

def product_stores_changed_signal(sender, instance, action, pk_set, **kwargs):
    """
    Creates stock level when new store is added to a product and deletes
    stock level when store is removed 
    """
    if action == 'post_add':

        for pk in pk_set:
            StockLevel.objects.create(
                store=Store.objects.get(pk=pk),
                product=instance,
                price=instance.price,
            )

    elif action == 'post_remove':
        for pk in pk_set:
            StockLevel.objects.filter(store__pk=pk, product=instance).delete()

m2m_changed.connect(product_stores_changed_signal, sender=Product.stores.through)


def product_variant_changed_signal(sender, instance, action, pk_set, **kwargs):
    """
    If product has variants, variant_count field is updated
    """
    if action == 'post_add' or action == 'post_remove':
        
        variant_count = instance.variants.all().count()
        
        # We only call instance's save if it needs updating
        if not instance.variant_count == variant_count:
 
            instance.variant_count = variant_count
            instance.save()
 
m2m_changed.connect(product_variant_changed_signal, sender=Product.variants.through)


def product_bundle_changed_signal(sender, instance, action, pk_set, **kwargs):
    """
    If product is a bundle, is_bundle field is changed to true and false
    otherwise
    """
    if action == 'post_add' or action == 'post_remove':

        is_bundle = instance.bundles.all().exists()
        
        # We only call instance's save if it needs updating
        if not instance.is_bundle == is_bundle:
            instance.is_bundle = is_bundle
            instance.save()
 
m2m_changed.connect(product_bundle_changed_signal, sender=Product.bundles.through)




def product_production_changed_signal(sender, instance, action, pk_set, **kwargs):
    """
    If product has productions, producton_count field is updated
    """
    if action == 'post_add' or action == 'post_remove':
        
        production_count = instance.productions.all().count()
        
        # We only call instance's save if it needs updating
        if not instance.production_count == production_count:
 
            instance.production_count = production_count
            instance.save()
 
m2m_changed.connect(product_production_changed_signal, sender=Product.productions.through)


# TODO Test this
@receiver(post_delete, sender=ProductVariant)
def delete_product_variant_assests_signal(sender, instance, **kwargs):
    """
    Deletes the the variant's product
    """
    Product.objects.filter(id=instance.product_variant.id).delete()
