import datetime

from django.utils import timezone

from core.test_utils.create_store_models import create_new_store
from core.test_utils.create_user import (
    create_new_user,
    create_new_manager_user, 
    create_new_cashier_user
)

from core.test_utils.make_payment import make_payment
from core.time_utils.time_localizers import utc_to_local_datetime

from profiles.models import Profile, EmployeeProfile


class InitialUserDataMixin:

    def create_initial_user_data(self):
        self.generate_initial_user_data(complete_payment=True)

    def create_initial_user_data_with_no_payment_history(self):
        self.generate_initial_user_data(complete_payment=False)

    def create_initial_user_data_with_superuser(self):
        return self.generate_initial_user_data(include_superuser=True)

    def create_initial_user_data_with_superuser_with_no_payment_history(self):
        return self.generate_initial_user_data(include_superuser=True, complete_payment=False)
  
    def generate_initial_user_data(self, include_superuser=False, complete_payment=True):
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
        
        """********* Create top user 1 assets """
        if include_superuser:
            # Create superuser top user 1 assets
            self.user1 = create_new_user('super')

        else:
            # Create top user 1 assets
            self.user1 = create_new_user('john')
        
        self.top_profile1 = Profile.objects.get(user__email='john@gmail.com')

        self.create_create_top_user1_and_its_assets(complete_payment)

        """********* Create top user 2 assets """
        self.user2 = create_new_user('jack')
        
        self.top_profile2 = Profile.objects.get(user__email='jack@gmail.com')

        self.create_create_top_user2_and_its_assets(complete_payment)

    def create_create_top_user1_and_its_assets(self, complete_payment):
        """
        Creates 2 stores for top user 1.
        Store 1 has 1 manager and 3 cashiers
        Store 2 has 1 manager and 1 cashier
        """

        ############ Create store1 with 1 manager and 3 cashiers
        #####################################################
        self.store1 = create_new_store(self.top_profile1, 'Computer Store')

        # *** Create a manager 
        # Create a manager user1
        create_new_manager_user("gucci", self.top_profile1, self.store1)
        self.manager_profile1 = EmployeeProfile.objects.get(user__email='gucci@gmail.com')

        if complete_payment:
            # Make a single payment so that the manager will be qualified
            make_payment(self.user1, self.manager_profile1.reg_no, 1)
        
            manager1 = EmployeeProfile.objects.get(reg_no=self.manager_profile1.reg_no)
            self.assertEqual(manager1.is_employee_qualified(), True)
        
        # *** Create cashiers        
        # Create a cashier user 1
        create_new_cashier_user("kate", self.top_profile1, self.store1)
        self.cashier_profile1 = EmployeeProfile.objects.get(user__email='kate@gmail.com')
        
        if complete_payment:
            # Make a single payment so that the cashier will be qualified
            make_payment(self.user1, self.cashier_profile1.reg_no, 1)
        
            cashier1 = EmployeeProfile.objects.get(reg_no=self.cashier_profile1.reg_no)
            self.assertEqual(cashier1.is_employee_qualified(), True)
            
        # Create a cashier user 2
        create_new_cashier_user("james", self.top_profile1, self.store1)
        self.cashier_profile2 = EmployeeProfile.objects.get(user__email='james@gmail.com')
        
        if complete_payment:
            # Make a single payment so that the the cashier will be qualified
            make_payment(self.user1, self.cashier_profile2.reg_no, 1)
        
            cashier2 = EmployeeProfile.objects.get(reg_no=self.cashier_profile2.reg_no)
            self.assertEqual(cashier2.is_employee_qualified(), True)
        
        # Create a cashier user3
        create_new_cashier_user("ben", self.top_profile1, self.store1)
        self.cashier_profile3 = EmployeeProfile.objects.get(user__email='ben@gmail.com')
        
        if complete_payment:
            # Make a single payment so that the the cashier will be qualified
            make_payment(self.user1, self.cashier_profile3.reg_no, 1)
        
            cashier3 = EmployeeProfile.objects.get(reg_no=self.cashier_profile3.reg_no)
            self.assertEqual(cashier3.is_employee_qualified(), True)

        
        ############ Create store2 with 1 manager and cashier
        #####################################################
        self.store2 = create_new_store(self.top_profile1, 'Cloth Store')

        
        # *** Create a manager 
        #Create a manager user 2
        create_new_manager_user("lewis", self.top_profile1, self.store2)
        self.manager_profile2 = EmployeeProfile.objects.get(user__email='lewis@gmail.com')

        if complete_payment:
            # Make a single payment so that the manager will be qualified
            make_payment(self.user1, self.manager_profile2.reg_no, 1)
        
            manager2 = EmployeeProfile.objects.get(reg_no=self.manager_profile2.reg_no)
            self.assertEqual(manager2.is_employee_qualified(), True)

        
        create_new_cashier_user("hugo", self.top_profile1, self.store2)
        self.cashier_profile4 = EmployeeProfile.objects.get(user__email='hugo@gmail.com')
        
        # *** Create a cashier
        #Create a cashier user 4
        if complete_payment:
            # Make a single payment so that the the cashier will be qualified
            # to have locations
            make_payment(self.user1, self.cashier_profile4.reg_no, 1)
        
            cashier4 = EmployeeProfile.objects.get(reg_no=self.cashier_profile4.reg_no)
            self.assertEqual(cashier4.is_employee_qualified(), True)
        
    def create_create_top_user2_and_its_assets(self, complete_payment):
        """
        Creates 1 stores for top user 2.

        Store 1 has 1 manager and 1 cashier
        """

        ############ Create store3 and it's assets
        #####################################################
        self.store3 = create_new_store(self.top_profile2, 'Toy Store')


        # *** Create a manager 
        # Create a manager user 3
        create_new_manager_user("cristiano", self.top_profile2, self.store3)
        self.manager_profile3 = EmployeeProfile.objects.get(user__email='cristiano@gmail.com')

        if complete_payment:
            # Make a single payment so that the manager will be qualified
            make_payment(self.user1, self.manager_profile3.reg_no, 1)
        
            manager3 = EmployeeProfile.objects.get(reg_no=self.manager_profile3.reg_no)
            self.assertEqual(manager3.is_employee_qualified(), True)



        # *** Create a cashier
        #Create a cashier user 5
        create_new_cashier_user("juliet", self.top_profile2, self.store3)
        self.cashier_profile5 = EmployeeProfile.objects.get(user__email='juliet@gmail.com')

        #Create a cashier user 3
        if complete_payment:
            # Make a single payment so that the the cashier will be qualified
            # to have locations
            make_payment(self.user1, self.cashier_profile5.reg_no, 1)
        
            cashier5 = EmployeeProfile.objects.get(reg_no=self.cashier_profile5.reg_no)
            self.assertEqual(cashier5.is_employee_qualified(), True)



        


