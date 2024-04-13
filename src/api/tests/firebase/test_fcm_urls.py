from django.urls import reverse
from django.utils import timezone

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from firebase.models import FirebaseDevice

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.initial_user_data import InitialUserDataMixin

from mysettings.models import MySetting

class FirebaseDeviceViewTestCase(APITestCase, InitialUserDataMixin):

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

        self.token = 'cjSXLZvFSi6uzFLVPxFkfM:APA91bG3c4LagkGXl31iKi9uJB8Bfguf6uoX3VQ6n_69OgJIjTT_WvPMjqzd2bnU_uKAcBXkbxb_DJVETuVXTH2KYvy8uAPHZ7jLh3XBH0JhimtaRj-AvejuJw7HcunkUCIX0Rdy6_ZC'

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_if_view_is_will_create_model_when_its_non_existent(self):

        # Confirm there firbase device models
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 0)
    
        data = {'token': self.token, 'store_reg_no': self.store1.reg_no}
        
        response = self.client.post(reverse('api:fcm'), data, format='json')                                        
        self.assertEqual(response.status_code, 200)

        # Confirm a firbase device model was created
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 1)

        firebase = FirebaseDevice.objects.get(token=self.token)

        self.assertEqual(firebase.user, self.user1)
        self.assertEqual(firebase.store, self.store1)

    def test_if_view_is_will_update_user_when_it_already_exists(self):

        FirebaseDevice.objects.create(
            token=self.token,
            user=self.user2,
            store=self.store1,
            last_login_date=timezone.now()
        )

        data = {'token': self.token, 'store_reg_no': self.store2.reg_no}
        
        response = self.client.post(reverse('api:fcm'), data, format='json')                                        
        self.assertEqual(response.status_code, 200)

        # Confirm a firbase device model was created
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 1)

        firebase = FirebaseDevice.objects.get(token=self.token)

        self.assertEqual(firebase.user, self.user1)
        self.assertEqual(firebase.store, self.store2)

    def test_if_view_wont_create_a_new_one_if_one_already_exists(self):

        FirebaseDevice.objects.create(
            token=self.token,
            user = self.user1,
            store=self.store1,
            last_login_date = timezone.now()
        )

        data = {'token': self.token, 'store_reg_no': self.store1.reg_no}
        
        response = self.client.post(reverse('api:fcm'), data, format='json')                                        
        self.assertEqual(response.status_code, 200)

        # Confirm a firbase device model was created
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 1)

        firebase = FirebaseDevice.objects.get(token=self.token)

        self.assertEqual(firebase.user, self.user1)
        self.assertEqual(firebase.store, self.store1)

    def test_if_view_wont_accept_empty_token(self):

        data = {'token': '', 'store_reg_no': self.store1.reg_no}
        
        response = self.client.post(reverse('api:fcm'), data, format='json')                                        
        self.assertEqual(response.status_code, 400)

        result = {'token': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

        # Confirm a firbase device model was not created
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 0)

    def test_if_view_wont_accept_empty_store_reg_no(self):

        data = {'token': self.token, 'store_reg_no': ''}
        
        response = self.client.post(reverse('api:fcm'), data, format='json')                                        
        self.assertEqual(response.status_code, 400)
     
        result = {'store_reg_no': ['A valid integer is required.']}
        self.assertEqual(response.data, result)

        # Confirm a firbase device model was not created
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 0)

    def test_if_a_store_cant_be_created_with_a_wrong_store_reg_no(self):

        wrong_reg_nos = [
            7878787, # Wrong reg no,
            445464666666666666666666666666666666666666666666666666666, # long reg no
        ]

        i=0
        for wrong_reg_no in wrong_reg_nos:
            i+=1

            data = {'token': self.token, 'store_reg_no': wrong_reg_no}

            response = self.client.post(reverse('api:fcm'), data, format='json')                                        
            self.assertEqual(response.status_code, 404)

        # Confirm a firbase device model was not created
        self.assertEqual(
            FirebaseDevice.objects.filter(token=self.token).count(), 0)

    def test_if_FirebaseDeviceView_is_not_working_for_unloggedin_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        response = self.client.get(reverse('api:fcm'))
        self.assertEqual(response.status_code, 401)

