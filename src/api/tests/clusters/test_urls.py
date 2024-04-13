from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from clusters.models import StoreCluster
from core.test_utils.create_store_models import create_new_store

from core.test_utils.create_user import create_new_user
from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from mysettings.models import MySetting
from profiles.models import Profile

class LeanStoreClusterIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.magadi_cluster = StoreCluster.objects.create(
            name='Magadi',
            profile=self.top_profile1
        )

        self.kajiado_cluster = StoreCluster.objects.create(
            name='Kajiado',
            profile=self.top_profile1
        )

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_models_correclty(self):

        clusters = StoreCluster.objects.all().order_by('name')

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(
            reverse('api:store-cluster-index-lean'))
        self.assertEqual(response.status_code, 200)

        results = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.kajiado_cluster.name, 
                    'reg_no': clusters[0].reg_no
                }, 
                {
                    'name': self.magadi_cluster.name, 
                    'reg_no': clusters[1].reg_no
                }
            ]
        }


        self.assertEqual(response.data, results)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all models
        StoreCluster.objects.all().delete()

        page_size = 50
        model_num_to_be_created = page_size+1

        # Create and confirm spot check logs
        for i in range(model_num_to_be_created):
            StoreCluster.objects.create(
                name = f'Cluster {i}',
                profile=self.top_profile1
            )

        self.assertEqual(
            StoreCluster.objects.all().count(),
            model_num_to_be_created
        )  # Confirm models were created

        models = StoreCluster.objects.all().order_by('-name')

        # ######### Test first paginated page - list ######### # 

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(reverse('api:store-cluster-index-lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/clusters/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all store proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for model in models[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], model.reg_no)
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, page_size)

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:store-cluster-index-lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

    
        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/clusters/lean/',
            'results': [
                {
                    'name': models[0].name, 
                    'reg_no': models[0].reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_models(self):

        # First delete all models
        StoreCluster.objects.all().delete()

        response = self.client.get(
            reverse('api:store-cluster-index-lean'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
        }

        self.assertEqual(response.data, result)

    def test_view_can_only_be_viewed_by_owner(self):

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(
            reverse('api:store-cluster-index-lean'))
        self.assertEqual(response.status_code, 200)

        results = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, results)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:store-cluster-index-lean'))
        self.assertEqual(response.status_code, 401)


class StoreClusterIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.magadi_cluster = StoreCluster.objects.create(
            name='Magadi',
            profile=self.top_profile1
        )

        self.kajiado_cluster = StoreCluster.objects.create(
            name='Kajiado',
            profile=self.top_profile1
        )

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_models_correclty(self):

        clusters = StoreCluster.objects.all().order_by('name')

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(
            reverse('api:store-cluster-index'))
        self.assertEqual(response.status_code, 200)

        results = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.kajiado_cluster.name, 
                    'stores': clusters[0].get_registered_cluster_stores_data(),
                    'reg_no': clusters[0].reg_no
                }, 
                {
                    'name': self.magadi_cluster.name, 
                    'stores': clusters[1].get_registered_cluster_stores_data(),
                    'reg_no': clusters[1].reg_no
                }
            ]
        }

        self.assertEqual(response.data, results)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all models
        StoreCluster.objects.all().delete()

        page_size = 50
        model_num_to_be_created = page_size+1

        # Create and confirm spot check logs
        for i in range(model_num_to_be_created):
            StoreCluster.objects.create(
                name = f'Cluster {i}',
                profile=self.top_profile1
            )

        self.assertEqual(
            StoreCluster.objects.all().count(),
            model_num_to_be_created
        )  # Confirm models were created

        models = StoreCluster.objects.all().order_by('-name')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(54):
            response = self.client.get(reverse('api:store-cluster-index'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/clusters/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(
            len(response_data_dict['results']), page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all store proifiles are listed except the first one since it's in the next paginated page #
        i = 0
        for model in models[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], model.reg_no)
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, page_size)

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:store-cluster-index') + '?page=2')
        self.assertEqual(response.status_code, 200)

    
        result = {
            'count': model_num_to_be_created,
            'next': None,
            'previous': 'http://testserver/api/clusters/',
            'results': [
                {
                    'name': models[0].name, 
                    'stores': models[0].get_registered_cluster_stores_data(),
                    'reg_no': models[0].reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_models(self):

        # First delete all models
        StoreCluster.objects.all().delete()

        response = self.client.get(
            reverse('api:store-cluster-index'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': [],
        }

        self.assertEqual(response.data, result)

    def test_view_can_only_be_viewed_by_owner(self):

        # Login an employee user
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(
            reverse('api:store-cluster-index'))
        self.assertEqual(response.status_code, 200)

        results = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, results)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:store-cluster-index'))
        self.assertEqual(response.status_code, 401)



class StoreClusterCreateViewTestCase(APITestCase):

    def setUp(self):

        # Create a user with email john@gmail.com
        self.user = create_new_user('john')

        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create 2 stores and 2 products
        self.create_test_models()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_test_models(self):

        self.store1 = create_new_store(self.profile, 'Store1')
        self.store2 = create_new_store(self.profile, 'Store2')
        self.store3 = create_new_store(self.profile, 'Store3')

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            'name': 'Magadi',
            'stores_info': [
                {
                    'reg_no': self.store1.reg_no
                },
                {
                    'reg_no': self.store2.reg_no
                } 
            ]
        }

        return payload

    def test_if_view_creates_the_model_correctly(self):

        payload = self.get_premade_payload()

        response = self.client.post(
            reverse('api:store-cluster-create'), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        cluster = StoreCluster.objects.get()

        self.assertEqual(cluster.name, 'Magadi')
        self.assertEqual(
            list(cluster.stores.all().values_list('id', flat=True)),
            [self.store1.id, self.store2.id]
        )
        self.assertTrue(cluster.reg_no > 100000)  # Check if we have a valid reg_no

        self.assertEqual(str(cluster), cluster.name)

    def test_view_when_stores_info_is_empty(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = []

        response = self.client.post(
            reverse('api:store-cluster-create'), 
            payload
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data, 
            {'stores_info': ['This list may not be empty.']}
        )

        # Check if no model was created
        self.assertEqual(StoreCluster.objects.all().count(), 0)

    def test_view_when_stores_info_as_non_existing_stores(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = [
            {
                'reg_no': 1111
            },
            {
                'reg_no': 2222
            } 
        ] 

        response = self.client.post(
            reverse('api:store-cluster-create'), 
            payload
        )
        self.assertEqual(response.status_code, 200)

        cluster = StoreCluster.objects.get()

        self.assertEqual(cluster.name, 'Magadi')
        self.assertEqual(
            list(cluster.stores.all().values_list('id', flat=True)),
            []
        )

class StoreClusterViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Create test models
        self.create_test_models()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_test_models(self):

        # Create stores
        self.store1 = create_new_store(self.top_profile1, 'Store1')
        self.store2 = create_new_store(self.top_profile1, 'Store2')
        self.store3 = create_new_store(self.top_profile1, 'Store3')
        self.store4 = create_new_store(self.top_profile1, 'Store4')

        # Create cluster
        self.cluster = StoreCluster.objects.create(
           name='Magadi',
           profile=self.top_profile1
        )

        self.cluster.stores.add(self.store1, self.store2)

    def test_view_can_be_called_successefully(self):

        cluster = StoreCluster.objects.get()

        # Count Number of Queries #
        #with self.assertNumQueries(5):
        response = self.client.get(
            reverse('api:store-cluster-view', 
            args=(cluster.reg_no,))
        )
        self.assertEqual(response.status_code, 200)

        results = {
            'name': self.cluster.name, 
            'available_stores': cluster.get_available_stores_data(), 
            'cluster_stores': cluster.get_registered_cluster_stores_data(), 
            'reg_no': cluster.reg_no
        }

        self.assertEqual(response.data, results)

    def test_view_can_only_be_viewed_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        cluster = StoreCluster.objects.get()

        response = self.client.get(
            reverse('api:store-cluster-view', 
            args=(cluster.reg_no,))
        )
        self.assertEqual(response.status_code, 404)

    def test_view_can_handle_a_wrong_reg_no(self):

        response = self.client.get(
            reverse('api:store-cluster-view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(
            reverse('api:store-cluster-view', 
            args=(self.cluster.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

class StoreClusterEditViewForEditingTestCase(APITestCase, InitialUserDataMixin):

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

        # Create test models
        self.create_test_models()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def create_test_models(self):

        # Create stores
        self.store1 = create_new_store(self.top_profile1, 'Store1')
        self.store2 = create_new_store(self.top_profile1, 'Store2')
        self.store3 = create_new_store(self.top_profile1, 'Store3')
        self.store4 = create_new_store(self.top_profile1, 'Store4')

        # Create cluster
        self.cluster = StoreCluster.objects.create(
           name='Magadi',
           profile=self.top_profile1
        )

        self.cluster.stores.add(self.store1, self.store2)   

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """
        payload = {
            'name': 'New name',
            'stores_info': [
                {
                    'reg_no': self.store1.reg_no
                } 
            ]
        }

        return payload

    def test_view_can_edit_a_cluster_name(self):

        cluster = StoreCluster.objects.get()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:store-cluster-view', args=(self.cluster.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        cluster = StoreCluster.objects.get()

        # Confirm name was edited
        self.assertEqual(cluster.name, payload['name'])

    def test_view_can_remove_a_store_from_cluster(self):

        # Confirm stores counts
        cluster = StoreCluster.objects.get()
        self.assertEqual(cluster.stores.all().count(), 2)

        payload = self.get_premade_payload()
        payload['stores_info'] = []

        response = self.client.put(
            reverse('api:store-cluster-view', args=(self.cluster.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(cluster.stores.all().count(), 0)

    def test_view_can_add_a_store_and_remove_another_at_the_same_time(self):

        # Confirm stores counts
        cluster = StoreCluster.objects.get()
        self.assertEqual(cluster.stores.all().count(), 2)

        self.assertEqual(
            list(cluster.stores.all().values_list('id', flat=True)),
            [self.store1.id, self.store2.id]
        )

        payload = self.get_premade_payload()
        payload['stores_info'] = [
            {
                'reg_no': self.store3.reg_no
            },
            {
                'reg_no': self.store4.reg_no
            } 
        ]

        response = self.client.put(
            reverse('api:store-cluster-view', args=(self.cluster.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 200)

        # Confirm stores addition and remove
        cluster = StoreCluster.objects.get()
        self.assertEqual(cluster.stores.all().count(), 2)

        self.assertEqual(
            list(cluster.stores.all().values_list('id', flat=True)),
            [self.store3.id, self.store4.id]
        )

    def test_view_can_handle_a_wrong_store_reg_no(self):

        payload = self.get_premade_payload()
        payload['stores_info']= [{'reg_no': self.store2.reg_no},]

        response = self.client.put(
            reverse('api:store-cluster-view', args=(111111111,)), payload
        )
        self.assertEqual(response.status_code, 404)

    def test_view_wont_accept_an_empty_store_info(self):

        payload = self.get_premade_payload()
        payload['stores_info'] = ''

        response = self.client.put(
            reverse('api:store-cluster-view', args=(self.cluster.reg_no,)), payload
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            response.data, 
            {'stores_info': ['Expected a list of items but got type "str".']}
        )

        # Confirm truck was not changed
        cluster = StoreCluster.objects.get()
        self.assertEqual(cluster.stores.all().count(), 2)

    def test_if_view_cant_be_edited_with_a_wrong_stores_reg_no(self):

        wrong_stores_reg_nos = [
            '1010',  # Wrong reg no
            'aaaa',  # Non numeric
            #3333333333333333333333333333333333333333333333  # Extremely long
        ]

        i = 0
        for reg_no in wrong_stores_reg_nos:

            payload = self.get_premade_payload()
            payload['stores_info'][0]['reg_no'] = reg_no

            response = self.client.put(reverse(
                'api:store-cluster-view', 
                args=(self.cluster.reg_no,)), 
                payload
            )
            self.assertEqual(response.status_code, 400)

            if i == 0:
                self.assertEqual(
                    response.data, {'stores_info': 'You provided wrong stores.'})

            elif i == 1:
                self.assertEqual(
                    response.data,
                    {'stores_info': {
                        0: {'reg_no': ['A valid integer is required.']}}}
                )

            else:
                self.assertEqual(
                    response.data,
                    {'stores_info': {
                        0: {'reg_no': ['You provided wrong stores']}}}
                )

            i += 1

        # Confirm truck was not changed
        cluster = StoreCluster.objects.get()
        self.assertEqual(cluster.stores.all().count(), 2)
    
    def test_if_view_can_handle_a_wrong_product_reg_no(self):

        payload = self.get_premade_payload()

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        for wrong_reg_no in wrong_reg_nos:
            response = self.client.put(
                reverse('api:store-cluster-view', args=(wrong_reg_no,)), payload
            )

            self.assertEqual(response.status_code, 404)

    def test_view_can_only_be_edited_by_its_owner(self):

        # login a top user user
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='jack@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:store-cluster-view', 
            args=(self.cluster.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 404)

    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        payload = self.get_premade_payload()

        response = self.client.put(
            reverse('api:store-cluster-view', 
            args=(self.cluster.reg_no,)), 
            payload,
        )
        self.assertEqual(response.status_code, 401)

class StoreClusterViewForDeletingTestCase(APITestCase):

    def setUp(self):

        # Create a user with email john@gmail.com
        self.user = create_new_user('john')

        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create cluster
        self.cluster = StoreCluster.objects.create(
           name='Magadi',
           profile=self.profile
        )

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_view_returns_models_correclty(self):

        # Count Number of Queries #
        with self.assertNumQueries(10):
            response = self.client.delete(
                reverse('api:store-cluster-view', 
                args=(self.cluster.reg_no,))
            )
        self.assertEqual(response.status_code, 204)

        # Confirm the model was deleted
        self.assertEqual(StoreCluster.objects.all().count(), 0)

    def test_view_can_handle_a_wrong_reg_no(self):

        response = self.client.delete(
            reverse('api:store-cluster-view', args=(4646464,)))
        self.assertEqual(response.status_code, 404)

        # Confirm the model was not deleted
        self.assertEqual(StoreCluster.objects.all().count(), 1)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.delete(
            reverse('api:store-cluster-view', 
            args=(self.cluster.reg_no,))
        )
        self.assertEqual(response.status_code, 401)

        # Confirm the model was not deleted
        self.assertEqual(StoreCluster.objects.all().count(), 1)