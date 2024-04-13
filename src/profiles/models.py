import os
import shutil
from PIL import Image

from django.db.models.aggregates import Sum
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator

from accounts.models import UserGroup
from accounts.websocket.consumers.user_consumers import WebSocketMessageSender
from accounts.utils.validators import validate_phone_for_models
from accounts.utils.currency_choices import CURRENCY_CHOICES
from accounts.utils.user_type import TOP_USER

from core.image_utils import ModelImageHelpers
from core.reg_no_generator import get_unique_reg_no

from core.time_utils.time_localizers import utc_to_local_datetime_with_format
from profiles.model_managers import EmployeeModelManager



# Profile image directory
def profile_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images/profiles/<profiile.reg_no>_<filename>.jpg

    path = '{}{}_{}'.format(
        settings.IMAGE_SETTINGS['profile_images_dir'], instance.reg_no, filename)

    return path

# Profile initial image
def get_initial_profile_image2():
    """
    Creates the initial profile image by copying the default stie's no_image.jgp
    then moves it into the profile image folder.

    Returns the path of the newly created profile image
    """
    original_img = './accounts/management/commands/utils/createmedia_assets/images/no_image.jpg'

    media_path = f'images/profiles/{get_unique_reg_no()}.jpg'

    target = ''
    target2 = ''
    if not settings.TESTING_MODE:
        target = f'{settings.MEDIA_URL}{media_path}'
        target2 = media_path
    else:
        target = f'{settings.MEDIA_URL}images/tests/{media_path}'
        target2 = f'{media_path}'

    shutil.copyfile(original_img, f'.{target}')


    print(f'TT>{target}')

    return Image.open(f'.{target}'), target2

# Profile initial image
def get_initial_profile_image():
    """
    Creates the initial profile image by copying the default stie's no_image.jgp
    then moves it into the profile image folder.

    Returns the path of the newly created profile image
    """
    original_img = './accounts/management/commands/utils/createmedia_assets/images/no_image.jpg'

    media_path = f'images/profiles/{get_unique_reg_no()}.jpg'

    target = ''
    if not settings.TESTING_MODE:
        target = f'{settings.MEDIA_URL}{media_path}'
    else:
        target = f'{settings.MEDIA_URL}images/tests/{media_path}'

    shutil.copyfile(original_img, f'.{target}')

    return media_path

# Receipt image directory
def receipt_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images/receipts/<receipt.reg_no>_<filename>.jpg

    path = '{}{}_{}'.format(
        settings.IMAGE_SETTINGS['receipt_images_dir'], instance.reg_no, filename)

    return path


