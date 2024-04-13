import base64
import yaml

from PIL import Image

from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.test_utils.custom_testcase import APITestCase
from core.test_utils.log_reader import get_log_content
from core.test_utils.create_user import create_new_random_cashier_user

from profiles.models import EmployeeProfile, Profile
from mysettings.models import MySetting
from mylogentries.models import UserActivityLog, CHANGED
from core.test_utils.initial_user_data import InitialUserDataMixin


class EpLeanUserIndexViewTestCase(APITestCase, InitialUserDataMixin):

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

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='gucci@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    
    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_user_index_lean'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 7, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.cashier_profile4.get_full_name(),
                    'reg_no': self.cashier_profile4.reg_no
                },
                {
                    'name': self.manager_profile2.get_full_name(),
                    'reg_no': self.manager_profile2.reg_no
                },
                {
                    'name': self.cashier_profile3.get_full_name(),
                    'reg_no': self.cashier_profile3.reg_no
                },
                {
                    'name': self.cashier_profile2.get_full_name(),
                    'reg_no': self.cashier_profile2.reg_no
                },
                {
                    'name': self.cashier_profile1.get_full_name(),
                    'reg_no': self.cashier_profile1.reg_no
                },
                {
                    'name': self.manager_profile1.get_full_name(),
                    'reg_no': self.manager_profile1.reg_no
                },
                {
                    'name': self.top_profile1.get_full_name(),
                    'reg_no': self.top_profile1.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = True
        ms.save()

        response = self.client.get(reverse('api:ep_user_index_lean'))
        self.assertEqual(response.status_code, 401)

    def test_view_can_only_show_employees_for_employee_registerd_stores(self):

        # Remove user from all stores 
        self.manager_profile1.stores.remove(self.store1, self.store2)

        response = self.client.get(reverse('api:ep_user_index_lean'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': []
        }

        self.assertEqual(response.data, result)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_view_for_employees_returns_the_right_content_with_pagination(self):

        # First delete all employe profiles
        EmployeeProfile.objects.all().exclude(reg_no=self.manager_profile1.reg_no).delete()

        p1 = Profile.objects.get(user__email='john@gmail.com')

        model_num_to_be_created = settings.LEAN_PAGINATION_PAGE_SIZE

        cashier_names = create_new_random_cashier_user(
            p1, 
            self.store1, 
            model_num_to_be_created - 1 
        )

        names_length = len(cashier_names)
        self.assertEqual(names_length, model_num_to_be_created-1)  # Confirm number of names

        self.assertEqual(
            EmployeeProfile.objects.filter(
                profile__user__email=p1.user.email).count(),
            names_length + 1
        )  # Confirm models were created

        employee_profiles = EmployeeProfile.objects.filter(
            profile__user__email=p1.user.email
        ).order_by('id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(7):
            response = self.client.get(
                reverse('api:ep_user_index_lean'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created+1)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/ep/profile/users/lean/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all employee profiles are listed except the first one since it's in the next paginated page #
        i = 1
        for employee in employee_profiles[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], employee.get_full_name())
            self.assertEqual(
                response_data_dict['results'][i]['reg_no'], employee.reg_no)

            i += 1

        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  # Confirm the number the for loop ran

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:ep_user_index_lean') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created + 1,
            'next': None,
            'previous': 'http://testserver/api/ep/profile/users/lean/',
            'results': [
                {
                    'name': self.top_profile1.get_full_name(),
                    'reg_no': self.top_profile1.reg_no
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_can_perform_search(self):

        search_terms = [
            self.cashier_profile1.user.first_name,
            self.cashier_profile1.user.last_name,
            self.cashier_profile1.user.email
        ]

        for search_term in search_terms:
            param = f'?search={search_term}'
            response = self.client.get(reverse('api:ep_user_index_lean') + param)
            self.assertEqual(response.status_code, 200)

            result = {
                'count': 1,
                'next': None,
                'previous': None,
                'results': [
                    {
                        'name': self.cashier_profile1.get_full_name(),
                        'reg_no': self.cashier_profile1.reg_no
                    }
                ]
            }

            self.assertEqual(response.data, result)

    def test_view_cant_be_viewed_by_a_top_user(self):

        # Login a top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.get(reverse('api:ep_user_index_lean'))
        self.assertEqual(response.status_code, 403)

    def test_view_cant_be_viewed_by_an_unlogged_in_user(self):

        # Unlogged in user
        self.client = APIClient()

        response = self.client.get(reverse('api:ep_user_index_lean'))
        self.assertEqual(response.status_code, 401)


class EmployeeProfileEditViewTestCase(APITestCase, InitialUserDataMixin):

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
        
        # Include an appropriate `Authorization:` header on all requests.
        token = Token.objects.get(user__email='kate@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def get_premade_payload(self):
        """
        Simplifies creating payload
        """

        payload = {
            'location':'Nairobi',
            'phone': 254711220000
        }

        return payload

    def test_if_view_is_returning_a_user_profile(self):
        
        response = self.client.get(reverse('api:ep_edit_employee_profile'))
        self.assertEqual(response.status_code, 200)
        
        result = {
            'full_name': self.cashier_profile1.get_full_name(), 
            'email': 'kate@gmail.com', 
            'image_url': f'/media/images/profiles/{self.cashier_profile1.reg_no}_.jpg', 
            'join_date': self.cashier_profile1.get_join_date(
                self.cashier_profile1.user.get_user_timezone()
            ), 
            'last_login_date': False, 
            'location': self.cashier_profile1.location, 
            'phone': self.cashier_profile1.phone
        }
        
        self.assertEqual(response.data, result)
  
                
        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
        
        response = self.client.get(reverse('api:ep_edit_employee_profile'))
        self.assertEqual(response.status_code, 401)

    def test_if_view_can_edit_a_profile(self):
        
        payload = self.get_premade_payload()
        
        response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 200)
                
        result = {
            'full_name': self.cashier_profile1.get_full_name(), 
            'email': 'kate@gmail.com', 
            'image_url': f'/media/images/profiles/{self.cashier_profile1.reg_no}_.jpg',  
            'join_date': self.cashier_profile1.get_join_date(
                self.cashier_profile1.user.get_user_timezone()
            ), 
            'last_login_date': False, 
            'location': payload['location'],  
            'phone': payload['phone'], 
        }
        
        self.assertEqual(response.data, result)

       
        # Confirm that the profile was edited successfully#
        p = EmployeeProfile.objects.get(user__email='kate@gmail.com')
    
        self.assertEqual(p.location, payload['location'])
        self.assertEqual(p.phone, payload['phone'])
        
        # Confirm that when profile phone is edited, the user's phone is also
        # edited
        
        user = get_user_model().objects.get(email='kate@gmail.com')
        
        self.assertEqual(user.phone, 254711220000)
        
        ########################## UserActivityLog ##############################'#
        # Confirm that the change was logged correctly
        
        log=UserActivityLog.objects.get(user__email='kate@gmail.com')
                        
        self.assertTrue('Location changed from "Killimani" to "Nairobi".\n' in log.change_message)
        self.assertTrue('Phone changed from "254711223366" to "254711220000".\n' in log.change_message)
        
        self.assertEqual(log.object_id, str(p.pk))
        self.assertEqual(log.object_repr, 'kate@gmail.com')
        self.assertEqual(log.content_type.model, 'employeeprofile')
        self.assertEqual(log.user.email, 'kate@gmail.com')
        self.assertTrue(len(log.ip) > 7)
        self.assertEqual(log.action_type, CHANGED)
        self.assertEqual(log.owner_email, '')
        self.assertEqual(log.panel, 'Api')
        
        self.assertEqual(UserActivityLog.objects.all().count(), 1)
        
        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
        
        response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
        self.assertEqual(response.status_code, 401)
    
    def test_if_view_wont_accept_an_empty_location(self):
                
        payload = self.get_premade_payload()
        payload['location'] = ''
        
        response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
        
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
        
        result = {'location': ['This field may not be blank.']}
        self.assertEqual(response.data, result)

    def test_if_view_accepts_correct_phones(self):

        phones = [
            '254700223322',
            '254709223322',
            '254711223322',
            '254719223322',
            '254720223327',
            '254729223322',
            '254790223322',
            '254799223322',       
        ]
        
        i=0
        for phone in phones:
            # Clear cache before every new request 
            cache.clear()
            
            payload = self.get_premade_payload()
            payload['phone'] = phone
            
            response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
            # Check if the request was successful #
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 7)
            
            # Confirm phone was changed
            self.assertEqual(EmployeeProfile.objects.filter(phone=phone).exists(), True)

            i+=1

    def test_if_view_cant_accept_a_non_unique_phone(self):
        
        # Try to edit profile with a phones from existing users

        top_user1_phone = get_user_model().objects.get(email='jack@gmail.com').phone 
        
        team_user1_phone = get_user_model().objects.get(email='james@gmail.com').phone 
        
        user_phones = [
            top_user1_phone, 
            team_user1_phone, 
        ]
        
        i=0
        for phone in user_phones:
            
            payload = self.get_premade_payload()
            payload['phone'] = phone
            
            response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
            
            # Check if the request was successful #
            self.assertEqual(response.status_code, 400)
        
            result = {'phone': ['User with this phone already exists.']}
            self.assertEqual(response.data, result)
            
            i+=1
            
        # Confirm how many times the loop ran
        self.assertEqual(i, 2)

     
    def test_if_view_cant_accept_wrong_phones(self):

        phones = [
            '25470022332j', # Number with letters
            '2547112233222', # Long Number
            '25471122332', # Short Number
            '254711223323333333333333333333333333333333',   # long Number
        ]
    
        i=0
        for phone in phones:
            # Clear cache before every new request 
            cache.clear()
            
            payload = self.get_premade_payload()
            payload['phone'] = phone
            
            response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
            # Check if the request was successful #
            self.assertEqual(response.status_code, 400)
            self.assertEqual(len(response.data['phone']), 1)
            
            if i == 1 or i == 3:               
                result = {'phone': ['This phone is too long.']}
                self.assertEqual(response.data, result)

            elif i == 2:
                result = {'phone': ['This phone is too short.']}
                self.assertEqual(response.data, result)

            else:                
                result = {'phone': ['A valid integer is required.']}
                self.assertEqual(response.data, result)

            i+=1

        self.assertEqual(i, 4)

      
    def test_if_view_logs_form_invalid(self):

        payload = self.get_premade_payload()
        payload['phone'] = 2577302233400   # Wrong long phone
             
        response = self.client.put(reverse('api:ep_edit_employee_profile'), payload)
        # Check if the request was successful #
        self.assertEqual(response.status_code, 400)
                
        result = {'phone': ['This phone is too long.']}
        self.assertEqual(response.data, result)
        
        
        ########################## Test Logging ##############################'#
        # Confirm that the created was logged correctly in a file
        
        
        content = get_log_content()
        
        self.assertEqual(len(content), 1)
        
        data = content[0]
        
        self.assertEqual(data['method'], 'PUT')
        self.assertEqual(data['full_path'], '/api/ep/profile/')
        self.assertEqual(data['status_code'], '400')
        
        self.assertEqual(data['process'].split('<=>')[0], 'form_invalid')
        self.assertTrue("This phone is too long." in data['process'].split('<=>')[1])
        
        process_dict = yaml.safe_load(data['process'].split('<=>')[2])
        self.assertEqual(process_dict['phone'], payload['phone'])

    def test_if_viewcan_only_be_viewed_by_its_owner(self):
        
        # Authorize team user
        token = Token.objects.get(user__email='james@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        response = self.client.get(reverse('api:ep_edit_employee_profile'))

        self.assertEqual(response.status_code, 200)
        
        response_data_dict = dict(response.data)
        
        self.assertEqual(response_data_dict['full_name'], 'James Sawer')
        self.assertEqual(response_data_dict['email'], 'james@gmail.com')
        
    def test_if_view_cant_be_viewed_by_a_top_user(self):
                
        # Login top user
        token = Token.objects.get(user__email='john@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        
        response = self.client.get(reverse('api:ep_edit_employee_profile'))
        self.assertEqual(response.status_code, 404)
            
    def test_if_view_cant_be_viewed_by_an_unlogged_in_user(self):
        
        # Unlogged in user
        self.client = APIClient()
        
        response = self.client.get(reverse('api:ep_edit_employee_profile'))
        self.assertEqual(response.status_code, 401)


class EmployeeProfilePictureEditViewTestCase(APITestCase, InitialUserDataMixin):

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
        token = Token.objects.get(user__email='kate@gmail.com')
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        # Test image resources
        self.test_image_name = 'pil_red.png'
        self.full_path=settings.MEDIA_ROOT + self.test_image_name

    def get_payload(self):

        return {
            'header': 'This is the edited header', 
            'footer': 'This is the edited footer', 
        }

    def test_if_view_can_edit_a_product_image(self):

        # Count Number of Queries
        #with self.assertNumQueries(9):
        with open(self.full_path, 'rb') as my_image: 
            
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'), 
                payload
            )

        self.assertEqual(response.status_code, 200)

        profile = EmployeeProfile.objects.get(user__email='kate@gmail.com')

        """
        Ensure the model has the right fields after it has been edited
        """
        # Check model url values
        self.assertEqual(
            profile.image.url, 
            f'/media/images/profiles/{profile.reg_no}_.jpg'
        )

        ########################## Test Maintenance ##############################'#
        # Turn on maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance=True
        ms.save()
         
        # Send data
        with open(self.full_path, 'rb') as my_image:
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'),
                payload,
            )
            
            self.assertEqual(response.status_code, 401)

    def test_if_view_can_edit_an_image_with_the_right_dimensions(self):

        # Send data
        with open(self.full_path, 'rb') as my_image:
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'),
                payload,
            )
            
            self.assertEqual(response.status_code, 200)

        # Confirm that the product image was saved with the right dimentsions#
        profile = EmployeeProfile.objects.get(user__email='kate@gmail.com')

        image_path = settings.MEDIA_ROOT + (profile.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)
       
        # Check model url values
        self.assertEqual(
            profile.image.url, 
            f'/media/images/profiles/{profile.reg_no}_.jpg'
        )

    def test_if_view_will_accept_jpg_image(self):

        blue_image_name = 'pil_blue.jpg'
        blue_image_path = settings.MEDIA_ROOT + blue_image_name
        
        blue_image =  Image.open(blue_image_path)
        
        width , height = blue_image.size

        self.assertEqual(width, 3264)
        self.assertEqual(height, 1836)
    
        # Send data
        with open(blue_image_path, 'rb') as my_image:
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'),
                payload,
            )
            
            self.assertEqual(response.status_code, 200)

        # Confirm that the product image was saved with the right dimentsions#
        profile = EmployeeProfile.objects.get(user__email='kate@gmail.com')

        image_path = settings.MEDIA_ROOT + (profile.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)

        # Check model url values
        self.assertEqual(
            profile.image.url, 
            f'/media/images/profiles/{profile.reg_no}_.jpg'
        )

    def test_if_view_will_accept_jpeg_image(self):

        orange_image_name = 'pil_orange.jpeg'
        orange_image_path = settings.MEDIA_ROOT + orange_image_name
        
        orange_image =  Image.open(orange_image_path)
        
        width , height = orange_image.size

        self.assertEqual(width, 3264)
        self.assertEqual(height, 1836)

        # Send data
        with open(orange_image_path, 'rb') as my_image:
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'),
                payload,
            )
            
            self.assertEqual(response.status_code, 200)

        # Confirm that the product image was saved with the right dimentsions#
        profile = EmployeeProfile.objects.get(user__email='kate@gmail.com')

        image_path = settings.MEDIA_ROOT + (profile.image.url).replace('/media/', '')

        image =  Image.open(image_path)
        
        width , height = image.size
        
        self.assertEqual(width, 200)
        self.assertEqual(height, 200)
       
        # Check model url values
        self.assertEqual(
            profile.image.url, 
            f'/media/images/profiles/{profile.reg_no}_.jpg'
        )

    def test_if_view_wont_accept_an_image_if_its_not_jpeg_jpg_or_png(self):

        gif_image_name = 'animated-love-image-0187.gif'
        gif_image_path = settings.MEDIA_ROOT + gif_image_name
        
        gif_image =  Image.open(gif_image_path)
        
        width , height = gif_image.size

        self.assertEqual(width, 240)
        self.assertEqual(height, 320)

        # Send data
        with open(gif_image_path, 'rb') as my_image:
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'),
                payload,
            )

            self.assertEqual(response.status_code, 400)
            
        result = {'error': 'Allowed image extensions are .jpg, .jpeg and .png'}
        self.assertEqual(response.data, result)

    def test_if_view_wont_accept_a_non_image_file(self):

        bad_file__name = 'bad_file_extension.py'
        bad_file_path = settings.MEDIA_ROOT + bad_file__name

        # Send data
        with open(bad_file_path, 'rb') as my_image:
            payload = self.get_payload()
            payload['uploaded_image'] = base64.b64encode(my_image.read())

            response = self.client.put(
                reverse('api:ep_edit_employee_profile_image'),
                payload,
            )

            self.assertEqual(response.status_code, 400)
            
        result = {'uploaded_image': ['Upload a valid image. The file you uploaded was either not an image or a corrupted image.']}
        self.assertEqual(response.data, result)

    def test_if_view_url_can_throttle_post_requests(self):

        throttle_rate = int(settings.THROTTLE_RATES['api_profile_image_rate'].split("/")[0])
    
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Send data
            with open(self.full_path, 'rb') as my_image:                    
                payload = self.get_payload()
                payload['uploaded_image'] = base64.b64encode(my_image.read()) 
    
                response = self.client.put(
                    reverse('api:ep_edit_employee_profile_image'),
                    payload,
                )
                self.assertEqual(response.status_code, 200)


        # Sometimes when testing throttling rates, depending on the the current
        # system time, we can be off by 1 or 2 retires which is acceptable.
        # So to accommodate this inconsistency, we make another additional 
        # request if the previous request was not throttled 
        for i in range(throttle_rate): # pylint: disable=unused-variable

            # Try to see if the next request will be throttled
            with open(self.full_path, 'rb') as my_image:
                payload = self.get_payload()
                payload['uploaded_image'] = base64.b64encode(my_image.read())
    
                response = self.client.put(
                    reverse('api:ep_edit_employee_profile_image'),
                    payload,
                )

            if response.status_code == 429:
                self.assertEqual(response.status_code, 429)
                break

        else: 
            # Executed because break was not called. This means the request was
            # never throttled 
            self.fail()

