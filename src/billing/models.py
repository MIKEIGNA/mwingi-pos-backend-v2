from dateutil.relativedelta import relativedelta

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.conf import settings
from django.utils.safestring import mark_safe
from core.time_utils.time_localizers import utc_to_local_datetime

from mylogentries.models import PaymentLog
from profiles.models import EmployeeProfile


class Subscription(models.Model):
    employee_profile = models.OneToOneField(
        EmployeeProfile, on_delete=models.CASCADE)
    due_date = models.DateTimeField(
        verbose_name='due date',
        default=timezone.now)
    last_payment_date = models.DateTimeField(
        verbose_name='last payment date',
        default=timezone.now)
    days_to_go = models.IntegerField(
        verbose_name='days to go',
        default=0)
    expired = models.BooleanField(
        verbose_name='expired',
        default=True)

    def __str__(self):
        return 'Subs - {}'.format(str(self.employee_profile))

    def get_profile(self):
        """Return the subscriptions top profile"""
        return self.employee_profile.profile

    def get_employee_profile(self):
        """Return the subscriptions employee profile"""
        return self.employee_profile

    def get_due_date(self, local_timezone):
        """Return the subscriptions due_date in local time"""

        # Change time from utc to local
        due_date = utc_to_local_datetime(self.due_date, local_timezone)

        # Change date format
        due_date = (due_date).strftime("%B, %d, %Y")

        return due_date
    # Make due_date to be filterable
    get_due_date.admin_order_field = 'due_date'

    # TODO Test this
    def get_admin_due_date(self):
        """Return the due date in local time format"""
        return self.get_due_date(settings.LOCATION_TIMEZONE)
    # Make due_date to be filterable
    get_admin_due_date.admin_order_field = 'due_date'

    def get_last_payment_date(self, local_timezone):
        """Return the user last_payment_date"""

        # Change time from utc to local
        last_payment_date = utc_to_local_datetime(
            self.last_payment_date,
            local_timezone
        )

        # Change date format
        last_payment_date = (last_payment_date).strftime("%B, %d, %Y")

        return last_payment_date
    # Make last_payment_date to be filterable
    get_last_payment_date.admin_order_field = 'last_payment_date'

    # TODO Test this
    def get_admin_last_payment_date(self):
        """Return the due date in local time format"""
        return self.get_last_payment_date(settings.LOCATION_TIMEZONE)
    # Make last_payment_date to be filterable
    get_admin_last_payment_date.admin_order_field = 'last_payment_date'

    def get_employee_profile_reg_no(self):
        """ Return the subscription's employee profile reg_no """
        return self.employee_profile.reg_no

    def set_days_to_go(self):
        """Set subscription days_to_go and due_date"""
        join_date = self.employee_profile.join_date
        last_payment_date = self.last_payment_date

        """
        If join_date == last_payment_date, that means the device has no
        payment history and so days_to_go is set to 0
        """
        if not join_date == last_payment_date:
            self.days_to_go = (self.due_date - timezone.now()).days

        else:
            self.days_to_go = 0

    def is_expired(self):
        """Check if the Subscription has expired
           If days to go is below zero, Subscription is expired and device is locked
        """
        if self.days_to_go < 0:
            self.expired = True
        else:
            self.expired = False

        """ If the employee profile has no payment history, expired should be True"""
        if self.employee_profile.join_date == self.last_payment_date:
            self.expired = True

        """
        Turn subscription employee_profile's
        user is_active to False when subscription has expired and True otherwise
        """

        # if self.expired:
        #     user = self.employee_profile.user
        #     user.is_active = False
        #     user.save()

        # else:
        #     user = self.employee_profile.user
        #     user.is_active = True
        #     user.save()

    def save(self, *args, **kwargs):
        self.set_days_to_go()
        self.is_expired()

        # Call the "real" save() method.
        super(Subscription, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass


class Payment(models.Model):
    paymentlog = models.ForeignKey(PaymentLog, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        verbose_name='amount',
        default=0)
    payed_date = models.DateTimeField(
        verbose_name='payed date',
        default=timezone.now)
    parent_reg_no = models.BigIntegerField(
        verbose_name='parent reg no',
        default=0,
    )
    account_reg_no = models.BigIntegerField(
        verbose_name='account reg no',
        default=0,
    )
    account_type = models.CharField(
        verbose_name='account type',
        max_length=50,
        blank=True,
    )
    duration = models.PositiveIntegerField(
        verbose_name='duration',
        default=0)  # Subsription duration

    def __str__(self):
        return 'Pay - {}'.format(self.account_reg_no)

    def get_payed_date(self, local_timezone):
        """ Returns the payments payed_date in local time """

        # Change time from utc to local
        payed_date = utc_to_local_datetime(self.payed_date, local_timezone)

        # Change date format
        payed_date = (payed_date).strftime("%B, %d, %Y, %I:%M:%p")

        return payed_date
    # Make payed_date to be filterable
    get_payed_date.admin_order_field = 'payed_date'

    def get_account_reg_no(self):
        """ Return the payment's account reg_no """
        return self.account_reg_no

    def get_admin_url(self):
        """
        Returns the admin URL to edit the object represented by this log entry.
        """
        content_type = ContentType.objects.get_for_model(PaymentLog)

        try:
            return reverse(
                "admin:%s_%s_change" % (
                    content_type.app_label, content_type.model),
                args=(self.paymentlog.id,)
            )

        # pylint: disable=bare-except
        except Exception as e:
            print("Error ", e)
            return "Can't return Url"

    def show_paymentlog_id_link(self):
        url = '<a href="{}{}">{}</a>'.format(
            settings.MY_SITE_URL,
            self.get_admin_url(),
            self.paymentlog.payment_method
        )

        return mark_safe(url)

    show_paymentlog_id_link.allow_tags = True
    show_paymentlog_id_link.admin_order_field = 'paymentlog_link'
    show_paymentlog_id_link.short_description = 'paymentlog_link'

    def save(self, *args, **kwargs):
        # Call the "real" save() method.
        super(Payment, self).save(*args, **kwargs)


@receiver(post_save, sender=Payment)
def update_account_subscription_signal(sender, instance, created, **kwargs):
    """Update Subscription last_payment_date and due_date"""
    if created:
        payed_date = instance.payed_date

        subscription = Subscription.objects.get(
            employee_profile__reg_no=instance.account_reg_no
        )

        if subscription.expired:
            due_date = (payed_date + relativedelta(months=instance.duration))
        else:
            due_date = (subscription.due_date +
                        relativedelta(months=instance.duration))

        subscription.last_payment_date = payed_date
        subscription.due_date = due_date
        subscription.save()