class CommonProfileMethodsMixin:
    """
    This mixin should only contain universal methods that can be used by both the
    Profile and EmployeeProfile models without causing any problems or security flaws
    """

    def __str__(self):
        return self.user.email

    def get_short_name(self):
        """Return the user name"""
        return self.user.get_short_name()

    def get_full_name(self):
        """Return the user full name"""

        full_name = ""
        with transaction.atomic():
            full_name = self.user.get_full_name()

        return full_name

    def get_join_date(self, local_timezone):
        """Return the user join date in local time format"""
        return utc_to_local_datetime_with_format(self.join_date, local_timezone)
    # Make join_date to be filterable
    get_join_date.admin_order_field = 'join_date'

    # TODO Test this
    def get_admin_join_date(self):
        """Return the join date in local time format"""
        return self.get_join_date(settings.LOCATION_TIMEZONE)
    # Make join_date to be filterable
    get_admin_join_date.admin_order_field = 'join_date'

    def get_last_login_date(self, local_timezone): 
        """Return the user last login date in local time format"""

        """ 
        If the profile has never logged in, getting date will fail and so
        we return False
        """
        try:

            # Change time from utc to local
            local_last_login_date = utc_to_local_datetime_with_format(
                self.user.last_login, 
                local_timezone
            )

        # pylint: disable=bare-except
        except:
            local_last_login_date = False

        return local_last_login_date
    # Make last_login to be filterable
    get_last_login_date.admin_order_field = 'last_login'

    # TODO Test this
    def get_admin_last_login_date(self):
        """Return the user last login date in local time format"""
        return self.get_last_login_date(settings.LOCATION_TIMEZONE)
    # Make last_login to be filterable
    get_admin_last_login_date.admin_order_field = 'last_login'

    def get_profile_image_url(self):
        """
        Return image url or an empty string
        """
        try:
            return self.image.url

        # pylint: disable=bare-except
        except:
            return ""

    def get_location(self):
        """
        Return location or return "Not set" if location is not there
        """

        if self.location:
            return self.location
        else:
            return "Not set"

    def get_user_group_identification(self):
        """
        Returns a group id that should be used by this profile and his/employees
        in veryfing firebase messages in mobile apps
        """
        return f'group_{self.reg_no}'

    def mark_staff_as_approved(self):
        """ 
        If user is staff mark profile as approved
        """
        if self.user.is_staff:
            self.approved = True

    def sync_profile_phone_and_its_user_phone(self):
        """
        Make sure user's phone is the same with profile's phone
        """

        user = self.user

        if not self.phone == user.phone:
            user.phone = self.phone
            user.save()

    def send_profile_update_to_websocket(self):

        # Type is needed so that websocket clients will know how to deal with
        # the data
        payload = {
            'type': 'profile_change',
            'profile_image_url': self.get_profile_image_url()}

        WebSocketMessageSender.send_profile_update_to_user(self.user, payload)

    def create_inital_image(self, created):
        """
        Only create initial image during model creation 

        Args:
            created: A flag indicating if the model is being created for the 
                     first time or not
        """

        # Only create initial image during model creation 
        if created:
            ModelImageHelpers.save_model_mage(self)

# ========================== START Profile Models

