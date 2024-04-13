from django.db.models import Q

from firebase.tasks import firebase_multiple_users_messaging_tasks
from firebase.models import FirebaseDevice

class StoreClusterMessageSender:

    @staticmethod
    def send_cluster_creation_update_to_users(cluster):
        """
        Sends a newly cretaed cluster's data to users through firebase

        Args:
            cluster (StoreCluster): The new cluster that has been created
        """
        StoreClusterMessageSender.send_cluster_update_to_users(
            cluster, 
            'create'
        )

    @staticmethod
    def send_cluster_edit_update_to_users(cluster):
        """
        Sends a newly edited cluster's data to users through firebase

        Args:
            cluster (StoreCluster): The new cluster that has been created
        """
        StoreClusterMessageSender.send_cluster_update_to_users(
            cluster, 
            'edit'
        )

    @staticmethod
    def send_cluster_deletion_update_to_users(cluster):
        """
        Sends a newly deleted cluster's data to users through firebase

        Args:
            cluster (StoreCluster): The new cluster that has been created
        """
        StoreClusterMessageSender.send_cluster_update_to_users(
            cluster, 
            'delete'
        )

    @staticmethod
    def send_cluster_update_to_users(cluster, action_type):
        """
        Sends a newly cretaed cluster's data to users through firebase

        Args:
            cluster (StoreCluster): The new cluster that has been created
            action (String): A str describing the action type
        """
        owner_profile = cluster.profile
        owner_user = owner_profile.user
        group_id = owner_profile.get_user_group_identification()

        tokens = FirebaseDevice.objects.filter(
            Q(user=owner_user) | Q(user__employeeprofile__profile__user=owner_user)
            ).values_list('token')

        retrieved_tokens=[]
        for token in tokens:
            retrieved_tokens.append(token[0])

        relevant_stores = []
        
        payload = {
            'group_id': group_id,
            'relevant_stores': str(relevant_stores),
            'model': 'cluster',
            'action_type': action_type, 

            'name': cluster.name, 
            'reg_no': str(cluster.reg_no)
        }
        
        firebase_multiple_users_messaging_tasks(retrieved_tokens, payload)
    