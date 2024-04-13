from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import NoReverseMatch, reverse
from django.contrib.admin.utils import quote
from django.utils.safestring import mark_safe

from core.time_utils.time_localizers import utc_to_local_datetime_with_format

from profiles.models import Profile


User = get_user_model()

CREATED = 1
CHANGED = 2
DELETED = 3

ACTION_TYPE_CHOICES = [
    (CREATED, 'Created',),
    (CHANGED, 'Changed',),
    (DELETED, 'Deleted',),
]

class UserActivityLog(models.Model):
    action_time = models.DateTimeField(
        verbose_name='action time',
        default=timezone.now,
        editable=False,
    )
    change_message = models.TextField(
        'change message',
        blank=True
    )
    object_id = models.TextField('object id',
                                 blank=True,
                                 null=True
                                 )
    # Translators: 'repr' means representation (https://docs.python.org/3/library/functions.html#repr)
    object_repr = models.CharField(
        verbose_name='object repr',
        max_length=200,
        default='',
    )
    ip = models.GenericIPAddressField(
        verbose_name='ip',
        blank=True,
        null=True,
    )
    content_type = models.ForeignKey(
        ContentType,
        models.SET_NULL,
        verbose_name='content type',
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        User,
        models.CASCADE,
        verbose_name='user',
        blank=True,
        null=True,
    )
    action_type = models.PositiveSmallIntegerField(
        verbose_name='action type',
        choices=ACTION_TYPE_CHOICES,
    )
    owner_email = models.EmailField(
        verbose_name='owner email',
        max_length=254,
        blank=True
    )
    panel = models.CharField(
        verbose_name='panel',
        max_length=6,
        default='',
    )
    is_hijacked = models.BooleanField(
        verbose_name='is hijacked',
        default=False)

    class Meta:
        verbose_name = 'user activity log'
        verbose_name_plural = 'user activity logs'
        ordering = ('-action_time',)

    def __str__(self):
        if self.is_creation():
            return '{} Created.'.format((str(self.content_type)).title())

        elif self.is_change():
            return '{} Changed.'.format((str(self.content_type)).title())

        elif self.is_deletion():
            return '{} Deleted.'.format((str(self.content_type)).title())

    def is_creation(self):
        return self.action_type == CREATED

    def is_change(self):
        return self.action_type == CHANGED

    def is_deletion(self):
        return self.action_type == DELETED

    def get_change_message(self):
        return self.change_message

    def get_edited_object(self):
        "Returns the edited object represented by this log entry"
        try:
            return self.content_type.get_object_for_this_type(pk=self.object_id)
        except:
            return "Can't be found"

    def get_admin_url(self):
        """
        Returns the admin URL to edit the object represented by this log entry.
        """
        if self.content_type and self.object_id:
            url_name = 'admin:%s_%s_change' % (
                self.content_type.app_label, self.content_type.model)

            try:
                return reverse(url_name, args=(quote(self.object_id),))
            except NoReverseMatch:

                pass
        return None

    def the_object(self):
        """ Returns the logged object's admin url """
        if self.action_type != DELETED:
            url = '<a href="{}{}">{}</a>'.format(
                settings.MY_SITE_URL, self.get_admin_url(), (str(self.content_type)).title())

        else:
            url = '{}'.format((str(self.content_type)).title())

        return mark_safe(url)
    the_object.allow_tags = True

    def editor_profile(self):
        """ Returns the profile's admin url that edited the log entry """
        url = self.get_email_url(self.user.email)

        return mark_safe(url)
    editor_profile.allow_tags = True
    editor_profile.admin_order_field = 'editor'
    editor_profile.short_description = 'editor'

    def find_owner(self):
        """ Returns email of the profile that owns the log entry object thats been logged"""

        email = self.owner_email
        if email:
            url = self.get_email_url(email)
            return mark_safe(url)
        else:
            return 'Not Assigned'
    find_owner.allow_tags = True
    find_owner.admin_order_field = 'owner'
    find_owner.short_description = 'owner'

    def get_email_url(self, email):
        """ Returns the profile's admin url or email that edited the log entry """

        try:
            pk = Profile.objects.get(user__email=email).pk

            app_label = 'profiles'
            my_model = 'profile'
            url_name = 'admin:%s_%s_change' % (app_label, my_model)
            reverse_url = reverse(url_name, args=(quote(pk),))

            url = '<a href="{}{}">{}</a>'.format(settings.MY_SITE_URL,
                                                 reverse_url,
                                                 email
                                                 )

            return url
        except:
            return email