class Profile(CommonProfileMethodsMixin, models.Model):
    
    # This field is required by all models that will use ApiImageUploader()
    # to upload images using REST Api
    IMAGE_SUB_DIRECTORY = settings.IMAGE_SETTINGS['profile_images_dir']

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to=profile_directory_path,
        default=settings.IMAGE_SETTINGS['no_image_url'],
        verbose_name='image',
    )
    phone = models.BigIntegerField(
        verbose_name='phone',
        validators=[validate_phone_for_models],
        unique=True,
        default=0
    )
    approved = models.BooleanField(
        verbose_name='approved',
        default=False)  # Consider deletion
    join_date = models.DateTimeField(
        verbose_name='join date',
        default=timezone.now,
        db_index=True)
    business_name = models.CharField(
        verbose_name='business name',
        max_length=60,
        default=''
    )
    location = models.CharField(
        verbose_name='location',
        max_length=100,
    )
    currency = models.IntegerField(
        verbose_name='currency',
        choices=CURRENCY_CHOICES,
        default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )

    """ The CommonProfileMethodsMixin defines the following methods
    
    __str__
    get_short_name
    get_full_name
    get_join_date
    get_last_login_date
    get_profile_image_url
    get_location
    mark_staff_as_approved
    sync_profile_phone_and_its_user_phone
    send_profile_update_to_websocket
    create_inital_image
    """

    def get_currency(self):
        return self.currency

    def get_currency_initials(self):
        # pylint: disable=invalid-sequence-index
        return CURRENCY_CHOICES[self.currency][1]

    def create_profile_count(self, created):
        """
        Create ProfileCount
        """

        if created:
            ProfileCount.objects.create(profile=self)

    def get_inventory_valuation(self, store_reg_nos=None): 
        from django.db.models import F
        from inventories.models import StockLevel

        stock_level_queryset = StockLevel.objects.filter(
            store__profile=self,
            product__variant_count=0
        )

        if store_reg_nos:
            stock_level_queryset = stock_level_queryset.filter(
                store__reg_no__in=store_reg_nos
            )

        aggregate = stock_level_queryset.aggregate(
            Sum('units'),
            inventory_value=Sum(F('units') * F('product__cost')),
            retail_value=Sum(F('units') * F('product__price'))
        )

        inventory_value = aggregate['inventory_value']
        retail_value = aggregate['retail_value']

        # If any of these values is None, replace them with 0
        inventory_value = inventory_value if inventory_value else 0
        retail_value = retail_value if retail_value else 0

        potential_profit = retail_value - inventory_value

        try:
            margin = (potential_profit * 100) / retail_value
        except: # pylint: disable=bare-except
            margin = 0

        return {
            'inventory_value': str(round(inventory_value, 2)),
            'retail_value': str(round(retail_value, 2)),
            'potential_profit': str(round(potential_profit, 2)),
            'margin': str(round(margin, 2)),
        }

    def get_store_payments(self):

        return list(self.storepaymentmethod_set.all().values(
            'name', 'payment_type', 'reg_no'
        ))

    def get_store_payment_method(self, payment_type):

        try:
            return self.storepaymentmethod_set.get(
                profile=self,
                payment_type=payment_type
            )
        except: # pylint: disable=bare-except
            return None

    def get_store_payment_method_from_reg_no(self, reg_no):

        try:
            return self.storepaymentmethod_set.get(profile=self, reg_no=reg_no)
        except: # pylint: disable=bare-except
            return None

    def get_inventory_levels(self):

        from inventories.models import StockLevel

        levels = StockLevel.objects.filter(store__profile=self).values(
            'units',
            'store__loyverse_store_id',
            'product__loyverse_variant_id'
        )

        sorted_list = [
            {
                'in_stock': str(l['units']),
                'store_id': str(l['store__loyverse_store_id']),
                'variant_id': str(l['product__loyverse_variant_id'])
            }
            for l in levels
        ]

        return {'inventory_levels': list(sorted_list)}

    def save(self, *args, **kwargs):

        # Sync User's and profile phone
        self.sync_profile_phone_and_its_user_phone()

        # If user is staff mark profile as approved
        self.mark_staff_as_approved()

        # If user is staff mark profile as approved
        if self.user.is_staff:
            self.approved = True

        """ Only Save when the user is an top user """
        if self.user.user_type == TOP_USER:

            """ Check if this object is being created """
            created = self.pk is None

            # Call the "real" save() method.
            super(Profile, self).save(*args, **kwargs)

            # Create initial image during model creation
            self.create_inital_image(created)

            # Send updated data through the websocket to the user
            self.send_profile_update_to_websocket()

            """
            To avoid using post save signal we use our custom way to know if the model
            is being created
            """
            self.create_profile_count(created)


class ProfileCount(models.Model):
    profile = models.ForeignKey(Profile,
                                on_delete=models.SET_NULL,
                                null=True,
                                blank=True,
                                )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        if self.profile:
            return self.profile.user.email
        else:
            return "No profile"

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    
    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)
    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = 'created_date'

# ========================== END Profile Models


