import time
import datetime

from django.utils import timezone

from core.test_utils.custom_testcase import TestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from mysettings.models import MySetting
from billing.models import Subscription

from ..tasks import midnight_tasks

class MidnightTasksTestCase(TestCase, InitialUserDataMixin):
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
        
        self.create_initial_user_data()
        
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()
            
        # Get employee_profile1 (Belongs to top_profile1)
        self.assertEqual(self.cashier_profile1.is_employee_qualified(), True)
        
    def test_if_midnight_tasks_will_update_subscription_to_expired_when_time_is_up(self):

        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        
        # Set 1 secnod to go before expiry
        days =  datetime.timedelta(seconds=1)
        
        s.last_payment_date = timezone.now() - datetime.timedelta(days=1)
        s.due_date = timezone.now() + days
        s.save()

        # Confirm the subscription has not expired
        self.assertEqual(s.expired, False)

        # We sleep for 2 seconds to allow the 1 second date time to pass
        time.sleep(2)

        # Update subscriptions
        midnight_tasks()

       # Confirm the subscription was changed to expired
        s = Subscription.objects.get(employee_profile__reg_no=self.cashier_profile1.reg_no)
        self.assertEqual(s.expired, True)
        