class PaymentLog(models.Model):
    amount = models.PositiveIntegerField(
        verbose_name='amount',
    )
    payment_method = models.CharField(
        verbose_name='payment method',
        max_length=50,
        default='',
    )
    mpesa_id = models.PositiveIntegerField(
        verbose_name='mpesa id',
        default=0,
    )
    payment_type = models.CharField(
        verbose_name='payment type',
        max_length=50,
        default='',
    )
    email = models.EmailField(
        verbose_name='email',
        max_length=50,
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
    )
    duration = models.IntegerField(
        verbose_name='duration',
        default=0,
        blank=True
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    
    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)
    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = 'created_date'


class MpesaLog(models.Model):
    paymentlog = models.ForeignKey(PaymentLog, on_delete=models.CASCADE)
    transaction_type = models.CharField(
        verbose_name='transaction type',
        max_length=50,
        default='',
    )
    trans_id = models.CharField(
        verbose_name='trans id',
        max_length=50,
        unique=True,
    )
    trans_time = models.BigIntegerField(
        verbose_name='trans time',
    )
    trans_amount = models.DecimalField(
        verbose_name='trans amount',
        max_digits=30,
        decimal_places=2,
    )
    business_shortcode = models.IntegerField(
        verbose_name='business shortcode',
    )
    bill_ref_number = models.BigIntegerField(
        verbose_name='bill ref number',
    )
    invoice_number = models.IntegerField(
        verbose_name='invoice number',
    )
    org_account_balance = models.DecimalField(
        verbose_name='org account balance',
        max_digits=7,
        decimal_places=2,
    )
    third_party_trans_id = models.CharField(
        verbose_name='third party trans id',
        max_length=50,
        default='',
    )
    msisdn = models.BigIntegerField(
        verbose_name='msisdn',
    )
    first_name = models.CharField(
        verbose_name='first name',
        max_length=50,
        default='',
    )
    middle_name = models.CharField(
        verbose_name='middle name',
        max_length=50,
        default='',
    )
    last_name = models.CharField(
        verbose_name='last name',
        max_length=50,
        default='',
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_admin_url(self):
        """
        Returns the admin URL to edit the PaymentLog for this MpesaLog.
        """
        content_type = ContentType.objects.get_for_model(PaymentLog)

        try:
            return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.paymentlog.id,))

        except:
            return "Can't return Url"

    def show_paymentlog_id_link(self):
        """
        Returns the admin URL to edit the PaymentLog for this MpesaLog.
        """

        url = '<a href="{}{}">{}</a>'.format(
            settings.MY_SITE_URL, self.get_admin_url(), self.paymentlog.payment_method)

        return mark_safe(url)

    show_paymentlog_id_link.allow_tags = True
    show_paymentlog_id_link.admin_order_field = 'paymentlog_link'
    show_paymentlog_id_link.short_description = 'paymentlog_link'

    def save(self, *args, **kwargs):

        try:
            self.invoice_number = int(self.invoice_number)
        except:
            self.invoice_number = 0

        try:
            self.org_account_balance = Decimal(self.org_account_balance)
        except:
            self.org_account_balance = 0.0

        # Call the "real" save() method.
        super(MpesaLog, self).save(*args, **kwargs)


class RequestTimeSeries(models.Model):
    email = models.EmailField(
        verbose_name='email',
        max_length=70,
    )
    is_logged_in_as_email = models.EmailField(
        verbose_name='is logged in as email',
        max_length=70,
        blank=True
    )
    is_logged_in_as = models.BooleanField(
        verbose_name='is logged in as',
        default=False
    )
    os = models.CharField(
        verbose_name='os',
        max_length=15,
    )
    device_type = models.CharField(
        verbose_name='device type',
        max_length=15,
    )
    browser = models.CharField(
        verbose_name='browser',
        max_length=15,
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='ip address',)
    view_name = models.CharField(
        verbose_name='view name',
        max_length=500,
    )
    request_method = models.CharField(
        verbose_name='request method',
        max_length=10,
    )
    status_code = models.PositiveIntegerField(
        verbose_name='status code',
        default=0,
    )
    is_api = models.BooleanField(
        verbose_name='is api',
        default=False
    )
    location_update = models.BooleanField(
        verbose_name='location update',
        default=False
    )
    map_loaded = models.BooleanField(
        verbose_name='map loaded',
        default=False
    )
    was_throttled = models.BooleanField(
        verbose_name='was throttled',
        default=False
    )
    response_time = models.FloatField(
        verbose_name='response time',
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def set_is_logged_in_as(self):
        """Set is_logged_in_as depending with the availability of 
        is_logged_in_as_email"""

        if self.is_logged_in_as_email:
            self.is_logged_in_as = True
        else:
            self.is_logged_in_as = False

    def save(self, *args, **kwargs):

        # Set is_logged_in_as
        self.set_is_logged_in_as()

        # Call the "real" save() method.
        return super(RequestTimeSeries, self).save(*args, **kwargs)
