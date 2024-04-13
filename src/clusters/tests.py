from pprint import pprint
from django.test import TestCase

from core.test_utils.create_store_models import create_new_store
from core.test_utils.create_user import create_new_user
from core.test_utils.log_reader import get_test_firebase_sender_log_content

from profiles.models import Profile
from clusters.models import StoreCluster

from core.test_utils.custom_testcase import TestCase, empty_logfiles

# Create your tests here.
class StoreClusterTestCase(TestCase):

    def setUp(self):
        
        #Create a user1
        self.user = create_new_user('john') 
        
        self.profile = Profile.objects.get(user__email='john@gmail.com')

        # Create stores
        self.store1 = create_new_store(self.profile, 'Store1')
        self.store2 = create_new_store(self.profile, 'Store2')
        self.store3 = create_new_store(self.profile, 'Store3')
        self.store4 = create_new_store(self.profile, 'Store4')

        # Create cluster
        cluster = StoreCluster.objects.create(profile=self.profile, name='Magadi')

        cluster.stores.add(self.store1, self.store2)
   
    def test_verbose_names(self):
        
        cluster = StoreCluster.objects.get()

        self.assertEqual(cluster._meta.get_field('name').verbose_name,'name')
        self.assertEqual(cluster._meta.get_field('reg_no').verbose_name,'reg no')
                
        fields = ([field.name for field in StoreCluster._meta.fields])
        
        self.assertEqual(len(fields), 4)

    def test_model_fields_after_it_has_been_created(self):
        
        cluster = StoreCluster.objects.get()

        self.assertEqual(cluster.profile, self.profile)
        self.assertEqual(cluster.name, 'Magadi')
        self.assertEqual(
            list(cluster.stores.all().values_list('id', flat=True)),
            [self.store1.id, self.store2.id]
        )
        self.assertTrue(cluster.reg_no > 100000)  # Check if we have a valid reg_no

        self.assertEqual(str(cluster), cluster.name)

    def test_get_registered_cluster_stores_method(self):

        cluster = StoreCluster.objects.get()

        self.assertEqual(
            cluster.get_registered_cluster_stores_data(),
            [
                {
                    'name': self.store1.name, 
                    'reg_no': self.store1.reg_no
                }, 
                {
                    'name': self.store2.name, 
                    'reg_no': self.store2.reg_no
                } 
            ]
        )

    def test_get_available_stores_method(self):

        cluster = StoreCluster.objects.get() 

        stores_data = cluster.get_available_stores_data()
        results = [
            {
                'name': self.store1.name, 
                'reg_no': self.store1.reg_no
            }, 
            {
                'name': self.store2.name, 
                'reg_no': self.store2.reg_no
            }, 
            {
                'name': self.store3.name, 
                'reg_no': self.store3.reg_no
            },
            {
                'name': self.store4.name, 
                'reg_no': self.store4.reg_no
            }
        ]

        self.assertEqual(len(stores_data), len(results))

        for store in stores_data:
            self.assertTrue(store in results)

    def test_get_clusters_store_names_method(self):

        cluster = StoreCluster.objects.get()

        self.assertEqual(
            cluster.get_clusters_store_names().sort(),  
            [self.store1.name, self.store2.name].sort()
        )

    def test_firebase_messages_are_sent_correctly(self):

        StoreCluster.objects.all().delete()
        empty_logfiles()

        # Create cluster
        cluster = StoreCluster.objects.create(profile=self.profile, name='Magadi')

        content = get_test_firebase_sender_log_content(only_include=['cluster'])
        self.assertEqual(len(content), 1)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'cluster', 
                'action_type': 'create', 
                'name': cluster.name,
                'reg_no': str(cluster.reg_no)
            }
        }

        self.assertEqual(content[0], result)

        # Edit cluster
        cluster = StoreCluster.objects.get(profile=self.profile)
        cluster.name = 'New name'
        cluster.save()

        content = get_test_firebase_sender_log_content(only_include=['cluster'])
        self.assertEqual(len(content), 2)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'cluster', 
                'action_type': 'edit', 
                'name': 'New name', 
                'reg_no': str(cluster.reg_no)
            }
        }

        self.assertEqual(content[1], result)
    

        #Delete cluster
        StoreCluster.objects.get(name='New name').delete()

        content = get_test_firebase_sender_log_content(only_include=['cluster'])
        self.assertEqual(len(content), 3)

        result = {
            'tokens': [], 
            'payload': {
                'group_id': self.profile.get_user_group_identification(), 
                'relevant_stores': '[]', 
                'model': 'cluster', 
                'action_type': 'delete', 
                'name': 'New name', 
                'reg_no': str(cluster.reg_no)
            }
        }

        self.assertEqual(content[2], result)
        
