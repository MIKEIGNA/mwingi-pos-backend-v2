from django.urls import reverse
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from api.tests.sales.create_receipts_for_test import CreateReceiptsForTesting

from core.test_utils.create_store_models import create_new_category, create_new_tax
from core.test_utils.initial_user_data import CreateTimeVariablesMixin, InitialUserDataMixin

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.create_user import create_new_customer
from stores.models import StorePaymentMethod

from sales.models import Receipt, ReceiptLine, ReceiptPayment

from mysettings.models import MySetting
from products.models import Product


class ReceiptIndexViewTestCase(APITestCase, InitialUserDataMixin, CreateTimeVariablesMixin):

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

        # Increase user's store count
        self.manager_profile1.stores.add(self.store2)

        """
        Adds the following date variables into the class context:
        
         today, yesterday, two_weeks, three_weeks, last_month, last_month_but_1,
         last_month_but_2, last_120_days_date
        """
        self.insert_time_variables()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        """
        Creates 3 receipts for profile. manager ang cashier respectively. First 
        2 are in store1 while the last one is in store2
        """
        CreateReceiptsForTesting(
            self.top_profile1,
            self.manager_profile1, 
            self.cashier_profile1,
            self.store1, 
            self.store2
        ).create_receipts()

        self.pagination_users = [
            {
                'name': self.manager_profile1.get_full_name(), 
                'reg_no': self.manager_profile1.reg_no
            }, 
            {
                'name': self.user1.get_full_name(), 
                'reg_no': self.user1.reg_no
            }, 
            {
                'name': self.cashier_profile1.get_full_name(), 
                'reg_no': self.cashier_profile1.reg_no
            }, 
            {
                'name': self.cashier_profile2.get_full_name(), 
                'reg_no': self.cashier_profile2.reg_no
            }, 
            {
                'name': self.cashier_profile3.get_full_name(), 
                'reg_no': self.cashier_profile3.reg_no
            },
            {
                'name': self.manager_profile2.get_full_name(), 
                'reg_no': self.manager_profile2.reg_no
            }, 
            {
                'name': self.cashier_profile4.get_full_name(), 
                'reg_no': self.cashier_profile4.reg_no
            }
        ]

        # Get payments
        self.cash_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )

        self.mpesa_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.MPESA_TYPE
        )

        self.card_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CARD_TYPE
        )

        self.points_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.POINTS_TYPE
        )

        self.debt_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.DEBT_TYPE
        )

        self.other_pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.OTHER_TYPE
        )

        self.payment_list = [
            {
                'name': self.cash_pay_method.name, 
                'reg_no': self.cash_pay_method.reg_no
            }, 
            {
                'name': self.mpesa_pay_method.name, 
                'reg_no': self.mpesa_pay_method.reg_no
            }, 
            {
                'name': self.card_pay_method.name, 
                'reg_no': self.card_pay_method.reg_no
            }, 
            {
                'name': self.points_pay_method.name, 
                'reg_no': self.points_pay_method.reg_no
            }, 
            {
                'name': self.debt_pay_method.name, 
                'reg_no': self.debt_pay_method.reg_no
            }, 
            {
                'name': self.other_pay_method.name, 
                'reg_no': self.other_pay_method.reg_no
            }
        ]

    def test_view_returns_the_user_receipts_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(11):
            response = self.client.get(reverse('api:receipt_index'))
            self.assertEqual(response.status_code, 200)

        receipts = Receipt.objects.all().order_by('id')

        result = {
            'count': 4, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': receipts[3].customer_info,
                    'name': receipts[3].__str__(), 
                    'total_amount': f'{receipts[3].total_amount}', 
                    'is_refund': receipts[3].is_refund,
                    'sale_maker': receipts[3].user.get_full_name(),
                    'store_name': self.store2.name,  
                    'payment_type': receipts[3].get_payment_type(), 
                    'sale_type': receipts[3].get_sale_type(), 
                    'reg_no': receipts[3].reg_no, 
                    'creation_date': receipts[3].get_created_date(
                        self.user1.get_user_timezone()
                    )
                },
                {
                    'customer_info': receipts[2].customer_info,
                    'name': receipts[2].__str__(), 
                    'total_amount': f'{receipts[2].total_amount}', 
                    'is_refund': receipts[2].is_refund,
                    'sale_maker': receipts[2].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[2].get_payment_type(), 
                    'sale_type': receipts[2].get_sale_type(), 
                    'reg_no': receipts[2].reg_no, 
                    'creation_date': receipts[2].get_created_date(
                        self.user1.get_user_timezone()
                    )
                },
                {
                    'customer_info': receipts[1].customer_info,
                    'name': receipts[1].__str__(), 
                    'total_amount': f'{receipts[1].total_amount}', 
                    'is_refund': receipts[1].is_refund,
                    'sale_maker': receipts[1].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[1].get_payment_type(), 
                    'sale_type': receipts[1].get_sale_type(), 
                    'reg_no': receipts[1].reg_no, 
                    'creation_date': receipts[1].get_created_date(
                        self.user1.get_user_timezone()
                    )
                },
                {
                    'customer_info': receipts[0].customer_info,
                    'name': receipts[0].__str__(), 
                    'total_amount': f'{receipts[0].total_amount}', 
                    'is_refund': receipts[0].is_refund,
                    'sale_maker': receipts[0].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[0].get_payment_type(), 
                    'sale_type': receipts[0].get_sale_type(), 
                    'reg_no': receipts[0].reg_no, 
                    'creation_date': receipts[0].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:receipt_index'))
        self.assertEqual(response.status_code, 401)

    def test_view_can_only_show_results_for_employee_registerd_stores(self):

        # Decrease user's store count
        self.manager_profile1.stores.remove(self.store1, self.store2)

        response = self.client.get(reverse('api:receipt_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [], 
            'payments': self.payment_list,
            'users': [
                {
                    'name': 'Gucci Gucci', 
                    'reg_no': self.manager_profile1.reg_no
                }
            ], 
            'stores': []
        }

        self.assertEqual(response.data, result)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all receipt
        Receipt.objects.all().delete()

        pagination_page_size = settings.PRODUCT_POS_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        # Create and confirm receipts
        for i in range(model_num_to_be_created):
            Receipt.objects.create(
                user=self.top_profile1.user,
                store=self.store1,
                discount_amount=401.00,
                tax_amount=60.00,
                given_amount=2500.00,
                change_amount=500.00,
                subtotal_amount=2000,
                total_amount=1599.00,
                transaction_type=Receipt.MONEY_TRANS,
                payment_completed=True,
                local_reg_no=222
            )

        self.assertEqual(
            Receipt.objects.filter(user=self.user1).count(),
            model_num_to_be_created)  # Confirm models were created

    
        receipts = Receipt.objects.filter(user=self.user1).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        #with self.assertNumQueries(3):
        response = self.client.get(reverse('api:receipt_index'))
        self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/receipts/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # Check if all receipts are listed except the first one since it's in 
        # the next paginated page #
        i = 0
        for receipt in receipts[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], receipt.__str__())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], receipt.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)


        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:receipt_index') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/receipts/', 
            'results': [
                {
                    'customer_info': receipts[0].customer_info,
                    'name': receipts[0].__str__(), 
                    'total_amount': f'{receipts[0].total_amount}', 
                    'is_refund': receipts[0].is_refund,
                    'sale_maker': receipts[2].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[0].get_payment_type(),
                    'sale_type': receipts[0].get_sale_type(), 
                    'reg_no': receipts[0].reg_no, 
                    'creation_date': receipts[0].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_store(self):

        param = f'?store_reg_no={self.store2.reg_no}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        receipts = Receipt.objects.all().order_by('id')

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': receipts[3].customer_info,
                    'name': receipts[3].__str__(), 
                    'total_amount': f'{receipts[3].total_amount}', 
                    'is_refund': receipts[3].is_refund,
                    'sale_maker': receipts[3].user.get_full_name(),
                    'store_name': self.store2.name,  
                    'payment_type': receipts[3].get_payment_type(), 
                    'sale_type': receipts[3].get_sale_type(),
                    'reg_no': receipts[3].reg_no, 
                    'creation_date': receipts[3].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_user(self):

        param = f'?user_reg_no={self.manager_profile1.user.reg_no}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        receipts = Receipt.objects.all().order_by('id')

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': receipts[2].customer_info,
                    'name': receipts[2].__str__(), 
                    'total_amount': f'{receipts[2].total_amount}', 
                    'is_refund': receipts[2].is_refund,
                    'sale_maker': receipts[2].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[2].get_payment_type(), 
                    'sale_type': receipts[2].get_sale_type(),
                    'reg_no': receipts[2].reg_no, 
                    'creation_date': receipts[2].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_is_refund(self):

        param = f'?is_refund={True}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        receipts = Receipt.objects.all().order_by('id')

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': receipts[2].customer_info,
                    'name': receipts[2].__str__(), 
                    'total_amount': f'{receipts[2].total_amount}', 
                    'is_refund': receipts[2].is_refund,
                    'sale_maker': receipts[2].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[2].get_payment_type(), 
                    'sale_type': receipts[2].get_sale_type(),
                    'reg_no': receipts[2].reg_no, 
                    'creation_date': receipts[2].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_today_date(self):

        today_date = self.today.strftime("%Y-%m-%d")
        
        param = f'?date_after={today_date}&date_before={today_date}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        receipts = Receipt.objects.all().order_by('id')

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': receipts[1].customer_info,
                    'name': receipts[1].__str__(), 
                    'total_amount': f'{receipts[1].total_amount}', 
                    'is_refund': receipts[1].is_refund,
                    'sale_maker': receipts[1].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[1].get_payment_type(), 
                    'sale_type': receipts[1].get_sale_type(), 
                    'reg_no': receipts[1].reg_no, 
                    'creation_date': receipts[1].get_created_date(
                        self.user1.get_user_timezone()
                    )
                },
                {
                    'customer_info': receipts[0].customer_info,
                    'name': receipts[0].__str__(), 
                    'total_amount': f'{receipts[0].total_amount}', 
                    'is_refund': receipts[0].is_refund,
                    'sale_maker': receipts[0].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[0].get_payment_type(), 
                    'sale_type': receipts[0].get_sale_type(),
                    'reg_no': receipts[0].reg_no, 
                    'creation_date': receipts[0].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_this_month_date(self):

        first_day_this_month = self.first_day_this_month.strftime("%Y-%m-%d")
        tomorrow_date = self.tomorrow.strftime("%Y-%m-%d")
        
        param = f'?date_after={first_day_this_month}&date_before={tomorrow_date}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        receipts = Receipt.objects.all().order_by('id')

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'customer_info': receipts[2].customer_info,
                    'name': receipts[2].__str__(), 
                    'total_amount': f'{receipts[2].total_amount}', 
                    'is_refund': receipts[2].is_refund,
                    'sale_maker': receipts[2].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[2].get_payment_type(), 
                    'sale_type': receipts[2].get_sale_type(),
                    'reg_no': receipts[2].reg_no, 
                    'creation_date': receipts[2].get_created_date(
                        self.user1.get_user_timezone()
                    )
                },
                {
                    'customer_info': receipts[1].customer_info,
                    'name': receipts[1].__str__(), 
                    'total_amount': f'{receipts[1].total_amount}', 
                    'is_refund': receipts[1].is_refund,
                    'sale_maker': receipts[1].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[1].get_payment_type(), 
                    'sale_type': receipts[1].get_sale_type(),
                    'reg_no': receipts[1].reg_no, 
                    'creation_date': receipts[1].get_created_date(
                        self.user1.get_user_timezone()
                    )
                },
                {
                    'customer_info': receipts[0].customer_info,
                    'name': receipts[0].__str__(), 
                    'total_amount': f'{receipts[0].total_amount}', 
                    'is_refund': receipts[0].is_refund,
                    'sale_maker': receipts[0].user.get_full_name(),
                    'store_name': self.store1.name,  
                    'payment_type': receipts[0].get_payment_type(),
                    'sale_type': receipts[0].get_sale_type(), 
                    'reg_no': receipts[0].reg_no, 
                    'creation_date': receipts[0].get_created_date(
                        self.user1.get_user_timezone()
                    )
                }
            ],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ],
        }

        self.assertEqual(response.data, result)

    def test_view_can_handle_wrong_dates(self):

        date1 = self.last_month_but_2.strftime("%Y-%m-%d")
        date2 = self.last_120_days_date.strftime("%Y-%m-%d")
        
        param = f'?date_after={date1}&date_before={date2}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_filter_with_payment_type(self):

        receipts = Receipt.objects.all().order_by('id')

        # Cash
        param = f'?payment_type_reg_no={self.cash_pay_method.reg_no}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 3)

        self.assertEqual(response.data['results'][0]['store_name'], self.store1.name)
        self.assertEqual(response.data['results'][0]['reg_no'], receipts[2].reg_no)

        self.assertEqual(response.data['results'][1]['store_name'], self.store1.name)
        self.assertEqual(response.data['results'][1]['reg_no'], receipts[1].reg_no)

        self.assertEqual(response.data['results'][2]['store_name'], self.store1.name)
        self.assertEqual(response.data['results'][2]['reg_no'], receipts[0].reg_no)

        # Mpesa
        param = f'?payment_type_reg_no={self.mpesa_pay_method.reg_no}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['store_name'], self.store1.name)
        self.assertEqual(response.data['results'][0]['reg_no'], receipts[1].reg_no)

        # Card
        param = f'?payment_type_reg_no={self.card_pay_method.reg_no}'
        response = self.client.get(reverse('api:receipt_index') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['store_name'], self.store2.name)
        self.assertEqual(response.data['results'][0]['reg_no'], receipts[3].reg_no)
        

    def test_view_returns_empty_when_there_are_no_receipts(self):

        # First delete all receipts
        Receipt.objects.all().delete()

        response = self.client.get(reverse('api:receipt_index'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
            'payments': self.payment_list,
            'users': self.pagination_users,
            'stores': [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:receipt_index'))
        self.assertEqual(response.status_code, 401)


class ReceiptViewTestCase(APITestCase, InitialUserDataMixin):

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
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        self.create_receipt()

    def create_receipt(self):

        #Create a tax
        self.tax = create_new_tax(self.top_profile1, self.store1, 'Standard')

        #Create a category
        self.category = create_new_category(self.top_profile1, 'Hair')

        # Create a customer user
        self.customer = create_new_customer(self.top_profile1, 'chris')

        # Create a product
        product1 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Shampoo",
            price=2500,
            cost=1000,
            barcode='code123'
        )

        product2 = Product.objects.create(
            profile=self.top_profile1,
            tax=self.tax,
            category=self.category,
            name="Conditioner",
            price=2800,
            cost=1200,
            barcode='code123'
        )

        # Create receipt1
        self.receipt = Receipt.objects.create(
            user=self.top_profile1.user,
            store=self.store1,
            customer=self.customer,
            customer_info={
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            },
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=222,
            created_date_timestamp=1632748682
        )

        # Create receipt line1
        self.receiptline1 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=product1,
            product_info={'name': product1.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        self.receiptline2 =  ReceiptLine.objects.create(
            receipt=self.receipt,
            product=product2,
            product_info={'name': product2.name},
            price=2500,
            units=10
        )

        # Create payments
        pay_method = StorePaymentMethod.objects.get(
            profile=self.top_profile1,
            payment_type=StorePaymentMethod.CASH_TYPE
        )
        ReceiptPayment.objects.create(
            receipt=self.receipt,
            payment_method=pay_method,
            amount=self.receipt.subtotal_amount
        )

    def test_if_view_can_be_called_successefully(self):

        # Count Number of Queries #
        with self.assertNumQueries(6):
            response = self.client.get(
                reverse('api:receipt_view', args=(self.receipt.reg_no,)))
            self.assertEqual(response.status_code, 200)

        receipt = Receipt.objects.get(store=self.store1)

        result = {
            'customer_info': {
                'name': self.customer.name, 
                'reg_no': self.customer.reg_no
            }, 
            'name': receipt.__str__(), 
            'discount_amount': f'{receipt.discount_amount}',  
            'tax_amount': f'{receipt.tax_amount}', 
            'subtotal_amount': f'{receipt.subtotal_amount}', 
            'total_amount': f'{receipt.total_amount}', 
            'given_amount': f'{receipt.given_amount}', 
            'change_amount': f'{receipt.change_amount}',  
            'payment_completed': receipt.payment_completed, 
            'receipt_closed': receipt.receipt_closed, 
            'is_refund': receipt.is_refund, 
            'item_count': receipt.item_count,
            'local_reg_no': receipt.local_reg_no, 
            'reg_no': receipt.reg_no, 
            'creation_date': receipt.get_created_date(
                self.user1.get_user_timezone()
            ), 
            'created_date_timestamp': receipt.created_date_timestamp,
            'receipt_data': receipt.get_receipt_view_data()
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
            reverse('api:receipt_view', args=(self.receipt.reg_no,)))
        self.assertEqual(response.status_code, 401)

    def test_if_view_can_handle_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:receipt_view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_viewed_by_employee_in_the_same_store(self):

        # Remove user from store
        self.manager_profile1.stores.remove(self.store1)

        response = self.client.get(
            reverse('api:receipt_view', args=(self.receipt.reg_no,)))
       
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:receipt_view', args=(self.receipt.reg_no,)))
        self.assertEqual(response.status_code, 401)
