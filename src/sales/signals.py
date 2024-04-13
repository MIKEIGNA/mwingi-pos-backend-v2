from decimal import Decimal
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce

from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import CustomerDebt

User = get_user_model()


def _update_customer_debt(customer):

    total_debt = CustomerDebt.objects.filter(customer=customer).all().aggregate(
        total=Coalesce(Sum('debt'), Decimal(0.00)))['total']

    customer.current_debt = round(total_debt, 2)
    customer.save()


@receiver(post_save, sender=CustomerDebt)
def customer_debt_created_signal(sender, instance, created, **kwargs):
    """ 
    Update customer current debt
    """

    if created:

        if not instance.customer: return

        _update_customer_debt(instance.customer)

@receiver(post_delete, sender=CustomerDebt)
def customer_debt_delete_signal(sender, instance, **kwargs):
    """ 
    Update customer current debt
    """
    if not instance.customer: return

    _update_customer_debt(instance.customer)