# ========================== START Employee Profile Models
class EmployeeProfile(CommonProfileMethodsMixin, models.Model):
    # To avoid circular import error
    from stores.models import Store
    from clusters.models import StoreCluster

    # This field is required by all models that will use ApiImageUploader()
    # to upload images using REST Api
    IMAGE_SUB_DIRECTORY = settings.IMAGE_SETTINGS['profile_images_dir']

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    stores = models.ManyToManyField(Store)
    clusters = models.ManyToManyField(StoreCluster)
    image = models.ImageField(
        upload_to=profile_directory_path,
        default=settings.IMAGE_SETTINGS['no_image_url'],
        verbose_name='image',
    )
    phone = models.BigIntegerField(
        verbose_name='phone',
        # validators=[validate_phone_for_models],
        # unique=True,
        default=0
    )
    join_date = models.DateTimeField(
        verbose_name='join date',
        default=timezone.now,
        db_index=True
    )
    location = models.CharField(
        verbose_name='location',
        max_length=50,
    )
    role_name = models.CharField(
        verbose_name='role name',
        max_length=50,
        default=''
    )
    role_reg_no = models.BigIntegerField(
        verbose_name='role reg no',
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )
    unlocked = models.BooleanField(
        verbose_name='unlocked',
        default=True
    )
    loyverse_employee_id = models.UUIDField(
        verbose_name='loyverse employee id',
        db_index=True,
        null=True,
        blank=True,
    )
    loyverse_store_id = models.UUIDField(
        verbose_name='loyverse store id',
        db_index=True,
        null=True,
        blank=True,
    )
    is_api_user = models.BooleanField(
        verbose_name='is api user',
        default=False
    )


    objects = EmployeeModelManager()

    """ The CommonProfileMethodsMixin defines the following methods
    
    __str__
    get_short_name
    get_full_name
    get_join_date
    get_last_login_date
    get_profile_image_url
    get_location
    sync_profile_phone_and_its_user_phone
    send_profile_update_to_websocket
    create_inital_image
    """

    def is_employee_qualified(self):
        """ Returns true if the subscription is unlocked and it's subscription 
        has not expired
        """
        if self.unlocked and not self.subscription.expired:
            return True
        return False

    def get_due_date(self, local_timezone):
        """ Returns the tracker device subscription's due_date """
        return (self.subscription.get_due_date(local_timezone))
    # Make due_date to be filterable
    get_due_date.admin_order_field = 'subscription__due_date'

    def assign_user_group(self):
        """
        Assigns the right user group to the user
        """

        groups = UserGroup.objects.filter(
            master_user=self.profile.user,
            reg_no=self.role_reg_no,
            is_owner_group=False
        ) 

        self.user.groups.set(groups)

        if groups:
            # We do this to avoid calling the save method
            EmployeeProfile.objects.filter(reg_no=self.reg_no).update(
                role_name=groups[0].ident_name
            )

    def create_employee_profile_count(self, created):
        """
        Create EmployeeProfileCount
        """

        if created:
            EmployeeProfileCount.objects.create(
                profile=self.profile,
                employee_profile=self
            )

    def create_subscription_model(self, created):

        # Create Team Model
        if created:
            from billing.models import Subscription

            Subscription.objects.create(
                employee_profile=self,
                last_payment_date=self.join_date
            )

    def get_registered_clusters_data(self):
        """
        Returns a list of dicts with all cluster's names and reg nos for this
        employee
        """
        clusters = self.clusters.all().order_by('id').values(
            'name',
            'reg_no'
        )

        return list(clusters)
    
    def get_registered_clusters_count(self):
        """
        Returns a number of clusters already available to the model
        """
        return self.clusters.all().count()
    
    def get_available_clusters_data(self):
        """
        Returns a list of dicts with all cluster's names and reg nos that
        are available
        """
        from clusters.models import StoreCluster

        clusters = StoreCluster.objects.filter(
            profile=self.profile
        ).order_by('name').values(
            'name',
            'reg_no' 
        )

        return list(clusters) 

    def get_cluster_names_list(self):
        """
        Returns a list of clustters name(For this model)
        """
        cluster_names = self.clusters.all().order_by('name').values_list(
            'name',
            flat=True
        )

        return list(cluster_names)
    
    def add_store_to_employee(self):

        from stores.models import Store

        if self.loyverse_store_id:
            store_ids = Store.objects.filter(
                profile=self.profile,
                loyverse_store_id=self.loyverse_store_id
            ).values_list('id', flat=True)

            self.stores.add(*store_ids)

    def update_email_for_api_user(self):
        """
        Update the email of the user to be the same as the profile's email
        """

        if self.is_api_user:
            suggested_email = f'api-{self.reg_no}-{self.profile.user.email}'

            if not self.user.email == suggested_email:
                self.user.email = suggested_email
                self.user.save()

    def save(self, *args, **kwargs):

        # Sync User's and profile phone
        self.sync_profile_phone_and_its_user_phone()

        self.full_name = self.get_full_name()
        self.email = self.user.email

        """ Only Save when the user is not an top user """
        if not self.user.user_type == TOP_USER:

            """ Check if this object is being created """
            created = self.pk is None

            # Set reg no
            if created:
                self.reg_no = self.user.reg_no

            # Call the "real" save() method.
            super(EmployeeProfile, self).save(*args, **kwargs)

            # Create initial image during model creation
            self.create_inital_image(created)

            # Send updated data through the websocket to the user
            self.send_profile_update_to_websocket()

            # Assigns the right user group to the user
            self.assign_user_group()

            """
            To avoid using post save signal we use our custom way to know if the model
            is being created
            """
            
            self.create_employee_profile_count(created)
            self.create_subscription_model(created)
            self.add_store_to_employee()
            self.update_email_for_api_user()

