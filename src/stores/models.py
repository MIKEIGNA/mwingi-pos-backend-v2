from decimal import Decimal

from django.db.models import OuterRef
from django.contrib.auth import get_user_model
from django.db.models.aggregates import Sum, Count
from django.db.models.expressions import Case, When, Value
from django.db.models.fields import DecimalField
from django.utils import timezone
from django.db import models
from django.conf import settings
from django.db.models.functions import Coalesce

from core.queryset_helpers import QuerysetFilterHelpers
from core.time_utils.date_helpers import DateHelperMethods
from core.time_utils.time_localizers import utc_to_local_datetime_with_format
from core.utils.dict_utils import DictUtils

from profiles.models import Profile
from accounts.utils.validators import validate_code, validate_percentage

# ========================== START Store Models
class Store(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name='name',
        max_length=100,
        # db_collation="case_insensitive"
    )
    address = models.CharField(
        verbose_name='address',
        max_length=50,
        default='',
        blank=True
    )
    loyverse_store_id = models.UUIDField(
        verbose_name='loyverse store id',
        editable=False,
        db_index=True,
        null=True,
        blank=True,
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        # unique=True,
        default=0,
    )
    is_shop = models.BooleanField(
        verbose_name='is shop',
        default=False
    )
    is_truck = models.BooleanField(
        verbose_name='is truck',
        default=False
    )
    is_warehouse = models.BooleanField(
        verbose_name='is warehouse',
        default=False
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now
    )

    till_number = models.IntegerField(
        verbose_name='till number',
        # unique=True,
        default=0,
    )

    #### Extra data for shallow delete 
    is_deleted = models.BooleanField(
        verbose_name='is deleted',
        default=False
    )
    deleted_date = models.DateTimeField(
        verbose_name='deleted date',
        default=timezone.make_aware(
            DateHelperMethods.get_date_from_date_str(
                settings.DEFAULT_START_DATE
            )
        )
    )
    created_date_str = models.CharField(
        verbose_name='created date str',
        max_length=32,
        default='',
        blank=True
    )
    deleted_date_str = models.CharField(
        verbose_name='deleted date str',
        max_length=32,
        default='',
        blank=True
    )

    #### Fields for tally
    synced_with_tally = models.BooleanField(
        verbose_name='synced with tally',
        default=False
    )
    

    def __str__(self):
        """ Returns the store's name as a string"""
        return str(self.name)

    def get_profile(self):
        """ Returns the store's profile"""
        return self.profile

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_deleted_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.deleted_date, local_timezone)
    # Make deleted_date to be filterable
    get_deleted_date.admin_order_field = 'deleted_date'

    def get_employee_count(self):
        """
        Returns the number of employees in the store
        """
        return self.employeeprofile_set.all().count()

    def get_receipt_setting(self):

        setting = self.receiptsetting_set.get()

        return {
            'header1': setting.header1,
            'header2': setting.header2,
            'header3': setting.header3,
            'header4': setting.header4,
            'header5': setting.header5,
            'header6': setting.header6,

            'footer1': setting.footer1,
            'footer2': setting.footer2,
            'footer3': setting.footer3,
            'footer4': setting.footer4,
            'footer5': setting.footer5,
            'footer6': setting.footer6,
        }

    def create_store_count_model(self):
        """
        Create StoreCount
        """
        # We input created date to ease analytics testing
        StoreCount.objects.create(
            profile=self.profile,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def create_receipt_setting_model(self):

        from profiles.models import ReceiptSetting
        
        ReceiptSetting.objects.create(
            profile=self.profile,
            store=self,
        )

    def increment_increamental_id(self, created):

        if not created: return

        last_store = StoreCount.objects.filter(
            profile=self.profile
        ).order_by('increamental_id').last()

        if last_store:
            self.increamental_id = last_store.increamental_id + 1
        else:
            self.increamental_id = 100

    def update_store_type(self):
        """
        Updates store's type
        """

        if 'truck' in self.name.lower() or 'b2b' in self.name.lower():
            self.is_truck = True

            self.is_shop = False
            self.is_warehouse = False

        elif 'warehouse' in self.name.lower():
            self.is_warehouse = True

            self.is_shop = False
            self.is_truck = False

        else:
            self.is_shop = True

            self.is_truck = False
            self.is_warehouse = False
            
    def create_stock_levels_for_all_products(self):
        """
        Creates stock levels for all products when store is created
        """

        from products.models import Product

        products = Product.objects.filter(profile=self.profile)

        for product in products:product.stores.add(self)

    def soft_delete(self):
        """
        Soft deletes the store
        """

        self.is_deleted = True
        self.deleted_date = timezone.now()
        self.save()

    def update_date_str_fields(self):
        """
        Updates date string fields to this format 2023-11-26T17:16:43.339701Z
        """

        self.created_date_str = self.created_date.isoformat()
        self.deleted_date_str = self.deleted_date.isoformat()

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Increament increamental_id
        self.increment_increamental_id(created)

        # Updates store type
        self.update_store_type()

        # Update date string fields
        self.update_date_str_fields()

        # Call the "real" save() method.
        super(Store, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        if created:
            self.create_store_count_model()
            self.create_receipt_setting_model()
            self.create_stock_levels_for_all_products()

class StoreCount(models.Model):
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
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        # unique=True,
        default=0,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def increment_increamental_id(self, created):

        if not created: return

        last_store = StoreCount.objects.filter(
            profile=self.profile
        ).order_by('increamental_id').last()

        if last_store:
            self.increamental_id = last_store.increamental_id + 1
        else:
            self.increamental_id = 100

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Increament increamental_id
        self.increment_increamental_id(created)

        super(StoreCount, self).save(*args, **kwargs)

# ========================== END Store Models


# ========================== START user payment methods models

class StorePaymentMethod(models.Model):
    # To avoid mismatch errors, this constants number values should match
    # PAYMENT_CHOICES ordering
    CASH_TYPE = 0
    MPESA_TYPE = 1
    CARD_TYPE = 2
    POINTS_TYPE = 3
    DEBT_TYPE = 4
    OTHER_TYPE = 5

    PAYMENT_CHOICES = [
        (CASH_TYPE, 'Cash'),
        (MPESA_TYPE, 'Mpesa'),
        (CARD_TYPE, 'Card'),
        (POINTS_TYPE, 'Points'),
        (DEBT_TYPE, 'Debt'),
        (OTHER_TYPE, 'Others')
    ]

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    payment_type = models.IntegerField(
        verbose_name='payment type',
        choices=PAYMENT_CHOICES,
        default=0
    )
    name = models.CharField(
        verbose_name='name',
        max_length=30,
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
    )

    def __str__(self):
        """ Returns the store's name as a string"""
        return str(self.name)

    def get_profile(self):
        """ Returns the store's profile"""
        return self.profile

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):

        queryset = self.receiptpayment_set.all()
        
        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'receipt__created_date', 
            date_after, 
            date_before,
            local_timezone
        )

        if store_reg_nos:
            queryset = queryset.filter(receipt__store__reg_no__in=store_reg_nos)

        if user_reg_nos:
            queryset = queryset.filter(receipt__user__reg_no__in=user_reg_nos)

        data = queryset.aggregate(
            count=Count('id'),
            total_amount=Coalesce(Sum('amount'), Decimal(0.00)),
            refund_amount=Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then='amount'),
                        default=0,
                        output_field=DecimalField()
                    )
                ),
                Decimal(0.00)
            ),
            refund_count=Coalesce(
                Sum(
                    Case(
                        When(receipt__is_refund=True, then=Value(1)),
                    default=0,
                    )
                ),
                0
            )
        )

        return {
            'name': self.name,
            'count': data['count'],
            'amount': str(round(data['total_amount'], 2)),
            'refund_count': data['refund_count'],
            'refund_amount': str(round(data['refund_amount'], 2)),
        }        

    def save(self, *args, **kwargs):

        if self.payment_type == StorePaymentMethod.CASH_TYPE:
            self.name = "Cash"

        elif self.payment_type == StorePaymentMethod.MPESA_TYPE:
            self.name = "Mpesa"

        elif self.payment_type == StorePaymentMethod.CARD_TYPE:
            self.name = "Card"

        elif self.payment_type == StorePaymentMethod.POINTS_TYPE:
            self.name = "Points"

        elif self.payment_type == StorePaymentMethod.DEBT_TYPE:
            self.name = "Debt"

        else:
            self.name = "Other"

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(StorePaymentMethod, self).save(*args, **kwargs)


