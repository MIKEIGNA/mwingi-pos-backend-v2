import datetime

from django.db import models
from django.utils import timezone
from django.conf import settings

from core.time_utils.time_localizers import utc_to_local_datetime_with_format

#---------------- Start loyverse auth model --------------------------

class LoyverseAppData(models.Model):
    name = models.CharField(
        verbose_name='name',
        default='main',
        max_length=10,
        editable=False,
        unique=True,
    )
    access_token = models.CharField(
        verbose_name='access token',
        max_length=100,
        default='a827c4447e9d47a3c98'
    )
    refresh_token = models.CharField(
        verbose_name='refresh token',
        max_length=100,
        default='b827c4447e9d47a3c98'
    )
    access_token_expires_in = models.IntegerField(
        verbose_name='access token expires in',
        default=0,
        editable=False
    )
    updated_date = models.DateTimeField(
        verbose_name='updated date',
        default=timezone.now,
    )
    receipt_day_minus_today = models.IntegerField(
        verbose_name='receipt day minus today',
        default=0,
    )

    class Meta:
        verbose_name_plural = "loyverse app data"

    def __str__(self):
        return str(self.name)

    def get_updated_date(self):
        """Return the updated date in local time format"""
        return utc_to_local_datetime_with_format(
            self.updated_date, 
            settings.LOCATION_TIMEZONE
        )
    # Make updated date to be filterable
    get_updated_date.admin_order_field = 'updated_date'

    def update_receipt_day_minus_today(self):
        """
        We find the max number of days that we have to go back from our stores
        """
        
        # days = list(LoyverseStore.objects.all().values_list('days_to_go_back', flat=True))

        # max_num = 0
        # if days:
        #     max_num = max(days)

        # self.receipt_day_minus_today = max_num

        self.receipt_day_minus_today = 1

    def get_receipt_anlayze_date(self):

        back_date = timezone.now() + datetime.timedelta(
            days=-int(self.receipt_day_minus_today)
        )
        # This makes sure the back date starts at midnight
        back_date = back_date.replace(
            hour=0, 
            minute=0, 
            second=0, 
            microsecond=0
        )
 
        return back_date

    def receipt_anlayze_iso_date(self):
        """
        Returns date in this ISO 8601 format - This date is required for loyverse
        queries
        
        For example 2020-03-30T18:30:00.000Z
        """
        back_date = self.get_receipt_anlayze_date()

        # Change date format   2022-03-12T00:00:00.000Z
        return (back_date).strftime("%Y-%m-%dT00:00:00.000Z")

    def receipt_anlayze_date(self):
        """Return the receipt anlayze date in March, 30, 2022 format"""
        return (self.get_receipt_anlayze_date()).strftime("%B, %d, %Y")

    def save(self, *args, **kwargs):

        self.updated_date = timezone.now()

        self.update_receipt_day_minus_today()

        super(LoyverseAppData, self).save(*args, **kwargs)

#---------------- End loyverse auth model --------------------------
