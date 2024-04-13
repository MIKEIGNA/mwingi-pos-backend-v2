from django.db import models

from stores.models import Store
from profiles.models import Profile

class StoreCluster(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE,)
    name = models.CharField(verbose_name='name', max_length=50)
    stores = models.ManyToManyField(Store)
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        db_index=True,
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique 
    )

    def __str__(self):
        return str(self.name)

    def get_registered_cluster_stores_data(self):
        """
        Returns a list of dicts with all store's names and reg nos for the
        cluster
        """
        cluster_stores = self.stores.all().order_by('id').values(
            'name',
            'reg_no'
        )

        return list(cluster_stores)

    def get_available_stores_data(self):
        """
        Returns a list of dicts with all store's names and reg nos that
        are not trucks
        """
        stores_data = Store.objects.filter(
            profile=self.profile
        ).order_by('name').values(
            'name',
            'reg_no' 
        )

        return list(stores_data)

    def get_clusters_store_names(self):
        """
        Returns a list of truck clustter's(For this model) store names that
        """
        store_names = self.stores.all().order_by('name').values_list(
            'name',
            flat=True
        )

        return list(store_names)

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a customer creation message. Otherwise we
        send a customer edit message
        """
        from firebase.message_sender_cluster import StoreClusterMessageSender

        if created:
            StoreClusterMessageSender.send_cluster_creation_update_to_users(self)
        else:
            StoreClusterMessageSender.send_cluster_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Send a cluster delete message.
        """
        from firebase.message_sender_cluster import StoreClusterMessageSender
        
        StoreClusterMessageSender.send_cluster_deletion_update_to_users(self)

    def save(self, *args, **kwargs):

        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        """ Check if this object is being created """
        created = self.pk is None

        # Call the "real" save() method.
        super(StoreCluster, self).save(*args, **kwargs)

        self.send_firebase_update_message(created)

    def delete(self, *args, **kwargs):
        # Call the "real" delete() method.
        super(StoreCluster, self).delete(*args, **kwargs)

        self.send_firebase_delete_message()