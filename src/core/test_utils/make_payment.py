import datetime

from django.utils import timezone

from mylogentries.models import PaymentLog
from profiles.models import Profile

from billing.models import Payment
from billing.utils.payment_utils.price_gen import PriceGeneratorClass
from billing.models import Subscription


def make_payment(user, reg_no, duration):

    profile = Profile.objects.get(user__email=user.email)

    one_month_price = PriceGeneratorClass.account_price_calc(duration)

    payment_log = PaymentLog.objects.create(
        amount=one_month_price,
        payment_method="manual payment",
        payment_type='single {}'.format("account"),
        email=profile.user.email,
        reg_no=reg_no,
        duration=duration
    )

    Payment.objects.create(
        paymentlog=payment_log,
        amount=one_month_price,
        account_reg_no=reg_no,
        duration=duration,
        parent_reg_no=0,
        account_type='employee',
    )

def make_account_supbscription_to_expire(employee_profile):

    # This will make the device to be unqualified
    s = Subscription.objects.get(
        employee_profile__reg_no=employee_profile.reg_no)
    """ 1 whole day late """
    s.due_date = timezone.now() + datetime.timedelta(days=0)
    s.save()

    # Confirm that the subscription has expired
    s = Subscription.objects.get(
        employee_profile__reg_no=employee_profile.reg_no)
    assert s.days_to_go == -1
    assert s.expired == True
