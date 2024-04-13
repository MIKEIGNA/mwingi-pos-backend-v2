from dateutil.relativedelta import relativedelta
import datetime

from django.utils import timezone

from core.test_utils.custom_testcase import TestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from profiles.models import Profile
from mylogentries.models import PaymentLog

from billing.utils.payment_utils.price_gen import PriceGeneratorClass
from billing.models import Subscription, Payment


"""
=========================== PaymentLog ===================================
"""

class PaymentTestCase(TestCase, InitialUserDataMixin):
    def setUp(self):
        """
        This function is defined in the 'InitialUserDataMixin' mixin
        
        It creates 2 top users, 3 stores and 5 employee users as follows

        * Top User 1 assets:
            self.user1 - top user 
            self.top_profile1 - Profile for top user -- (john@gmail.com)

            - self.store1 - Store -- (Computer Store) 
                self.manager_profile1 - Manger Employee profile for top user 1 -- (gucci@gmail.com)

                self.cashier_profile1 - Cashier Employee profile under manager profile 1 -- (kate@gmail.com)
                self.cashier_profile2 - Cashier Employee profile under manager profile 1 -- (james@gmail.com)
                self.cashier_profile3 - Cashier Employee profile under manager profile 1 -- (ben@gmail.com)

            - self.store2 - Store -- (Cloth Store)
                self.manager_profile2 - Manger Employee profile for top user 1 -- (lewis@gmail.com)

                self.cashier_profile4 - Cashier Employee profile under manager profile 2 -- (hugo@gmail.com)


        * Top User 2 assets:
            self.user2 - top user
            self.top_profile2 - Profile for top user-- (jack@gmail.com)

            - self.store3 - Store -- (Toy Store)
                self.manager_profile3 - Manger Employee profile for top user 2 -- (cristiano@gmail.com):

                self.cashier_profile5 - Cashier Employee profile under manager profile 3 -- (juliet@gmail.com)
        """

        self.create_initial_user_data_with_no_payment_history()

    def create_payment_log_and_payment(self):

        duration = 1
        one_month_price = PriceGeneratorClass.account_price_calc(duration)

        profile = Profile.objects.get(user__email='john@gmail.com')

        payment_log = PaymentLog.objects.create(
            amount=one_month_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=payment_log,
            amount=one_month_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

    def test_payment_verbose_names(self):

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        payment = Payment.objects.get(
            account_reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(payment._meta.get_field(
            'amount').verbose_name, 'amount')
        self.assertEqual(payment._meta.get_field(
            'payed_date').verbose_name, 'payed date')
        self.assertEqual(payment._meta.get_field(
            'parent_reg_no').verbose_name, 'parent reg no')
        self.assertEqual(payment._meta.get_field(
            'account_reg_no').verbose_name, 'account reg no')
        self.assertEqual(payment._meta.get_field(
            'account_type').verbose_name, 'account type')
        self.assertEqual(payment._meta.get_field(
            'duration').verbose_name, 'duration')

    def test_payment_existence_after_it_has_been_created(self):

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        duration = 1
        one_month_price = PriceGeneratorClass.account_price_calc(duration)

        payment = Payment.objects.get(
            account_reg_no=self.cashier_profile1.reg_no)
        payment_log = PaymentLog.objects.get(
            reg_no=self.cashier_profile1.reg_no)

        # Payment fields

        # Ensure a Payment has the right fields after it has been created

        self.assertEqual(payment.paymentlog, payment_log)
        self.assertEqual(payment.amount, one_month_price)
        self.assertEqual((payment.payed_date).strftime(
            "%B, %d, %Y"), (timezone.now()).strftime("%B, %d, %Y"))
        self.assertEqual(payment.parent_reg_no, 0)
        self.assertEqual(payment.account_reg_no, self.cashier_profile1.reg_no)
        self.assertEqual(payment.account_type, 'team')
        self.assertEqual(payment.duration, 1)

    def test__str__method(self):

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(
            str(p), 'Pay - {}'.format(self.cashier_profile1.reg_no))

    def test_get_payed_date_method(self):
        # Confirm that get_payed_date_method returns payed_date
        # in local time

        now = timezone.now() + datetime.timedelta(hours=3)
        local_date = (now).strftime("%B, %d, %Y, %I:%M:%p")

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(p.get_payed_date(), local_date)

    def test_get_account_reg_no_method(self):

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        payment = Payment.objects.get(
            account_reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(payment.get_account_reg_no(),
                         self.cashier_profile1.reg_no)

    def test_get_admin_url_method(self):

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        payment = Payment.objects.get(
            account_reg_no=self.cashier_profile1.reg_no)
        payment_log = PaymentLog.objects.get(
            reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(
            payment.get_admin_url(),
            f'/magnupe/mylogentries/paymentlog/{payment_log.id}/change/')

    def test_show_paymentlog_id_link_method(self):

        # Create basic payment_log an dpayment
        self.create_payment_log_and_payment()

        payment = Payment.objects.get(
            account_reg_no=self.cashier_profile1.reg_no)
        payment_log = PaymentLog.objects.get(
            reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(
            payment.show_paymentlog_id_link(),
            f'<a href="http://127.0.0.1:8000/magnupe/mylogentries/paymentlog/{payment_log.id}/change/">mpesa</a>')

    def test_update_account_subscription_signal_for_1_month(self):

        # update_account_subscription signal for 1 month

        # Ensure that when Payment is created, it passes it's payed_date to subscription's
        # last_payment_date and calculates the right due_date
        duration = 1
        one_month_price = PriceGeneratorClass.account_price_calc(duration)

        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_month_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_month_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        next_pay_date = (p.payed_date + relativedelta(months=1)
                         ).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, next_pay_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 28 and 31#
        self.assertTrue(s.days_to_go > 28)
        self.assertTrue(s.days_to_go < 31)

        # Confirm that update_account_subscription_method only gets called during payment creation #
        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        p.save()

        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(s_due_date, next_pay_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 28 and 31#
        self.assertTrue(s.days_to_go > 28)
        self.assertTrue(s.days_to_go < 31)

    def test_update_account_subscription_signal_for_1_month_when_due_date_has_passed(self):

        # update_account_subscription signal for 1 month

        # Ensure that when Payment is created, subscription is updated even if
        # the due_date was negative

        # -1 days to go
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() - datetime.timedelta(days=5)
        s.save()

        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(s.days_to_go, -6)
        self.assertEqual(s.expired, True)

        duration = 1
        one_month_price = PriceGeneratorClass.account_price_calc(duration)

        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_month_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_month_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        next_pay_date = (p.payed_date + relativedelta(months=1)
                         ).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, next_pay_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 28 and 31#
        self.assertTrue(s.days_to_go > 28)
        self.assertTrue(s.days_to_go < 31)

        # Confirm that update_account_subscription_method only gets called during payment creation #
        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        p.save()

        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        self.assertEqual(s_due_date, next_pay_date)
        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 28 and 31#
        self.assertTrue(s.days_to_go > 28)
        self.assertTrue(s.days_to_go < 31)

    def test_update_account_subscription_signal_with_two_1_month_payments(self):

        # update_account_subscription signal with two 1 month payments

        # Ensure when First Payment is created, it passes it's payed_date to subscription's
        # last_payment_date and calculates the right due_date
        duration = 1
        one_month_price = PriceGeneratorClass.account_price_calc(duration)

        # First payment#
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_month_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_month_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        correct_payed_date = (
            p.payed_date + relativedelta(months=1)).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, correct_payed_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 28 an 31#
        self.assertTrue(s.days_to_go > 28)
        self.assertTrue(s.days_to_go < 31)

        old_due_date = s.due_date

        # Ensure when second payment is made while the subscription is still active,
        # the due_date is increased by the right values

        # Second payment#
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_month_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_month_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        self.assertEqual(s_due_date, (old_due_date +
                         relativedelta(months=1)).strftime("%B, %d, %Y"))

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 55 an 63#
        self.assertTrue(s.days_to_go > 55)
        self.assertTrue(s.days_to_go < 63)

    # 6 Months #
    def test_update_account_subscription_signal_for_6_months(self):

        # update_account_subscription signal for 6 month

        # Ensure that when Payment is created, it passes it's payed_date to subscription's
        # last_payment_date and calculates the right due_date
        duration = 6
        six_months_price = PriceGeneratorClass.account_price_calc(duration)

        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=six_months_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=six_months_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        correct_payed_date = (
            p.payed_date + relativedelta(months=6)).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, correct_payed_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 180 an 185
        self.assertTrue(s.days_to_go >= 180)
        self.assertTrue(s.days_to_go < 185)

    def test_update_account_subscription_signal_with_two_6_months_payments(self):

        # update_account_subscription signal with two 6 months payments

        # Ensure when First Payment is created, it passes it's payed_date to subscription's
        # last_payment_date and calculates the right due_date

        duration = 6
        six_months_price = PriceGeneratorClass.account_price_calc(duration)

        # First payment#
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=six_months_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=six_months_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        correct_payed_date = (
            p.payed_date + relativedelta(months=6)).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, correct_payed_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 180 an 185

        self.assertTrue(s.days_to_go >= 180)
        self.assertTrue(s.days_to_go < 185)

        old_due_date = s.due_date

        # Ensure when second payment is made while the subscription is still active,
        # the due_date is increased by the right values

        # Second payment#
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=six_months_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=six_months_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        self.assertEqual(s_due_date, (old_due_date +
                         relativedelta(months=6)).strftime("%B, %d, %Y"))

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 360 an 368
        self.assertTrue(s.days_to_go >= 360)
        self.assertTrue(s.days_to_go < 368)

    # 12 Months #

    def test_update_account_subscription_signal_for_12_months(self):

        # update_account_subscription signal for 12 month

        # Ensure that when Payment is created, it passes it's payed_date to subscription's
        # last_payment_date and calculates the right due_date
        duration = 12
        one_year_price = PriceGeneratorClass.account_price_calc(duration)

        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_year_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_year_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        correct_payed_date = (
            p.payed_date + relativedelta(months=12)).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, correct_payed_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 363 an 368
        self.assertTrue(s.days_to_go > 363)
        self.assertTrue(s.days_to_go < 368)

    def test_update_account_subscription_signal_with_two_12_months_payments(self):

        # update_account_subscription signal with two 12 months payments

        # Ensure when First Payment is created, it passes it's payed_date to subscription's
        # last_payment_date and calculates the right due_date

        duration = 12
        one_year_price = PriceGeneratorClass.account_price_calc(duration)

        # First payment#
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_year_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_year_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        p = Payment.objects.get(account_reg_no=self.cashier_profile1.reg_no)
        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        pre_last_payment_date = s.last_payment_date

        self.assertEqual((p.payed_date).strftime("%B, %d, %Y"),
                         (pre_last_payment_date).strftime("%B, %d, %Y"))

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        correct_payed_date = (
            p.payed_date + relativedelta(months=12)).strftime("%B, %d, %Y")

        self.assertEqual(s_due_date, correct_payed_date)

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 360 an 368
        self.assertTrue(s.days_to_go > 363)
        self.assertTrue(s.days_to_go < 368)

        old_due_date = s.due_date

        # Ensure when second payment is made while the subscription is still active,
        # the due_date is increased by the right values

        # Second payment#
        profile = Profile.objects.get(user__email='john@gmail.com')
        self.payment_log = PaymentLog.objects.create(
            amount=one_year_price,
            payment_method='mpesa',
            payment_type='single {}'.format('team'),
            email=profile.user.email,
            reg_no=self.cashier_profile1.reg_no,
            duration=duration,
        )

        Payment.objects.create(
            paymentlog=self.payment_log,
            amount=one_year_price,
            account_reg_no=self.cashier_profile1.reg_no,
            duration=duration,
            parent_reg_no=0,
            account_type='team',
        )

        s = Subscription.objects.get(
            employee_profile__reg_no=self.cashier_profile1.reg_no)

        s_due_date = (s.due_date).strftime("%B, %d, %Y")
        self.assertEqual(s_due_date, (old_due_date +
                         relativedelta(months=12)).strftime("%B, %d, %Y"))

        # Due to months with 28, 29, 30 and 31 days, we cant be sure
        # of days_to_go value but we know the range is btwn 720 an 730
        self.assertTrue(s.days_to_go > 725)
        self.assertTrue(s.days_to_go < 735)
