from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.create_store_models import create_new_tax
from core.test_utils.initial_user_data import InitialUserDataMixin
from core.test_utils.custom_testcase import APITestCase

from mysettings.models import MySetting
from stores.models import Tax

User = get_user_model()


class EpTaxPosIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.tax1 = create_new_tax(self.top_profile1, self.store1, 'Standard1')
        self.tax2 = create_new_tax(self.top_profile1, self.store1, 'Standard2')
        self.tax3 = create_new_tax(self.top_profile1, self.store2, 'Standard3')

        # Create taxes for top user 2
        self.tax4 = create_new_tax(self.top_profile2, self.store3, 'Standard4')


        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_the_user_models_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': 'Standard1', 
                    'rate': str(self.tax1.rate), 
                    'reg_no': self.tax1.reg_no
                },
                {
                    'name': 'Standard2', 
                    'rate': str(self.tax2.rate), 
                    'reg_no': self.tax2.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all taxes
        Tax.objects.all().delete()

        pagination_page_size = settings.LEAN_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        tax_names = []
        for i in range(model_num_to_be_created):
            tax_names.append(f'New Tax{i}')

        names_length = len(tax_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm taxes
        for i in range(names_length):
            create_new_tax(self.top_profile1, self.store1, tax_names[i])

        self.assertEqual(
            Tax.objects.filter(profile=self.top_profile1).count(),
            names_length)  # Confirm models were created

    
        taxes = Tax.objects.filter(profile=self.top_profile1).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,)))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 
            f'http://testserver/api/ep/pos/taxes/{self.store1.reg_no}/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all taxes are listed except the first one since it's in the next paginated page #
        i = 0
        for tax in taxes[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], tax.name)
            self.assertEqual(
                response_data_dict['results'][i]['rate'], str(tax.rate))
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], tax.reg_no)
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,))  + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': f'http://testserver/api/ep/pos/taxes/{self.store1.reg_no}/',
            'results': [
                {
                    'name': taxes[0].name,  
                    'rate': str(taxes[0].rate),  
                    'reg_no': taxes[0].reg_no,
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_tax_that_belong_to_store_only(self):

        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store2.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_tax_that_belong_to_user_store_only(self):

        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store3.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_taxes(self):

        # First delete all taxes
        Tax.objects.all().delete()

        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 200)

        result = {'count': 0, 'next': None, 'previous': None, 'results': []}

        self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
                reverse('api:ep_pos_tax_index', args=(self.store1.reg_no,)))
        self.assertEqual(response.status_code, 401)