class EmployeeProfileCount(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    employee_profile = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        if self.employee_profile:
            return self.employee_profile.user.email
        else:
            return "No profile"

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)
    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = 'created_date'


# ========================== END Employee Profile Models



# ========================== START customer models

class Customer(models.Model):
    from clusters.models import StoreCluster

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE,)
    cluster = models.ForeignKey(
        StoreCluster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name='name',
        max_length=50,
    )
    email = models.EmailField(
        verbose_name='email',
        max_length=30,
        blank=True,
        null=True,
        default=''
    )
    village_name = models.CharField(
        verbose_name='village name',
        max_length=30,
        default=''
    )
    phone = models.BigIntegerField(
        verbose_name='phone',
        validators=[validate_phone_for_models, ],
        blank=True,
        null=True,
    )
    address = models.CharField(
        verbose_name='address',
        max_length=50,
        blank=True,
        default=''
    )
    city = models.CharField(
        verbose_name='city',
        max_length=50,
        blank=True,
        default=''
    )
    region = models.CharField(
        verbose_name='region',
        max_length=50,
        blank=True,
        default=''
    )
    postal_code = models.CharField(
        verbose_name='postal code',
        max_length=50,
        blank=True,
        default=''
    )
    country = models.CharField(
        verbose_name='country',
        max_length=50,
        blank=True,
        default=''
    )
    customer_code = models.CharField(
        verbose_name='customer code',
        max_length=50,
        blank=True,
        default=''
    )
    tax_pin = models.CharField(
        verbose_name='tax pin',
        max_length=50,
        blank=True,
        default=''
    )
    credit_limit = models.DecimalField(
        verbose_name='credit limit',
        max_digits=30,
        decimal_places=2,
        blank=True,
        default=0
    )
    current_debt = models.DecimalField(
        verbose_name='current debt',
        max_digits=30,
        decimal_places=2,
        blank=True,
        default=0
    )
    points = models.IntegerField(
        verbose_name='points',
        default=0,
        validators=[MaxValueValidator(1000000000), ]
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )
    loyverse_customer_id = models.UUIDField(
        verbose_name='loyverse customer id',
        editable=False,
        db_index=True,
        null=True,
        blank=True,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        return "{}".format(self.name)

    def get_non_null_phone(self):
        """
        Retrun phone number or an empty string instead of return None
        """
        return self.phone if self.phone else ''

    def get_location_desc(self):

        desc = ''

        if self.address:
            desc += self.address

        if self.city:
            if desc:
                desc += f', {self.city}'
            else:
                desc += f'{self.city}'

        if self.region:
            if desc:
                desc += f', {self.region}'
            else:
                desc += f'{self.region}'

        if self.postal_code:
            if desc:
                desc += f', {self.postal_code}'
            else:
                desc += f'{self.postal_code}'

        if self.country:
            if desc:
                desc += f', {self.country}'
            else:
                desc += f'{self.country}'

        return desc

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_currency_initials(self):
        return self.profile.get_currency_initials()

    def get_credit_limit_desc(self):
        return f'{CURRENCY_CHOICES[0][1]} {self.credit_limit}'

    def get_current_debt_desc(self):
        return f'{CURRENCY_CHOICES[0][1]} {self.current_debt}'

    # TODO Implement this
    def get_first_visit(self):
        return "Mondy"

    # TODO Implement this
    def get_last_visit(self):
        return "Thursday"

    def get_sales_count(self):

        total_units_sum = self.receiptline_set.all().aggregate(
            Sum('units')).get('units__sum', 0)

        return total_units_sum if total_units_sum else 0

    def get_total_visits(self):
        return self.receipt_set.all().count()

    # TODO Implement this
    def get_total_spent(self):
        return "2000"

    def is_eligible_for_debt(self, debt_amount):
        """
        Returns true if the customer's is eligible for a new debt amount and 
        false otherwise
        """

        if self.credit_limit == 0:
            return False

        new_debt = self.current_debt + debt_amount

        return self.credit_limit >= new_debt

    def is_eligible_for_point_payment(self, amount):
        """
        Returns a tuple indicatiing if loyalty setting is enabled and if
        customer has enough points for a successful sale costing the passed
        amount
        """
        if self.points == 0:
            return False, False

        value = LoyaltySetting.objects.get(profile=self.profile).value

        if not value > 1:
            return False, False

        return value > 0, self.points >= amount

    def create_customer_count(self, created):

        # Create CustomerCount
        if created:
            # We input created date to ease analytics testing
            CustomerCount.objects.create(
                profile=self.profile,
                reg_no=self.reg_no,
                created_date=self.created_date
            )

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a customer creation message. Otherwise we
        send a customer edit message
        """
        from firebase.message_sender_customer import CustomerMessageSender

        if created:
            CustomerMessageSender.send_customer_creation_update_to_users(self)
        else:
            CustomerMessageSender.send_customer_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Send a customer delete message.
        """
        from firebase.message_sender_customer import CustomerMessageSender

        CustomerMessageSender.send_customer_deletion_update_to_users(self)

    def get_cluster_data(self):
        
        data = {'name': None, 'reg_no': None}

        if self.cluster:
            data['name'] = self.cluster.name
            data['reg_no'] = self.cluster.reg_no
        
        return data
    
    def send_customer_to_connector(self):
        """
        Sends customer data to connector
        """
    
        from accounts.tasks import (
            send_data_to_connector_task,
            MWINGI_CONN_CUSTOMER_REQUEST
        )

        # When testing, don't perform task in the background
        if settings.TESTING_MODE:
            send_data_to_connector_task(
                request_type=MWINGI_CONN_CUSTOMER_REQUEST,
                model_reg_no=self.reg_no
            )
        
        else:
            send_data_to_connector_task.delay(
                request_type=MWINGI_CONN_CUSTOMER_REQUEST,
                model_reg_no=self.reg_no
            )


    def save(self, *args, **kwargs):

        if not self.name:
            self.name = "No name"

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Supply customer code if it's empty
        if not self.customer_code:
            self.customer_code = f'Cu_{self.reg_no}'

        """ Check if this object is being created """
        created = self.pk is None

        # Call the "real" save() method.
        super(Customer, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.points = int(self.points)
        self.send_firebase_update_message(created)

        self.create_customer_count(created)

        # Send customer data to connector
        self.send_customer_to_connector()

    def delete(self, *args, **kwargs):
        # Call the "real" delete() method.
        super(Customer, self).delete(*args, **kwargs)

        self.send_firebase_delete_message()


class CustomerCount(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        if self.profile:
            return self.profile.user.email
        else:
            return "No profile"

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'


# ========================== END customer models



# ========================== START loyalty setting Models

class LoyaltySetting(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
    )
    value = models.DecimalField(
        verbose_name='value',
        max_digits=30,
        decimal_places=2,
        default=0,
        validators=[MaxValueValidator(100), MinValueValidator(0)]
    )

    def send_firebase_update_message(self):
        """
        sends a loyalty setting edit message
        """
        from firebase.message_sender_loyalty_settings import LoyaltySettingsMessageSender

        LoyaltySettingsMessageSender.send_model_update_to_users(self)

    def save(self, *args, **kwargs):

        # Call the "real" save() method.
        super(LoyaltySetting, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.send_firebase_update_message()

# ========================== END loyalty setting models


# ========================== START receipt setting Models

class ReceiptSetting(models.Model):
    # To avoid circular import error
    from stores.models import Store

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    header1 = models.CharField(
        verbose_name='header1',
        max_length=40,
        blank=True,
        default=''
    )
    header2 = models.CharField(
        verbose_name='header2',
        max_length=40,
        blank=True,
        default=''
    )
    header3 = models.CharField(
        verbose_name='header3',
        max_length=40,
        blank=True,
        default=''
    )
    header4 = models.CharField(
        verbose_name='header4',
        max_length=40,
        blank=True,
        default=''
    )
    header5 = models.CharField(
        verbose_name='header5',
        max_length=40,
        blank=True,
        default=''
    )
    header6 = models.CharField(
        verbose_name='header6',
        max_length=40,
        blank=True,
        default=''
    )
    footer1 = models.CharField(
        verbose_name='footer1',
        max_length=50,
        blank=True,
        default=''
    )
    footer2 = models.CharField(
        verbose_name='footer2',
        max_length=50,
        blank=True,
        default=''
    )
    footer3 = models.CharField(
        verbose_name='footer3',
        max_length=50,
        blank=True,
        default=''
    )
    footer4 = models.CharField(
        verbose_name='footer4',
        max_length=50,
        blank=True,
        default=''
    )
    footer5 = models.CharField(
        verbose_name='footer5',
        max_length=50,
        blank=True,
        default=''
    )
    footer6 = models.CharField(
        verbose_name='footer6',
        max_length=50,
        blank=True,
        default=''
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )

    def get_image_url(self):
        """
        Return image url or an empty string
        """
        try:
            return self.image.url

        # pylint: disable=bare-except
        except:
            return ""

    def save(self, *args, **kwargs):
        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(ReceiptSetting, self).save(*args, **kwargs)

# ========================== END receipt setting models


# ========================== START user general setting models

class UserGeneralSetting(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
    )
    enable_shifts = models.BooleanField(
        verbose_name='enable shifts',
        default=False
    )
    enable_open_tickets = models.BooleanField(
        verbose_name='enable open tickets',
        default=False
    )
    enable_low_stock_notifications = models.BooleanField(
        verbose_name='enable low stock notifications',
        default=True
    )
    enable_negative_stock_alerts = models.BooleanField(
        verbose_name='enable negative stock alerts',
        default=True
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
        editable=False
    )

    def __str__(self):
        return 'General settings'

    def get_settings_dict(self):

        return {
            'enable_shifts': self.enable_shifts, 
            'enable_open_tickets': self.enable_open_tickets, 
            'enable_low_stock_notifications': self.enable_low_stock_notifications,
            'enable_negative_stock_alerts': self.enable_negative_stock_alerts
        }

    def send_firebase_update_message(self):
        """
        Send an edit message
        """
        from firebase.message_sender_user_general_settings import UserGeneralSettingMessageSender

        UserGeneralSettingMessageSender.send_model_update_to_users(self)

    def save(self, *args, **kwargs):
        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(UserGeneralSetting, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.send_firebase_update_message()

# ========================== END user general setting models

