import os

from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import (
    EmployeeProfile, 
    Profile, 
    LoyaltySetting, 
    ReceiptSetting, 
    UserGeneralSetting
)

from stores.models import StorePaymentMethod

# pylint: disable=bare-except

@receiver(post_save, sender=Profile)
def profile_created_signal(sender, instance, created, **kwargs):
    """ 
    Create a loyalty and user general settings
    """

    if created:
        LoyaltySetting.objects.get_or_create(profile=instance, value=0.00)
        UserGeneralSetting.objects.get_or_create(profile=instance)

        # Create default store payment methods
        payment_methods = [
            StorePaymentMethod.CASH_TYPE,
            StorePaymentMethod.MPESA_TYPE,
            StorePaymentMethod.CARD_TYPE,
            StorePaymentMethod.POINTS_TYPE,
            StorePaymentMethod.DEBT_TYPE,
            StorePaymentMethod.OTHER_TYPE,
        ]

        for payment in payment_methods:
            StorePaymentMethod.objects.create(
                profile=instance,
                payment_type=payment
            )

@receiver(post_delete, sender=Profile)
def delete_profile_assests_signal(sender, instance, **kwargs):
    """
    Delte all the models and assets that depend on a profile model

    First we delete the profile's user 
    Second we delete the the profile's image
    """

    try:

        """ Delete this profile's user """
        get_user_model().objects.get(email=instance.user.email).delete()

        """ Delete the profile image """
        # Check if image is not empty
        if instance.image.path:
            # Only delete images that are in the profiles image path to avoid
            # deleting important images
            if '/images/profiles/' in instance.image.path:
                os.remove(instance.image.path)

    except:
        pass


@receiver(post_delete, sender=EmployeeProfile)
def delete_employee_profile_assests_signal(sender, instance, **kwargs):

    try:

        """ Delete this profile's user """
        get_user_model().objects.get(email=instance.user.email).delete()
        
        """ Delete the employee_profile image """
        # Check if image is not empty
        if instance.image.path:
            # Only delete images that are in the profiles image path to avoid
            # deleting important images
            if '/images/profiles/' in instance.image.path:
                os.remove(instance.image.path)
    except:
        pass



@receiver(post_delete, sender=ReceiptSetting)
def delete_receipt_setting_assests_signal(sender, instance, **kwargs):
    """
    Delete all the assets that depend on a receipt setting model

    """

    try:

        """ Delete the receipt setting image """
        # Check if image is not empty
        if instance.image.path:
            # Only delete images that are in the receipts image path to avoid
            # deleting important images
            if '/images/receipts/' in instance.image.path:
                os.remove(instance.image.path)

    except:
        pass