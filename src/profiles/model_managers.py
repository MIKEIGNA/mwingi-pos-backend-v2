from django.db import models

class EmployeeModelManager(models.Manager):
    def filter(self, *args, **kwargs):
        """
        This method is used to get the objects of the model with that is_api_user=True.
        
        """
        queryset = super().get_queryset().filter(*args, **kwargs)
        return queryset.filter(is_api_user=False)
    
    def all_filter(self, *args, **kwargs):
        """
        This method is used to get all the objects of the model with the given filters.
        """
        return super().get_queryset().filter(*args, **kwargs)