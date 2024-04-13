from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.time_utils.time_localizers import utc_to_local_datetime_with_format

from stores.models import Store

#---------------- Start firebase model --------------------------------------

class FirebaseDevice(models.Model):

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    # Key field, though it is not the primary key of the model
    token = models.CharField(
        verbose_name='token',
        max_length=200,
        db_index=True,
        default=''
    )
    last_login_date = models.DateTimeField(
        verbose_name='last login date',
    )
    is_current_active = models.BooleanField(
        verbose_name='is current active',
        default=True
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now
    )

    def __str__(self):

        if self.token:

            if len(self.token) > 150:
                length = len(self.token)
                return f'{self.token[0:10]}....{self.token[(length-10):(length)]}'

            else:
                return 'Short token'

        return 'Empty token'

    def get_last_login_date(self, local_timezone):
        """Return the last login date in local time format"""
        return utc_to_local_datetime_with_format(
            self.last_login_date, 
            local_timezone
        )
    # Make last_login_date to be filterable
    get_last_login_date.admin_order_field = 'last_login_date'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(
            self.created_date, 
            local_timezone
        )
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'
    
#---------------- End firebase model --------------------------------------