# ========================== END user payment methods models

# ========================== START tax models
class Tax(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    stores = models.ManyToManyField(Store)
    name = models.CharField(
        verbose_name='name',
        max_length=30,
    )
    rate = models.DecimalField(
        verbose_name='rate',
        max_digits=30,
        decimal_places=2,
        validators=[validate_percentage, ],
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
    )
    loyverse_tax_id = models.UUIDField(
        verbose_name='loyverse tax id',
        editable=False,
        db_index=True,
        null=True,
        blank=True,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True
    )

    class Meta:
        verbose_name_plural = "taxes"

    def __str__(self):
        """ Returns the tax's name as a string"""
        return str(self.name)

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def create_tax_count_model(self):
        """
        Create TaxCount
        """
        # We input created date to ease analytics testing
        TaxCount.objects.create(
            profile=self.profile,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a tax creation message. Otherwise we
        send a tax edit message
        """
        from firebase.message_sender_tax import TaxMessageSender

        if created:
            TaxMessageSender.send_tax_creation_update_to_users(self)
        else:
            TaxMessageSender.send_tax_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Send a tax delete message.
        """
        from firebase.message_sender_tax import TaxMessageSender
        
        TaxMessageSender.send_tax_deletion_update_to_users(self)

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):
        
        queryset = self.receipt_set.all()

        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'created_date', 
            date_after, 
            date_before,
            local_timezone
        )

        if store_reg_nos:
            queryset = queryset.filter(store__reg_no__in=store_reg_nos)

        if user_reg_nos:
            queryset = queryset.filter(user__reg_no__in=user_reg_nos)

        amount = queryset.aggregate(
            amount=Coalesce(Sum('tax_amount'), Decimal(0.00)))['amount']

        return {
            'name': self.name,
            'rate': str(self.rate),
            'amount': str(round(amount, 2))
        }

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(Tax, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.send_firebase_update_message(created)

        if created:
            self.create_tax_count_model()

    def delete(self, *args, **kwargs):
        # Call the "real" delete() method.
        super(Tax, self).delete(*args, **kwargs)
        
        self.send_firebase_delete_message()

class TaxCount(models.Model):
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
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'


# ========================== END tax models


# ========================== START category models

class Category(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name='name',
        max_length=30,
    )
    color_code = models.CharField(
        verbose_name='color code',
        max_length=7,
        default=settings.DEFAULT_COLOR_CODE,
        validators=[validate_code, ],
    )
    product_count = models.IntegerField(
        verbose_name='product count',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
    )
    loyverse_category_id = models.UUIDField(
        verbose_name='loyverse category id',
        editable=False,
        db_index=True,
        null=True,
        blank=True,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True
    )

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        """ Returns the category's name as a string"""
        return str(self.name)

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def create_category_count_model(self):
        """
        Create CategoryCount
        """
        # We input created date to ease analytics testing
        CategoryCount.objects.create(
            profile=self.profile,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a category creation message. Otherwise we
        send a category edit message
        """
        from firebase.message_sender_category import CategoryMessageSender

        if created:
            CategoryMessageSender.send_category_creation_update_to_users(self)
        else:
            CategoryMessageSender.send_category_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Send a category delete message.
        """
        from firebase.message_sender_category import CategoryMessageSender
        
        CategoryMessageSender.send_category_deletion_update_to_users(self)

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):

        # We import here to avoid cyclic imports error
        from sales.models import ReceiptLine
        
        queryset = ReceiptLine.objects.filter(product__category=self)

        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'receipt__created_date', 
            date_after, 
            date_before,
            local_timezone
        )

        if store_reg_nos:
            if (not type(store_reg_nos) == list):
                store_reg_nos = [store_reg_nos]
            queryset = queryset.filter(receipt__store__reg_no__in=store_reg_nos)

        if user_reg_nos:
            if (not type(user_reg_nos) == list):
                user_reg_nos = [user_reg_nos]
            queryset = queryset.filter(receipt__user__reg_no__in=user_reg_nos)

        queryset = queryset.aggregate(
            items_sold=Coalesce(Sum('units'), Decimal(0.00)),
            net_sales=Coalesce(Sum('price'), Decimal(0.00)),
            cost=Coalesce(Sum('cost'), Decimal(0.00)),
        )

        net_sales = round(queryset['net_sales'], 2)
        cost = round(queryset['cost'], 2)
        profit = net_sales - cost

        return {
            'name': self.name,
            'items_sold': str(queryset['items_sold']),
            'net_sales': str(net_sales),
            'cost': str(cost),
            'profit': str(round(profit, 2))
        }

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None
        
        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(Category, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.send_firebase_update_message(created)
        
        if created:
            self.create_category_count_model()

        # Update product count
        Category.objects.filter(
            pk=self.pk
        ).update(product_count=self.product_set.all().count())
            
    def delete(self, *args, **kwargs):
        # Call the "real" delete() method.
        super(Category, self).delete(*args, **kwargs)
        
        self.send_firebase_delete_message()


class CategoryCount(models.Model):
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
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

# ========================== END category models


# ========================== START discount models
class Discount(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    stores = models.ManyToManyField(Store)
    name = models.CharField(
        verbose_name='name',
        max_length=30,
    )
    value = models.DecimalField(
        verbose_name='value',
        max_digits=30,
        decimal_places=2,
        default=0,
        validators=[validate_percentage, ],
    )
    amount = models.DecimalField(
        verbose_name='amount',
        max_digits=30,
        decimal_places=2,
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True
    )

    def __str__(self):
        """ Returns the discount's name as a string"""
        return str(self.name)

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def create_discount_count_model(self):
        """
        Create DiscountCount
        """
        # We input created date to ease analytics testing
        DiscountCount.objects.create(
            profile=self.profile,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a discount creation message. Otherwise we
        send a discount edit message
        """
        from firebase.message_sender_discount import DiscountMessageSender

        if created:
            DiscountMessageSender.send_discount_creation_update_to_users(self)
        else:
            DiscountMessageSender.send_discount_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Send a discount delete message.
        """
        from firebase.message_sender_discount import DiscountMessageSender
        
        DiscountMessageSender.send_discount_deletion_update_to_users(self)

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):
        
        queryset = self.receipt_set.all()

        # Filters queryset with date range of the passed date field name
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset, 
            'created_date', 
            date_after, 
            date_before,
            local_timezone
        )

        if store_reg_nos:
            if (not type(store_reg_nos) == list):
                store_reg_nos = [store_reg_nos]
            queryset = queryset.filter(store__reg_no__in=store_reg_nos)

        if user_reg_nos:
            if (not type(user_reg_nos) == list):
                user_reg_nos = [user_reg_nos]   
            queryset = queryset.filter(user__reg_no__in=user_reg_nos)

        amount = queryset.aggregate(
            amount=Coalesce(Sum('discount_amount'), Decimal(0.00)))['amount']

        return {
            'name': self.name,
            'count': queryset.count(),
            'amount': str(round(amount, 2))
        }

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(Discount, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created 
        """
        self.send_firebase_update_message(created)

        if created:
            self.create_discount_count_model()
            
    def delete(self, *args, **kwargs):
        # Call the "real" delete() method.
        super(Discount, self).delete(*args, **kwargs)
        
        self.send_firebase_delete_message()

class DiscountCount(models.Model):
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
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'


# ========================== END discount models