class FilterDatesMixin:
    
    def create_filter_dates(self):
        # Change time from utc to local
        now = utc_to_local_datetime(timezone.now())
        
        # Generates today's date
        # For example if today is February, 09, 2020, the generated today's date will be
        # February, 09, 2020, 02:00:AM
        self.today = now.replace(hour=2, minute=0, second=0, microsecond=0)
        
        self.yesterday = self.today + datetime.timedelta(days=-1)

        # We make sure random_date_for_this_month is far as possible from today's date
        if self.today.day > 15:
            self.random_date_for_this_month = self.today.replace(day=5)
        else:
            self.random_date_for_this_month = self.today.replace(day=25)

        first_day_this_month = self.today.replace(day=1)
        self.last_60_days_date = first_day_this_month - datetime.timedelta(days=60)       
        


class CreateTimeVariablesMixin:
    
    def insert_time_variables(self):
        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """


        # Get the time now (Don't turn it into local)
        now = timezone.now()
        
        # Make time aware
        self.today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        #print(dir(self.today))
        #print(self.today.strftime("%B, %d, %Y"))
        #print(self.today.strftime("%Y-%m-%d"))

        self.first_day_this_month = self.today.replace(day=1)

        self.next_month_start = self.first_day_this_month + datetime.timedelta(days=30)

        last_month_end = self.first_day_this_month - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        last_month_but_1_end = last_month_start - datetime.timedelta(days=1)
        last_month_but_1_start = last_month_but_1_end.replace(day=1)
        
        last_month_but_2_end = last_month_but_1_start - datetime.timedelta(days=1)
        last_month_but_2_start = last_month_but_2_end.replace(day=1)

        self.tomorrow = self.today + datetime.timedelta(days=+1)

        self.yesterday = self.today + datetime.timedelta(days=-1)

        self.two_weeks = self.today - datetime.timedelta(days=12)

        self.three_weeks = self.today - datetime.timedelta(days=18)

        self.last_month = last_month_start + datetime.timedelta(days=1)
        
        self.last_month_but_1 = last_month_but_1_start + datetime.timedelta(days=1)

        self.last_month_but_2 = last_month_but_2_start + datetime.timedelta(days=1)

        self.last_120_days_date = self.first_day_this_month - datetime.timedelta(days=120)

