#pylint: disable=no-name-in-module

from decimal import Decimal

from django.conf import settings
from django.db.models.aggregates import Sum
from django.db.models.functions import Coalesce
from django.db.models import F, Case, When, Value, DecimalField
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from core.logger_manager import LoggerManager
from core.number_helpers import NumberHelpers

from core.time_utils.date_helpers import DateHelperMethods
from core.time_utils.time_localizers import utc_to_local_datetime_with_format


from products.models import Product
from profiles.models import Profile
from stores.models import Store

from accounts.utils.validators import validate_phone_for_models
from accounts.utils.user_type import EMPLOYEE_USER

class StockLevel(models.Model):

    # Stock level update type
    STOCK_LEVEL_UPDATE_ADDING = 0
    STOCK_LEVEL_UPDATE_SUBSTRACTING = 1
    STOCK_LEVEL_UPDATE_OVERWRITING = 2

    # Stock level state
    STOCK_LEVEL_IN_STOCK = 0
    STOCK_LEVEL_LOW_STOCK = 1
    STOCK_LEVEL_OUT_OF_STOCK = 2

    STOCK_LEVEL_STATUS_CHOICES = [
        (
            STOCK_LEVEL_IN_STOCK,
            "In stock",
        ),
        (
            STOCK_LEVEL_LOW_STOCK,
            "Low stock",
        ),
        (
            STOCK_LEVEL_OUT_OF_STOCK,
            "Out of stock",
        ),
    ]

    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    minimum_stock_level = models.IntegerField(
        verbose_name="minimum stock level",
        default=0,
    )
    units = models.DecimalField(
        verbose_name="units", 
        max_digits=30, 
        decimal_places=2, 
        default=0
    )
    price = models.DecimalField(
        verbose_name="price", 
        max_digits=30, 
        decimal_places=2, 
        default=0
    )
    status = models.IntegerField(
        verbose_name="status",
        choices=STOCK_LEVEL_STATUS_CHOICES,
        default=STOCK_LEVEL_IN_STOCK,
    )
    is_sellable = models.BooleanField(
        verbose_name='is sellable',
        default=True
    )
    inlude_in_price_calculations = models.BooleanField(
        verbose_name='inlude in price calculations',
        default=True
    )
    last_change_source_reg_no = models.BigIntegerField(
        verbose_name="last change source reg no",
        default=0,
    )

    # For faster queries
    loyverse_store_id = models.UUIDField(
        verbose_name='loyverse store id',
        # editable=False,
        db_index=True,
        null=True,
        blank=True,
    )
    loyverse_variant_id = models.UUIDField(
        verbose_name='loyverse variant id',
        # editable=False,
        db_index=True,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f'{self.product.name} {self.store.name}'

    def send_firebase_update_message(self, notify_low_stock):
        from firebase.message_sender_stock_levels import StockLevelsMessageSender

        StockLevelsMessageSender.send_model_update_to_users(self, notify_low_stock)


    @staticmethod
    def update_inventory_valuation_line(
        store,
        product,
        current_units,
        created_date
    ):
        
        from inventories.models.inventory_valuation_models import InventoryValuationLine
        

        try:

            inventory_value=current_units * F('cost')
            retail_value=current_units * F('price')
            margin = ((retail_value - inventory_value) * 100) / retail_value


            if current_units != 0:
                margin=Case(
                    When(price=0, cost=0, then=Value(0.0)),  # Handle the case when both price and cost are zero
                    When(price=0, then=Value(0.0)),  # Handle the case when price is zero
                    When(cost=0, then=Value(100.0)),  # Handle the case when cost is zero
                    default=((retail_value - inventory_value) * 100) / retail_value,
                    output_field=DecimalField()
                )
            else:
                margin = 0.0

            InventoryValuationLine.objects.filter(
                store=store, 
                product=product, 
                inventory_valution__created_date__date=created_date
            ).update(
                units=current_units,
                inventory_value=inventory_value,
                retail_value=retail_value,
                potential_profit=retail_value - inventory_value,
                margin=margin
            )
            
        except Exception as e:
            LoggerManager.log_critical_error(additional_message=str(e))
        
        

    @staticmethod
    def update_level_deprecated(
        user,
        store,
        product,
        inventory_history_reason,
        change_source_reg_no,
        line_source_reg_no,
        change_source_name,
        adjustment,
        update_type=True,
        created_date=None
    ):
        
        if not created_date:
            created_date = timezone.now()
            
        # Check if inventory history exists
        inventory_exits = InventoryHistory.objects.filter(line_source_reg_no=line_source_reg_no).exists()
        if inventory_exits: return

        history = InventoryHistory.objects.create(
            user=user,
            store=store,
            product=product,
            reason=inventory_history_reason,
            change_source_reg_no=change_source_reg_no,
            change_source_name=change_source_name,
            line_source_reg_no=line_source_reg_no,
            adjustment=0,
            stock_after=0,
            created_date=created_date,
            stock_was_deducted=False
        )

        inventory_count = InventoryHistory.objects.filter(line_source_reg_no=line_source_reg_no).count()
        if inventory_count > 1: return

        try:
            stock_level = StockLevel.objects.get(store=store, product=product)
 
            difference = adjustment

            if update_type == StockLevel.STOCK_LEVEL_UPDATE_ADDING:
                
                stock_level.units += Decimal(adjustment)
                stock_level.save()

                # Update inventory valuation line
                if inventory_history_reason == InventoryHistory.INVENTORY_HISTORY_REFUND:
                    StockLevel.update_inventory_valuation_line(
                        store=store,
                        product=product,
                        current_units=stock_level.units,
                        created_date=created_date
                    )

            elif update_type == StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING:
                stock_level.units -= Decimal(adjustment)
                stock_level.save()
                
                # If we are subtracting, we turn adjustment into a negative
                difference = 0 - adjustment

                # Update inventory valuation line
                if inventory_history_reason == InventoryHistory.INVENTORY_HISTORY_SALE:
                    StockLevel.update_inventory_valuation_line(
                        store=store,
                        product=product,
                        current_units=stock_level.units,
                        created_date=created_date
                    )

            else:

                # We calculate the added/subtracted difference
                initial_units = stock_level.units
                difference = adjustment - initial_units

                stock_level.units = adjustment
                stock_level.save()

            # Update the new fields
            InventoryHistory.objects.filter(id=history.id).update(
                adjustment=difference,
                stock_after=stock_level.units,
                stock_was_deducted=True
            )

        except Exception as e:

            data = {
                'user': user.get_full_name(),
                'store': store.name,
                'product': product.name,
                'inventory_history_reason': inventory_history_reason,
                'change_source_reg_no': change_source_reg_no,
                'change_source_name': change_source_name,
                'adjustment': str(adjustment),
                'update_type': update_type,
                'created_date': str(created_date),
                'exception': e
            }
            
            LoggerManager.log_critical_error(additional_message=str(data))

    @staticmethod
    def update_level(
        user,
        store,
        product,
        inventory_history_reason,
        change_source_reg_no,
        line_source_reg_no,
        change_source_name,
        adjustment,
        update_type=True,
        created_date=None
    ):
        
        if not created_date:
            created_date = timezone.now()
            
        # Check if inventory history exists
        inventory_exits = InventoryHistory.objects.filter(line_source_reg_no=line_source_reg_no).exists()
        if inventory_exits: return

        try:
            stock_level = StockLevel.objects.get(store=store, product=product)
 
            difference = adjustment

            if update_type == StockLevel.STOCK_LEVEL_UPDATE_ADDING:
                
                stock_level.units += Decimal(adjustment)
                stock_level.save()

            elif update_type == StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING:
                stock_level.units -= Decimal(adjustment)
                stock_level.save()
                
                # If we are subtracting, we turn adjustment into a negative
                difference = 0 - adjustment

            else:

                # We calculate the added/subtracted difference
                initial_units = stock_level.units
                difference = adjustment - initial_units

                stock_level.units = adjustment
                stock_level.save()

            # Update inventory valuation
            StockLevel.update_inventory_valuation_line(
                store=store,
                product=product,
                current_units=stock_level.units,
                created_date=created_date
            )

            # Create Inventory history
            InventoryHistory.objects.create(
                user=user,
                store=store,
                product=product,
                reason=inventory_history_reason,
                change_source_reg_no=change_source_reg_no,
                change_source_name=change_source_name,
                line_source_reg_no=line_source_reg_no,
                adjustment=difference,
                stock_after=stock_level.units,
                created_date=created_date,
            )

        except Exception as e:

            data = {
                'user': user.get_full_name(),
                'store': store.name,
                'product': product.name,
                'inventory_history_reason': inventory_history_reason,
                'change_source_reg_no': change_source_reg_no,
                'change_source_name': change_source_name,
                'adjustment': str(adjustment),
                'update_type': update_type,
                'created_date': str(created_date),
                'exception': e
            }
            
            LoggerManager.log_critical_error(additional_message=str(data))

    @staticmethod
    def perform_item_edit(
        user,
        store,
        product,
        units,
        minimum_stock
    ):

        stock_level = StockLevel.objects.get(
            product=product, 
            store=store
        )

        # We calculate the added/subtracted difference
        initial_units = stock_level.units
        difference = units - initial_units

        stock_level.units = units
        stock_level.minimum_stock_level = minimum_stock
        stock_level.save()

        # Create Inventory history
        InventoryHistory.objects.create(
            user=user,
            store=store,
            product=product,
            reason=InventoryHistory.INVENTORY_HISTORY_ITEM_EDIT,
            change_source_reg_no=0,
            adjustment=difference,
            stock_after=stock_level.units,
        )

    def send_is_not_sellabel_notification(self):
        pass

    def update_uuids(self):
        """
        Upadates Loyverse store and product uuids
        """

        if not self.loyverse_store_id:
            self.loyverse_store_id = self.store.loyverse_store_id

        if not self.loyverse_variant_id:
            self.loyverse_variant_id = self.product.loyverse_variant_id

    def send_stock_data_to_mwingi_connector(self):
        """
        Sends stock data to mwingi connector
        """

        from accounts.tasks import (
            send_data_to_connector_task,
            MWINGI_CONN_INVENTORY_REQUEST
        )

        payload = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'units': str(self.units), 
                    'loyverse_store_id': str(self.loyverse_store_id),
                    'loyverse_variant_id': str(self.loyverse_variant_id)
                }
            ]
        }

        # When testing, don't perform task in the background
        # if settings.TESTING_MODE:
        #     send_data_to_connector_task(
        #         request_type=MWINGI_CONN_INVENTORY_REQUEST,
        #         model_reg_no=0,
        #         payload=payload
        #     )
        
        # else:
        #     send_data_to_connector_task.delay(
        #         request_type=MWINGI_CONN_INVENTORY_REQUEST,
        #         model_reg_no=0,
        #         payload=payload
        #     )

        send_data_to_connector_task(
            request_type=MWINGI_CONN_INVENTORY_REQUEST,
            model_reg_no=0,
            payload=payload
        )

    def get_product_profile(self):
        return self.product.profile

    def save(self, *args, **kwargs):
        """Check if this object is being created"""
        created = self.pk is None
        notify_low_stock = False

        # Upadates Loyverse store and product uuids
        self.update_uuids()

        if self.product.track_stock:
            if self.units < 1:
                self.status = StockLevel.STOCK_LEVEL_OUT_OF_STOCK

            elif self.units < self.minimum_stock_level:
                # Only notify low stock when stock has changed from in stock to
                # low stock
                notify_low_stock = self.status == StockLevel.STOCK_LEVEL_IN_STOCK
                self.status = StockLevel.STOCK_LEVEL_LOW_STOCK

            else:
                self.status = StockLevel.STOCK_LEVEL_IN_STOCK

        else:
            self.status = StockLevel.STOCK_LEVEL_IN_STOCK

        if not created:
            self.send_firebase_update_message(notify_low_stock)

        # Call the "real" save() method.
        super(StockLevel, self).save(*args, **kwargs)

        # Send stock data to mwingi connector
        self.send_stock_data_to_mwingi_connector()


# ========================== START supplier models
class Supplier(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    name = models.CharField(verbose_name="name", max_length=50)
    email = models.EmailField(
        verbose_name="email", max_length=30, blank=True, default=""
    )
    phone = models.BigIntegerField(
        verbose_name="phone",
        validators=[
            validate_phone_for_models,
        ],
        blank=True,
        null=True,
    )
    address = models.CharField(
        verbose_name="address", max_length=50, blank=True, default=""
    )
    city = models.CharField(verbose_name="city", max_length=50, blank=True, default="")
    region = models.CharField(
        verbose_name="region", max_length=50, blank=True, default=""
    )
    postal_code = models.CharField(
        verbose_name="postal code", max_length=50, blank=True, default=""
    )
    country = models.CharField(
        verbose_name="country", max_length=50, blank=True, default=""
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no", unique=True, default=0, editable=False
    )
    created_date = models.DateTimeField(
        verbose_name="created date",
        default=timezone.now,
    )

    def __str__(self):
        return "{}".format(self.email)

    def get_non_null_phone(self):
        """
        Retrun phone number or an empty string instead of return None
        """
        return self.phone if self.phone else ""

    def get_location_desc(self):
        desc = ""

        if self.address:
            desc += self.address

        if self.city:
            if desc:
                desc += f", {self.city}"
            else:
                desc += f"{self.city}"

        if self.region:
            if desc:
                desc += f", {self.region}"
            else:
                desc += f"{self.region}"

        if self.country:
            if desc:
                desc += f", {self.country}"
            else:
                desc += f"{self.country}"

        return desc

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    # Make created_date to be filterable
    get_created_date.admin_order_field = "created_date"

    def create_supplier_count(self, created):
        # Create SupplierCount
        if created:
            # We input created date to ease analytics testing
            SupplierCount.objects.create(
                profile=self.profile, reg_no=self.reg_no, created_date=self.created_date
            )

    def save(self, *args, **kwargs):
        """If reg_no is 0 get a unique reg_no"""
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        """ Check if this object is being created """
        created = self.pk is None

        # Call the "real" save() method.
        super(Supplier, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        if created:
            self.create_supplier_count(created)


class SupplierCount(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no", unique=True, default=0, editable=False
    )
    created_date = models.DateTimeField(
        verbose_name="created date",
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
    get_created_date.admin_order_field = "created_date"


# ========================== END supplier models

# ========================== START stock adjustment models

class StockAdjustment(models.Model):
    STOCK_ADJUSTMENT_RECEIVE_ITEMS = 0
    STOCK_ADJUSTMENT_LOSS = 1
    STOCK_ADJUSTMENT_DAMAGE = 2
    STOCK_ADJUSTMENT_EXPIRY = 3

    STOCK_ADJUSTMENT_REASON_CHOICES = [
        (
            STOCK_ADJUSTMENT_RECEIVE_ITEMS,
            "Receive items",
        ),
        (
            STOCK_ADJUSTMENT_LOSS,
            "Loss",
        ),
        (
            STOCK_ADJUSTMENT_DAMAGE,
            "Damage",
        ),
        (
            STOCK_ADJUSTMENT_EXPIRY,
            "Expiry",
        ),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    notes = models.CharField(
        verbose_name="notes", max_length=500, blank=True, default=""
    )
    reason = models.IntegerField(
        verbose_name="reason",
        choices=STOCK_ADJUSTMENT_REASON_CHOICES,
    )
    quantity = models.DecimalField(
        verbose_name="quantity", max_digits=30, decimal_places=2, default=0
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )

    def __str__(self):
        return f"SA{self.increamental_id}"

    def get_str_quantity(self):
        return str(self.quantity)

    def get_adjusted_by(self):
        return self.user.get_full_name()

    def get_reason_desc(self):
        return StockAdjustment.STOCK_ADJUSTMENT_REASON_CHOICES[int(self.reason)][1]

    def get_store_name(self):
        return self.store.name

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)

    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = "created_date"

    def get_line_data(self):
        line_queryset = list(
            self.stockadjustmentline_set.all()
            .order_by("id")
            .values(
                "product_info",
                "add_stock",
                "remove_stock",
                "cost",
            )
        )

        lines = []
        for line in line_queryset:
            lines.append(
                {
                    "product_info": line["product_info"],
                    "add_stock": str(line["add_stock"]),
                    "remove_stock": str(line["remove_stock"]),
                    "cost": str(line["cost"]),
                }
            )

        return lines
    
    def increment_increamental_id(self, created, count_user):

        if not created: return

        last_model = StockAdjustmentCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def create_transfer_order_count_model(self, count_user):
        """
        Create StockAdjustmentCount
        """
        # We input created date to ease analytics testing
        StockAdjustmentCount.objects.create(
            user=count_user,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        # Increament increamental_id
        self.increment_increamental_id(created, count_user)

        """If reg_no is 0 get a unique reg_no"""
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(StockAdjustment, self).save(*args, **kwargs)

        if created:
            self.create_transfer_order_count_model(count_user)


class StockAdjustmentCount(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
        default=0,
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        default=0,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        return f'SA Count ({self.user})'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def increment_increamental_id(self, created):

        if not created: return

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        last_model = StockAdjustmentCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Increament increamental_id
        self.increment_increamental_id(created)

        super(StockAdjustmentCount, self).save(*args, **kwargs)




class StockAdjustmentLine(models.Model):
    stock_adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_info = models.JSONField(verbose_name="product info", default=dict)
    add_stock = models.DecimalField(
        verbose_name="add stock", max_digits=30, decimal_places=2, default=0
    )
    counted_stock = models.DecimalField(
        verbose_name="expected stock", max_digits=30, decimal_places=2, default=0
    )
    remove_stock = models.DecimalField(
        verbose_name="remove stock", max_digits=30, decimal_places=2, default=0
    )
    cost = models.DecimalField(
        verbose_name="cost", max_digits=30, decimal_places=2, default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        default=0,
        editable=False,
    )

    #### Fields for tally
    synced_with_tally = models.BooleanField(
        verbose_name='synced with tally',
        default=False
    )

    def __str__(self):
        return self.product.name

    def update_stock_level(self, created):
        if not created:
            return
        
        change_source_name = self.stock_adjustment.__str__()

        try:
            
            if (
                self.stock_adjustment.reason
                == StockAdjustment.STOCK_ADJUSTMENT_RECEIVE_ITEMS
            ):

                product = self.product

                total_units = StockLevel.objects.filter(product=product).aggregate(
                    units=Coalesce(Sum('units'), Decimal(0.00))
                )['units']

                current_stock = abs(total_units) # We don't want negative stock

                current_cost = product.cost
                current_stock_value = current_stock * current_cost

                po_stock = self.add_stock
                po_cost = self.cost
                po_total_value = po_stock * po_cost

                new_stock = current_stock + po_stock

                if new_stock > 0:
                    new_cost = (current_stock_value + po_total_value) / new_stock
                    # Save product's new cost
                    product.cost = new_cost
                    product.save()

                StockLevel.update_level(
                    user=self.stock_adjustment.user,
                    store=self.stock_adjustment.store, 
                    product=self.product, 
                    inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_RECEIVE,
                    change_source_reg_no=self.stock_adjustment.reg_no,
                    change_source_name=change_source_name,
                    line_source_reg_no=self.reg_no,
                    adjustment=self.add_stock, 
                    update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
                )

            elif self.stock_adjustment.reason == StockAdjustment.STOCK_ADJUSTMENT_LOSS or \
                self.stock_adjustment.reason == StockAdjustment.STOCK_ADJUSTMENT_DAMAGE or \
                self.stock_adjustment.reason == StockAdjustment.STOCK_ADJUSTMENT_EXPIRY:
                
                if self.stock_adjustment.reason == StockAdjustment.STOCK_ADJUSTMENT_LOSS:
                    reason = InventoryHistory.INVENTORY_HISTORY_LOSS

                elif self.stock_adjustment.reason == StockAdjustment.STOCK_ADJUSTMENT_DAMAGE:
                    reason = InventoryHistory.INVENTORY_HISTORY_DAMAGE
                
                else:
                    reason = InventoryHistory.INVENTORY_HISTORY_EXPIRY 

                StockLevel.update_level(
                    user=self.stock_adjustment.user,
                    store=self.stock_adjustment.store,  
                    product=self.product, 
                    inventory_history_reason=reason,
                    change_source_reg_no=self.stock_adjustment.reg_no,
                    change_source_name=change_source_name,
                    line_source_reg_no=self.reg_no,
                    adjustment=self.remove_stock, 
                    update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
                )

        except:  # pylint: disable=bare-except
            LoggerManager.log_critical_error()

    def save(self, *args, **kwargs):
        # This makes sure that product_info value is only update once
        if not self.product_info:
            self.product_info = {"name": self.product.name, "sku": self.product.sku}

        """ Check if this object is being created """
        created = self.pk is None

        """If reg_no is 0 get a unique reg_no"""
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(StockAdjustmentLine, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        if created:
            self.update_stock_level(created)


# ========================== END stock adjustment models


# ========================== START transfer order models


class TransferOrder(models.Model):
    TRANSFER_ORDER_PENDING = 0
    TRANSFER_ORDER_RECEIVED = 1
    TRANSFER_ORDER_CLOSED = 2

    TRANSFER_ORDER_CHOICES = [
        (
            TRANSFER_ORDER_PENDING,
            "Pending",
        ),
        (
            TRANSFER_ORDER_RECEIVED,
            "Received",
        ),
        (
            TRANSFER_ORDER_CLOSED,
            "Closed",
        ),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    source_store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="source_store"
    )
    destination_store = models.ForeignKey(
        Store, on_delete=models.CASCADE, related_name="destination_store"
    )
    notes = models.CharField(
        verbose_name="notes", max_length=500, blank=True, default=""
    )
    status = models.IntegerField(
        verbose_name="status",
        choices=TRANSFER_ORDER_CHOICES,
        default=TRANSFER_ORDER_PENDING,
    )
    quantity = models.DecimalField(
        verbose_name="quantity", max_digits=30, decimal_places=2, default=0
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        # unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    order_completed = models.BooleanField(
        verbose_name="order completed", default=False
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )
    completed_date = models.DateTimeField(
        verbose_name="completed date", default=timezone.now, db_index=True
    )

    # Fields for auto creation
    is_auto_created = models.BooleanField(
        verbose_name="is auto created", 
        default=False
    )
    source_description = models.CharField(
        verbose_name="source description", 
        max_length=300, 
        blank=True, 
        default=""
    )

    def __str__(self):
        return f"TO{self.increamental_id}"

    def get_str_quantity(self):
        return str(self.quantity)

    def get_ordered_by(self):
        return self.user.get_full_name()
    
    def get_stores_data(self):
        return {
            'source_store': {
                "name": self.source_store.name, 
                "reg_no": self.source_store.reg_no
            },
            'destination_store': {
                "name": self.destination_store.name, 
                "reg_no": self.destination_store.reg_no
            }
        }
    
    def get_source_store_name(self):
        return self.source_store.name

    def get_destination_store_name(self):
        return self.destination_store.name

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    def get_completed_date(self, local_timezone):
        """Return the completion date in local time format"""
        return utc_to_local_datetime_with_format(self.completed_date, local_timezone)

    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)

    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = "created_date"

    def get_line_data(self):
        line_queryset = list(
            self.transferorderline_set.all()
            .order_by("id")
            .values(
                "product_info",
                "quantity",
                "reg_no"

            )
        )

        lines = []
        for line in line_queryset:

            source_store_units = StockLevel.objects.get(
                product__reg_no=line["product_info"]['reg_no'],
                store=self.source_store
            ).units

            destination_store_units = StockLevel.objects.get(
                product__reg_no=line["product_info"]['reg_no'],
                store=self.destination_store
            ).units
            lines.append(
                {
                    "product_info": line["product_info"],
                    "quantity": str(line["quantity"]),
                    "source_store_units": source_store_units,
                    "destination_store_units": destination_store_units,
                    "reg_no": str(line["reg_no"]),

                }
            )

        return lines

    def update_stock_Level(self):
        if not self.order_completed:
            if self.status == TransferOrder.TRANSFER_ORDER_RECEIVED:
                
                # Update order completed and completed date
                self.order_completed = True
                self.completed_date = timezone.now()

                source_store = self.source_store
                destination_store = self.destination_store

                should_transform = source_store.is_truck and destination_store.is_shop

                change_source_name = self.__str__()
                lines = self.transferorderline_set.all()


                auto_repackaging = []
                auto_repackaging_total_quantity = 0
                for line in lines:
                    try:

                        product = line.product
                        
                        quantity = line.quantity

                        source_store_exists = StockLevel.objects.filter(
                            product=product, 
                            store=source_store
                        ).exists()

                        destination_store_exists = StockLevel.objects.filter(
                            product=product, 
                            store=destination_store
                        ).exists()
                        
                        # Only continue when we have both source and destination 
                        # stores
                        if not source_store_exists or not destination_store_exists:
                            return
                        
                        '''
                        Pesa kwa meza
                        Rachael husband
                        Competing with people

                        '''
                        
                        StockLevel.update_level(
                            user=self.user,
                            store=source_store, 
                            product=product, 
                            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_TRANSFER,
                            change_source_reg_no=self.reg_no,
                            change_source_name=change_source_name,
                            line_source_reg_no=f'{line.reg_no}0',
                            adjustment=quantity, 
                            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING
                        ) 

                        StockLevel.update_level(
                            user=self.user,
                            store=destination_store, 
                            product=product, 
                            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_TRANSFER,
                            change_source_reg_no=self.reg_no,
                            change_source_name=change_source_name,
                            line_source_reg_no=f'{line.reg_no}1',
                            adjustment=quantity, 
                            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING
                        )


                        if not should_transform: continue 

                        if product.productions.all().count():

                            transform_data = product.get_product_view_transform_data(
                                destination_store,
                                filter_for_repackaging=True
                            )  

                            product_map = transform_data['product_map']

                            if not product_map: continue

                            source_product = product
                            tartget_product = Product.objects.get(reg_no=product_map[0]['reg_no'])
                            
                            added_quantity = Decimal(quantity)*Decimal(product_map[0]["equivalent_quantity"])

                            source_product_cost = transform_data['cost']
                            target_product_cost = Decimal(source_product_cost)/Decimal(product_map[0]["equivalent_quantity"])

                            auto_repackaging.append({
                                'source_product': source_product,
                                'tartget_product': tartget_product,
                                'quantity': quantity,
                                'added_quantity': added_quantity,
                                'target_product_cost': target_product_cost
                            })

                            auto_repackaging_total_quantity += added_quantity

                    except:  # pylint: disable=bare-except
                        LoggerManager.log_critical_error()

                if not auto_repackaging: return

                # Create product disassembly
                self.create_product_transform(
                    auto_repackaging=auto_repackaging,
                    auto_repackaging_total_quantity=auto_repackaging_total_quantity,
                    source_desc=self.__str__(),
                    source_reg_no=self.reg_no
                )
 
    def create_product_transform(
            self, 
            auto_repackaging, 
            auto_repackaging_total_quantity,
            source_desc,
            source_reg_no
            ):

        if not auto_repackaging: return

        # Create product disassembly
        product_transform = ProductTransform.objects.create(
            user=self.user,
            store=self.destination_store,
            total_quantity=auto_repackaging_total_quantity,
            is_auto_repackaged=True,
            auto_repackaged_source_desc=source_desc,
            auto_repackaged_source_reg_no = source_reg_no,
        )

        for repackaging in auto_repackaging:
            ProductTransformLine.objects.create(
                product_transform=product_transform,
                source_product=repackaging['source_product'],
                target_product=repackaging['tartget_product'],
                quantity=repackaging['quantity'],
                added_quantity=repackaging['added_quantity'],
                cost=repackaging['target_product_cost'],
            )

        product_transform.status = ProductTransform.PRODUCT_TRANSFORM_RECEIVED
        product_transform.save()

    def increment_increamental_id(self, created, count_user):

        if not created: return

        last_store = TransferOrderCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_store:
            self.increamental_id = last_store.increamental_id + 1
        else:
            self.increamental_id = 1000

    def create_transfer_order_count_model(self, count_user):
        """
        Create TransferOrderCount
        """
        # We input created date to ease analytics testing
        TransferOrderCount.objects.create(
            user=count_user,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        self.update_stock_Level()

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        # Increament increamental_id
        self.increment_increamental_id(created, count_user)

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(TransferOrder, self).save(*args, **kwargs)

        if created:
            self.create_transfer_order_count_model(count_user)


class TransferOrderCount(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE
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

    def __str__(self):
        return f'TO Count ({self.user})'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def increment_increamental_id(self, created):

        if not created: return

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        last_model = TransferOrderCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Increament increamental_id
        self.increment_increamental_id(created)

        super(TransferOrderCount, self).save(*args, **kwargs)

class TransferOrderLine(models.Model):
    transfer_order = models.ForeignKey(TransferOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_info = models.JSONField(verbose_name="product info", default=dict)
    quantity = models.DecimalField(
        verbose_name="quantity", max_digits=30, decimal_places=2, default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        editable=False,
    )

    #### Fields for tally
    synced_with_tally = models.BooleanField(
        verbose_name='synced with tally',
        default=False
    )

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        # This makes sure that product_info value is only update once
        if not self.product_info:
            self.product_info = {
                "name": self.product.name,
                "sku": self.product.sku,
                "reg_no": self.product.reg_no,
            }

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(TransferOrderLine, self).save(*args, **kwargs)


# ========================== END transfer order models


# ========================== START inventory models

class InventoryCount(models.Model):
    INVENTORY_COUNT_PENDING = 0
    INVENTORY_COUNT_COMPLETED = 1
    INVENTORY_COUNT_CLOSED = 2

    INVENTORY_COUNT_CHOICES = [
        (
            INVENTORY_COUNT_PENDING,
            "Pending",
        ),
        (
            INVENTORY_COUNT_COMPLETED,
            "Completed",
        ),
        (
            INVENTORY_COUNT_CLOSED,
            "Closed",
        ),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    notes = models.CharField(
        verbose_name="notes", max_length=500, blank=True, default=""
    )
    mismatch_found = models.BooleanField(verbose_name="mismatch found", default=False)
    status = models.IntegerField(
        verbose_name="status",
        choices=INVENTORY_COUNT_CHOICES,
        default=INVENTORY_COUNT_PENDING,
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )
    completed_date = models.DateTimeField(
        verbose_name="completed date", default=timezone.now, db_index=True
    )

    def __str__(self):
        return f"IC{self.increamental_id}"

    def get_counted_by(self):
        return self.user.get_full_name()

    def get_store_name(self):
        return self.store.name
    
    # TODO Test this function
    def get_store_data(self):
        return {"name": self.store.name, "reg_no": self.store.reg_no}

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    
    def get_completed_date(self, local_timezone):
        """Return the completion date in local time format"""
        return utc_to_local_datetime_with_format(self.completed_date, local_timezone)

    # TODO #1 Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)

    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = "created_date"

    def get_line_data(self):
        """
        When status is completed, we return the data from the inventory count
        name. Otherwise we get the stock data from the stock levels and 
        recalculate both the difference and cost difference.

        Returns the following list
        [
            {
                'cost_difference': '-123000.00',
                'counted_stock': '77.00',
                'difference': '-123.00',
                'expected_stock': '200.00',
                'product_cost': '1000.00',
                'product_info': {'name': 'Shampoo', 'reg_no': 387387051534, 'sku': ''
            },
            'reg_no': '438110838417'},
            {
                'cost_difference': '3600.00',
                'counted_stock': '160.00',
                'difference': '3.00',
                'expected_stock': '157.00',
                'product_cost': '1200.00',
                'product_info': {'name': 'Conditioner', 'reg_no': 426750988186, 'sku': ''},
                'reg_no': '289826070648'
            }
        ]
        """

        line_queryset = list(
            self.inventorycountline_set.all()
            .order_by("id")
            .values(
                "product_info",
                "expected_stock",
                "counted_stock",
                "difference",
                "cost_difference",
                "product_cost",
                "reg_no"
            )
        )

        if self.status == InventoryCount.INVENTORY_COUNT_COMPLETED:
        
            lines = []
            for line in line_queryset:

                lines.append(
                    {
                        "product_info": line["product_info"],
                        "expected_stock": str(line["expected_stock"]),
                        "counted_stock": str(line["counted_stock"]),
                        "difference": str(line["difference"]),
                        "cost_difference": str(line["cost_difference"]),
                        "product_cost": str(line["product_cost"]),
                        "reg_no": str(line["reg_no"]),
                    }
                )

        else:

            # Create a dict map
            levels = StockLevel.objects.filter(store=self.store).values(
                'units', 
                'product__reg_no'
            )
            stock_levels = {level['product__reg_no']: level['units']for level in levels}

            lines = []
            for line in line_queryset:

                product_cost= line["product_cost"]
                counted_stock = line["counted_stock"]
                
                expected_stock = stock_levels[line["product_info"]['reg_no']]
                difference = counted_stock - expected_stock

                cost_difference = round(difference * product_cost, 2)

                lines.append(
                    {
                        "product_info": line["product_info"],
                        "expected_stock": str(expected_stock),
                        "counted_stock": str(counted_stock),
                        "difference": str(difference),
                        "cost_difference": str(cost_difference),
                        "product_cost": str(line["product_cost"]),
                        "reg_no": str(line["reg_no"]),
                    }
                )

        return lines
    
    def increment_increamental_id(self, created, count_user):

        if not created: return

        last_model = InventoryCountCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def create_inventory_count_count_model(self, count_user):
        """
        Create InventoryCountCount
        """
        # We input created date to ease analytics testing
        InventoryCountCount.objects.create(
            user=count_user,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        if self.status == InventoryCount.INVENTORY_COUNT_COMPLETED:
            self.completed_date = timezone.now()

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        # Increament increamental_id
        self.increment_increamental_id(created, count_user)
            
        """If reg_no is 0 get a unique reg_no"""
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(InventoryCount, self).save(*args, **kwargs)

        if created:
            self.create_inventory_count_count_model(count_user)


class InventoryCountCount(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE
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

    def __str__(self):
        return f'IC Count ({self.user})'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def increment_increamental_id(self, created):

        if not created: return

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        last_model = InventoryCountCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Increament increamental_id
        self.increment_increamental_id(created)

        super(InventoryCountCount, self).save(*args, **kwargs)


class InventoryCountLine(models.Model):
    inventory_count = models.ForeignKey(InventoryCount, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_info = models.JSONField(verbose_name="product info", default=dict)
    expected_stock = models.DecimalField(
        verbose_name="expected stock", max_digits=30, decimal_places=2, default=0
    )
    counted_stock = models.DecimalField(
        verbose_name="counted stock", max_digits=30, decimal_places=2, default=0
    )
    difference = models.DecimalField(
        verbose_name="difference", max_digits=30, decimal_places=2, default=0
    )
    cost_difference = models.DecimalField(
        verbose_name="cost difference", max_digits=30, decimal_places=2, default=0
    )
    product_cost = models.DecimalField(
        verbose_name="product cost", max_digits=30, decimal_places=2, default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        editable=False,
    )

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):

        # This makes sure that product_info value is only update once
        if not self.product_info:
            self.product_info = {
                "name": self.product.name, 
                "sku": self.product.sku,
                "reg_no": self.product.reg_no
            }

        self.product_cost = self.product.cost

        self.difference = self.counted_stock - self.expected_stock

        self.cost_difference = self.product.cost * self.difference

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        

        # Call the "real" save() method.
        super(InventoryCountLine, self).save(*args, **kwargs)

      
# ========================== END inventory count models
 

# ========================== START purchase order models
class PurchaseOrder(models.Model):
    PURCHASE_ORDER_PENDING = 0
    PURCHASE_ORDER_RECEIVED = 1
    PURCHASE_ORDER_CLOSED = 2

    PURCHASE_ORDER_CHOICES = [
        (
            PURCHASE_ORDER_PENDING,
            "Pending",
        ),
        (
            PURCHASE_ORDER_RECEIVED,
            "Received",
        ),
        (
            PURCHASE_ORDER_CLOSED,
            "Closed",
        ),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    notes = models.CharField(
        verbose_name="notes", max_length=500, blank=True, default=""
    )
    status = models.IntegerField(
        verbose_name="status",
        choices=PURCHASE_ORDER_CHOICES,
        default=PURCHASE_ORDER_PENDING,
    )
    total_amount = models.DecimalField(
        verbose_name="total amount", max_digits=30, decimal_places=2, default=0
    )
    order_completed = models.BooleanField(
        verbose_name="order completed", default=False, editable=False
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )
    created_date_timestamp = models.BigIntegerField(
        verbose_name="created date timestamp", default=0
    )
    expected_date = models.DateTimeField(
        verbose_name="expected date", default=timezone.now, db_index=True
    )
    expected_date_timestamp = models.BigIntegerField(
        verbose_name="expected date timestamp", default=0
    )
    completed_date = models.DateTimeField(
        verbose_name="completed date", default=timezone.now, db_index=True
    )

    def __str__(self):
        return f"PO{self.increamental_id}"

    def get_ordered_by(self):
        return self.user.get_full_name()

    def get_supplier_name(self):
        return self.supplier.name

    def get_supplier_data(self):
        return {
            "name": self.supplier.name,
            "email": self.supplier.email,
            "phone": self.supplier.phone,
            "location": self.supplier.get_location_desc(),
            "reg_no": self.supplier.reg_no,
        }

    def get_store_data(self):
        return {"name": self.store.name, "reg_no": self.store.reg_no}

    def get_store_name(self):
        return self.store.name

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    def get_completed_date(self, local_timezone):
        """Return the completion date in local time format"""
        return utc_to_local_datetime_with_format(self.completed_date, local_timezone)

    # Make created_date to be filterable
    get_created_date.admin_order_field = "created_date"

    def get_expected_date(self, local_timezone):
        """Return the expected date in local time format"""
        return utc_to_local_datetime_with_format(self.expected_date, local_timezone)

    # Make expected_date to be filterable
    get_expected_date.admin_order_field = "expected_date"

    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)

    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = "created_date"

    def get_line_data(self):
        line_queryset = list(
            self.purchaseorderline_set.all()
            .order_by("id")
            .values("product_info", "quantity", "purchase_cost", "amount", "reg_no")
        )

        lines = []
        for line in line_queryset:
            lines.append(
                {
                    "product_info": line["product_info"],
                    "quantity": str(line["quantity"]),
                    "purchase_cost": str(line["purchase_cost"]),
                    "amount": str(line["amount"]),
                    "reg_no": str(line["reg_no"]),
                }
            )

        return lines

    def get_additional_cost_line_data(self):
        line_queryset = list(
            self.purchaseorderadditionalcost_set.all()
            .order_by("id")
            .values("name", "amount")
        )

        lines = []
        for line in line_queryset:
            lines.append(
                {
                    "name": line["name"],
                    "amount": str(line["amount"]),
                }
            )

        return lines
    
    def get_po_line_total_cost(self, line, total_po_value, total_additional_cost_total):

        po_quantity = line.quantity
        po_cost = line.purchase_cost

        po_line_value = po_quantity * po_cost

        if total_po_value == 0:
            po_line_addintion_cost = 0
        else:
            po_line_addintion_cost = (po_line_value / total_po_value) * total_additional_cost_total

        po_line_addintion_cost = NumberHelpers.normal_round(
            po_line_addintion_cost, 
            2
        )

        po_added_cost = NumberHelpers.normal_round(
            po_line_addintion_cost/po_quantity,
            2
        )
        new_product_cost = po_cost + po_added_cost

        return new_product_cost

    def update_stock_Level(self): 
        if not self.order_completed:
            
            if self.status == PurchaseOrder.PURCHASE_ORDER_RECEIVED:
                
                # Update order completed and completed date
                self.order_completed = True
                self.completed_date = timezone.now()

                # Get additional cost total
                additional_cost_query = self.purchaseorderadditionalcost_set.all()

                additional_cost_total = 0

                if additional_cost_query:
                    additional_cost_total = additional_cost_query.aggregate(
                        total=Coalesce(Sum('amount'), Decimal(0.00))
                    )['total']
                
                lines = self.purchaseorderline_set.all()

                # Get lines total amount
                total_po_value = 0
                for line in lines: total_po_value += line.amount

                for line in lines:
                    try:
                        product = line.product

                        total_units = StockLevel.objects.filter(product=product).aggregate(
                            units=Coalesce(Sum('units'), Decimal(0.00))
                        )['units']

                        current_stock = abs(total_units) # We don't want negative stock
                        current_cost = line.product.cost
                        current_stock_value = current_stock * current_cost

                        po_stock = line.quantity
                        po_cost = self.get_po_line_total_cost(line, total_po_value, additional_cost_total)
                        po_total_value = po_stock * po_cost 

                        new_stock = current_stock + po_stock
                        new_cost = (current_stock_value + po_total_value) / new_stock

                        # Save product's new cost
                        product.cost = new_cost
                        product.save()

                        StockLevel.update_level(
                            user=self.user,
                            store= self.store, 
                            product=product, 
                            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE,
                            change_source_reg_no=self.reg_no,
                            change_source_name=self.__str__(),
                            line_source_reg_no=line.reg_no,
                            adjustment=po_stock, 
                            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING,
                            created_date=self.created_date
                        ) 

                    except:  # pylint: disable=bare-except
                        LoggerManager.log_critical_error()

    def format_date_fields(self):
        """
        If we have a valid created_date_timestamp, we get created date from it.
        If the created_date_timestamp is wrong, we replace it with the default
        created_date's timestamp
        """

        (
            self.created_date,
            self.created_date_timestamp,
        ) = DateHelperMethods.date_and_timestamp_equilizer(
            self.created_date, self.created_date_timestamp
        )
        
    def increment_increamental_id(self, created, count_user):

        if not created: return

        last_store = PurchaseOrderCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_store:
            self.increamental_id = last_store.increamental_id + 1
        else:
            self.increamental_id = 1000

    def create_transfer_order_count_model(self, count_user):
        """
        Create PurchaseOrderCount
        """

        # We input created date to ease analytics testing
        PurchaseOrderCount.objects.create(
            user=count_user,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Update stock if it's neccessary
        self.update_stock_Level()

        # Creates the right dates and date_timestamps
        self.format_date_fields()

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        # Increament increamental_id
        self.increment_increamental_id(created, count_user)

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(PurchaseOrder, self).save(*args, **kwargs)

        if created:
            self.create_transfer_order_count_model(count_user)


class PurchaseOrderCount(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE
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

    def __str__(self):
        return f'PO Count ({self.user})'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def increment_increamental_id(self, created):

        if not created: return

        count_user = self.user

        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)
            
        last_model = PurchaseOrderCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Increament increamental_id
        self.increment_increamental_id(created)

        super(PurchaseOrderCount, self).save(*args, **kwargs)

class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_info = models.JSONField(verbose_name="product info", default=dict)
    quantity = models.DecimalField(
        verbose_name="quantity", max_digits=30, decimal_places=2, default=0
    )
    purchase_cost = models.DecimalField(
        verbose_name="purchase cost", max_digits=30, decimal_places=2, default=0
    )
    amount = models.DecimalField(
        verbose_name="amount", max_digits=30, decimal_places=2, default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        # unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )

    #### Fields for tally
    synced_with_tally = models.BooleanField(
        verbose_name='synced with tally',
        default=False
    )

    def __str__(self):
        return self.product.name

    def save(self, *args, **kwargs):
        # This makes sure that product_info value is only update once
        # if not self.product_info:
        self.product_info = {
            "name": self.product.name,
            "sku": self.product.sku,
            "tax_rate": str(self.product.tax_rate),
            "reg_no": self.product.reg_no,
        }

        self.amount = self.purchase_cost * self.quantity

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(PurchaseOrderLine, self).save(*args, **kwargs)


class PurchaseOrderAdditionalCost(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    name = models.CharField(verbose_name="name", max_length=50)
    amount = models.DecimalField(
        verbose_name="amount", max_digits=30, decimal_places=2, default=0
    )


# ========================== END purchase order models 


# ========================== START inventory history models 
class InventoryHistory(models.Model):
    INVENTORY_HISTORY_SALE = 0 #
    INVENTORY_HISTORY_REFUND = 1 #
    INVENTORY_HISTORY_RECEIVE = 2 #
    INVENTORY_HISTORY_PO_RECEIVE = 3 #
    INVENTORY_HISTORY_TRANSFER = 4 #
    INVENTORY_HISTORY_DAMAGE = 5 #
    INVENTORY_HISTORY_LOSS = 6 #
    INVENTORY_HISTORY_REPACKAGE = 7
    INVENTORY_HISTORY_EXPIRY = 8

    INVENTORY_HISTORY_CHOICES = [
        (
            INVENTORY_HISTORY_SALE,
            "Sale",
        ),
        (
            INVENTORY_HISTORY_REFUND,
            "Refund",
        ),
        (
            INVENTORY_HISTORY_RECEIVE,
            "Receive",
        ),
        (
            INVENTORY_HISTORY_PO_RECEIVE,
            "Receive",
        ),
        (
            INVENTORY_HISTORY_TRANSFER,
            "Transfer",
        ),
        (
            INVENTORY_HISTORY_DAMAGE,
            "Damage",
        ),
        (
            INVENTORY_HISTORY_LOSS,
            "Loss",
        ),
        (
            INVENTORY_HISTORY_REPACKAGE,
            "Repackage",
        ),

        (
            INVENTORY_HISTORY_EXPIRY,
            "Expiry",
        ),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    reason = models.IntegerField(
        verbose_name="reason",
        choices=INVENTORY_HISTORY_CHOICES,
        default=INVENTORY_HISTORY_SALE,
    )
    change_source_reg_no = models.BigIntegerField(
        verbose_name="change source reg no",
        default=0,
        editable=False,
    )
    change_source_desc = models.CharField(
        verbose_name="change source desc", max_length=50, blank=True, default=""
    )
    line_source_reg_no = models.BigIntegerField(
        verbose_name="line source reg no",
        default=0,
    )
    change_source_name = models.CharField(
        verbose_name="change source name", max_length=50, blank=True, default=""
    )
    adjustment = models.DecimalField(
        verbose_name="adjustment", max_digits=30, decimal_places=2, default=0
    )
    stock_after = models.DecimalField(
        verbose_name="stock_after", max_digits=30, decimal_places=2, default=0
    )
    store_name = models.CharField(
        verbose_name="store name", 
        max_length=50, 
        blank=True, 
        default=""
    )
    product_name = models.CharField(
        verbose_name="product name", 
        max_length=50, 
        blank=True, 
        default=""
    )
    user_name = models.CharField(
        verbose_name="user name", 
        max_length=50, 
        blank=True, 
        default=""
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )
    stock_was_deducted = models.BooleanField(
        verbose_name="stock was deducted", default=True
    )

    # This field should never be updated. It should never be changed from 
    # what it was when the receipt was created
    sync_date = models.DateTimeField(
        verbose_name='sync date',
        default=timezone.now,
        db_index=True
    )

    def __str__(self):
        return str(self.change_source_name)

    def get_adjusted_by(self):
        return self.user.get_full_name()

    def get_store_data(self):
        return {"name": self.store.name, "reg_no": self.store.reg_no}

    def get_store_name(self):
        return self.store.name

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    # Make created_date to be filterable
    get_created_date.admin_order_field = "created_date"

    def get_synced_date(self, local_timezone):
        """Return the sync date in local time format"""
        return utc_to_local_datetime_with_format(self.sync_date, local_timezone)
    
    # Make sync_date to be filterable
    get_synced_date.admin_order_field = "sync_date"
    
    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)

    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = "created_date"

    def update_change_source_desc(self):

        if self.reason == InventoryHistory.INVENTORY_HISTORY_SALE:
            self.change_source_desc = "Sale"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_REFUND:
            self.change_source_desc = "Refund"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_RECEIVE:
            self.change_source_desc = "Receive"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_PO_RECEIVE:
            self.change_source_desc = "Receive"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_TRANSFER:
            self.change_source_desc = "Transfer"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_DAMAGE:
            self.change_source_desc = "Damage"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_LOSS:
            self.change_source_desc = "Loss"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_REPACKAGE:
            self.change_source_desc = "Repackage"

        elif self.reason == InventoryHistory.INVENTORY_HISTORY_EXPIRY:
            self.change_source_desc = "Expiry"

        else:
            self.change_source_desc = "Error"

    def recalculate_stock_afters_forward(self):
        """
        Recalculates the "stock after" for similar inventory history 
        (same product and store) that came after this.

        The first inventory history from the query below does not get changed
        in any way. It's stock after is used as the starting point for the
        recalculation of the inventory histories that came after it.
        """

        from inventories.models.inventory_valuation_models import InventoryValuationLine

        historys = InventoryHistory.objects.filter(
            store=self.store,
            product=self.product,
            created_date__gte=self.created_date 
        ).values(
            'line_source_reg_no', 
            'change_source_name',
            'adjustment', 
            'stock_after', 
            'reg_no',
            'created_date',
        ).order_by('created_date')

        newest_data = []
        for index, history in enumerate(historys):

            adjustment = history['adjustment']
            if index == 0:
                stock_after = history['stock_after']
            else:
                stock_after = newest_data[index-1]['stock_after'] + adjustment

            line_data = {
                'line_source_reg_no': history['line_source_reg_no'],
                'adjustment': adjustment,
                'stock_after': stock_after,
                'reg_no': history['reg_no'],
                'created_date': history['created_date']
            }

            newest_data.append(line_data)
           
            InventoryHistory.objects.filter(reg_no=history['reg_no']).update(
                stock_after=stock_after
            )

        all_histories = InventoryHistory.objects.filter(
            store=self.store,
            product=self.product,
            created_date__gte=self.created_date 
        ).order_by('created_date')

        first_date = all_histories.first().created_date
        end_date=all_histories.last().created_date

        # print('-------------')
        # print(f"First {first_date}")
        # print(f"Last {all_histories.last().created_date}")


        self.recalculate_inventory_valuations(first_date, end_date)

        # Get the dates in between
        # dates_in_between = DateHelperMethods.get_dates_in_between(
        #     start_date=first_date,
        #     end_date=end_date,
        # )
        # # pprint(dates_in_between)

        # for date in dates_in_between:
        #     # print(f'***************************************** {date}')
        #     history = InventoryHistory.objects.filter(
        #         store=self.store,
        #         product=self.product,
        #         created_date__date=date 
        #     ).order_by('created_date').last()

        #     if not history:
        #         # print("&&&&&&&& Code invoked for date")
        #         history = InventoryHistory.objects.filter(
        #             store=self.store,
        #             product=self.product,
        #             created_date__date__lte=date 
        #         ).order_by('created_date').last()

        #     if history:
        #         # print(f"Last {history.line_source_reg_no} {history.created_date} {history.stock_after}")
        #         InventoryValuationLine.objects.filter(
        #             store=self.store, 
        #             product=self.product,
        #             inventory_valution__created_date__date=date.date()
        #         ).update(units=history.stock_after)

    def recalculate_inventory_valuations(self, first_date, end_date):

        from inventories.models.inventory_valuation_models import InventoryValuationLine

        # Get the dates in between
        dates_in_between = DateHelperMethods.get_dates_in_between(
            start_date=first_date,
            end_date=end_date,
        )
        # pprint(dates_in_between)

        for date in dates_in_between:
            history = InventoryHistory.objects.filter(
                store=self.store,
                product=self.product,
                created_date__date=date 
            ).order_by('created_date').last()

            if not history:
                history = InventoryHistory.objects.filter(
                    store=self.store,
                    product=self.product,
                    created_date__date__lte=date 
                ).order_by('created_date').last()

            if history:
                InventoryValuationLine.objects.filter(
                    store=self.store, 
                    product=self.product,
                    inventory_valution__created_date__date=date.date()
                ).update(units=history.stock_after)

    def start_recalculating_stock_afters_forward(self, should_recalculate):

        # print('>>****************** ', self.line_source_reg_no, self.created_date)
        # print(should_recalculate)

        if should_recalculate:
            last_older_history = InventoryHistory.objects.filter(
                store=self.store,
                product=self.product,
                created_date__lte=self.created_date
            ).exclude(pk=self.pk).order_by('created_date').last()

            # if last_older_history:
                # print("Last older history ", last_older_history.line_source_reg_no )

            if last_older_history:
                # print(f"We got history {last_older_history.change_source_name} {last_older_history.stock_after}")
                last_older_history.recalculate_stock_afters_forward()
            # else:
            #     print("No older history")

    @staticmethod
    def start_recalculating_stock_afters_reversee(store, product, start_date, end_date):

        # print(f'Start date {start_date} End date {end_date}')

        # Get the dates in between
        # dates_in_between = DateHelperMethods.get_dates_in_between(
        #     start_date=start_date,
        #     end_date=end_date,
        # )
        # pprint(dates_in_between)

        # current_level = StockLevel.objects.filter(
        #     store=store,
        #     product=product,
        # ).first()

        # if not current_level: return

        # current_level_units = current_level.units

        # print(current_level_units)

        # last_history = InventoryHistory.objects.filter(
        #     store=store,
        #     product=product,
        #     created_date__gte=end_date 
        # ).order_by('-created_date').first()

        # if last_history:
        #     last_history.stock_after = current_level_units
        #     last_history.save()


        # print(last_history.line_source_reg_no)











        
        historys = InventoryHistory.objects.filter(
            store=store,
            product=product,
            created_date__gte=start_date 
        ).values(
            'line_source_reg_no', 
            'change_source_name',
            'adjustment', 
            'stock_after', 
            'reg_no',
            'created_date',
        ).order_by('-created_date', '-id')

        last_history = historys.last()
        first_history = historys.first()

        if first_history:
            # print(f"First history {first_history['change_source_name']} {first_history['stock_after']} {first_history['line_source_reg_no']}")


            level = StockLevel.objects.filter(
                store=store,
                product=product,
            ).first()

            if not level: return

            InventoryHistory.objects.filter(reg_no=first_history['reg_no']).update(
                stock_after=level.units
            )

        # if last_history:
        #     print(f"Last history {last_history['change_source_name']} {last_history['stock_after']} {last_history['line_source_reg_no']}")

        newest_data = []
        for index, history in enumerate(historys):

            if index == 0:
                stock_after = history['stock_after']
            else:
                last_adjustment = newest_data[index-1]['adjustment']
                last_stock_after = newest_data[index-1]['stock_after']

                add=False
                if last_adjustment < 0:
                    last_adjustment = abs(last_adjustment)
                    add=True

                if add:
                    stock_after = last_stock_after + last_adjustment
                else:
                    stock_after = last_stock_after - last_adjustment

            line_data = {
                'line_source_reg_no': history['line_source_reg_no'],
                'adjustment': history['adjustment'],
                'stock_after': stock_after,
                'reg_no': history['reg_no'],
                'created_date': history['created_date']
            }

            newest_data.append(line_data)

            # print(line_data)
           
            InventoryHistory.objects.filter(reg_no=history['reg_no']).update(
                stock_after=stock_after
            )
            history = InventoryHistory.objects.filter(reg_no=history['reg_no']).first()
            
        InventoryHistory.recalculate_inventory_valuationss(
            first_date=start_date, 
            end_date=end_date,
            store=store,
            product=product
        )

    @staticmethod
    def recalculate_inventory_valuationss(first_date, end_date, store, product):
        # print(f"\n&&& {first_date} {end_date}")

        from inventories.models.inventory_valuation_models import InventoryValuationLine

        # Get the dates in between
        dates_in_between = DateHelperMethods.get_dates_in_between(
            start_date=first_date,
            end_date=end_date,
        )
        # pprint(dates_in_between)

        for date in dates_in_between:

            minus_from_latest = False

            # print()
            # print(date)
            history = InventoryHistory.objects.filter(
                store=store,
                product=product,
                created_date__date=date 
            ).order_by('created_date', 'id').last()

            # if history:
            #     print(f'Using history {history.line_source_reg_no}')

            if not history:

                # print('********* In backups')
                historyss = InventoryHistory.objects.filter(
                    store=store,
                    product=product,
                    created_date__date__gte=date 
                ).order_by('created_date', 'id').values_list('line_source_reg_no', flat=True)
                # print(historyss)

                history = InventoryHistory.objects.filter(
                    store=store,
                    product=product,
                    created_date__date__gte=date 
                ).order_by('created_date', 'id').first()
                
                if history:
                    minus_from_latest = True
                    # print(f'Using backup history{history.line_source_reg_no}')

            if history:

                stock_after = history.stock_after

                if minus_from_latest:
                    # print('Minus from latest')

                    last_adjustment = history.adjustment
                    last_stock_after = history.stock_after

                    add=False
                    if last_adjustment < 0:
                        last_adjustment = abs(last_adjustment)
                        add=True

                    if add:
                        stock_after = last_stock_after + last_adjustment
                    else:
                        stock_after = last_stock_after - last_adjustment

                InventoryValuationLine.objects.filter(
                    store=store, 
                    product=product,
                    inventory_valution__created_date__date=date.date()
                ).update(units=stock_after)

            else:
                level = StockLevel.objects.filter(
                    store=store,
                    product=product,
                ).first()

                stock_units = level.units if level else 0

                if not level: return
                
                InventoryValuationLine.objects.filter(
                    store=store, 
                    product=product,
                    inventory_valution__created_date__date=date.date()
                ).update(units=stock_units)

    def start_recalculating_stock_afters_reverse(self):

        historys = InventoryHistory.objects.filter(
            store=self.store,
            product=self.product,
            created_date__gte=self.created_date 
        ).values(
            'line_source_reg_no', 
            'change_source_name',
            'adjustment', 
            'stock_after', 
            'reg_no',
            'created_date',
        ).order_by('-created_date')

        last_history = historys.last()
        first_history = historys.first()

        if first_history:
            # print(f"First history {first_history['change_source_name']} {first_history['stock_after']} {first_history['line_source_reg_no']}")


            level = StockLevel.objects.filter(
                store=self.store,
                product=self.product,
            ).first()

            if not level: return

            InventoryHistory.objects.filter(reg_no=first_history['reg_no']).update(
                stock_after=level.units
            )

        # if last_history:
        #     print(f"Last history {last_history['change_source_name']} {last_history['stock_after']} {last_history['line_source_reg_no']}")
   

        newest_data = []
        for index, history in enumerate(historys):

            if index == 0:
                stock_after = history['stock_after']
            else:
                last_adjustment = newest_data[index-1]['adjustment']
                last_stock_after = newest_data[index-1]['stock_after']

                add=False
                if last_adjustment < 0:
                    last_adjustment = abs(last_adjustment)
                    add=True

                if add:
                    stock_after = last_stock_after + last_adjustment
                else:
                    stock_after = last_stock_after - last_adjustment

            line_data = {
                'line_source_reg_no': history['line_source_reg_no'],
                'adjustment': history['adjustment'],
                'stock_after': stock_after,
                'reg_no': history['reg_no'],
                'created_date': history['created_date']
            }

            newest_data.append(line_data)
           
            InventoryHistory.objects.filter(reg_no=history['reg_no']).update(
                stock_after=stock_after
            )
        
            
        self.recalculate_inventory_valuations(
            first_date=last_history["created_date"], 
            end_date=first_history["created_date"]
        )

    def delete(self, *args, **kwargs):

        StockLevel.objects.filter(
            store=self.store,
            product=self.product,
        ).update(units=F('units') - self.adjustment)

        super(InventoryHistory, self).delete(*args, **kwargs)

        

    def save(self, *args, **kwargs):

        created = self.pk is None

        should_recalculate = InventoryHistory.objects.filter(
            store=self.store,
            product=self.product,
            created_date__gte=self.created_date
        ).exists()

        if self.product:
            self.product_name = self.product.name

        if self.store:
            self.store_name = self.store.name

        if self.user:
            self.user_name = self.user.get_full_name()

        # Update change_source_desc
        self.update_change_source_desc()

        """If reg_no is 0 get a unique reg_no"""
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(InventoryHistory, self).save(*args, **kwargs)

        if created:
            # Recalculate stock afters
            self.start_recalculating_stock_afters_forward(should_recalculate)


        






# ========================== START product disassembly models

class ProductTransform(models.Model):
    PRODUCT_TRANSFORM_PENDING = 0
    PRODUCT_TRANSFORM_RECEIVED = 1
    PRODUCT_TRANSFORM_CLOSED = 2

    PRODUCT_TRANSFORM_CHOICES = [
        (
            PRODUCT_TRANSFORM_PENDING,
            "Pending",
        ),
        (
            PRODUCT_TRANSFORM_RECEIVED,
            "Received",
        ),
        (
            PRODUCT_TRANSFORM_CLOSED,
            "Closed",
        ),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    status = models.IntegerField(
        verbose_name="status",
        choices=PRODUCT_TRANSFORM_CHOICES,
        default=PRODUCT_TRANSFORM_PENDING,
    )
    order_completed = models.BooleanField(
        verbose_name="order completed", 
        default=False, 
        editable=False
    )
    total_quantity = models.DecimalField(
        verbose_name="total quantity", max_digits=30, decimal_places=2, default=0
    )
    increamental_id = models.IntegerField(
        verbose_name='increamental id',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )

    is_auto_repackaged = models.BooleanField(
        verbose_name="is auto repackaged", 
        default=False,
    )
    auto_repackaged_source_desc = models.CharField(
        verbose_name="auto repackaged source desc", max_length=50, blank=True, default=""
    )
    auto_repackaged_source_reg_no = models.BigIntegerField(
        verbose_name="auto repackaged source reg no",
        default=0,
    )
    
    
    def __str__(self):
        return f"DS{self.increamental_id}"

    def get_created_by(self):
        return self.user.get_full_name()

    def get_store_data(self):
        return {"name": self.store.name, "reg_no": self.store.reg_no}

    def get_store_name(self):
        return self.store.name

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)

    def get_completed_date(self, local_timezone):
        """Return the completion date in local time format"""
        return utc_to_local_datetime_with_format(self.completed_date, local_timezone)

    # Make created_date to be filterable
    get_created_date.admin_order_field = "created_date"

    def get_expected_date(self, local_timezone):
        """Return the expected date in local time format"""
        return utc_to_local_datetime_with_format(self.expected_date, local_timezone)

    # Make expected_date to be filterable
    get_expected_date.admin_order_field = "expected_date"

    # TODO Test this
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)

    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = "created_date"

    def get_line_data(self):
        line_queryset = list(
            self.producttransformline_set.all()
            .order_by("id")
            .values(
                "source_product_info", 
                "target_product_info", 
                "quantity", 
                "added_quantity",
                "cost", 
                "amount", 
                'is_reverse',
                "reg_no"
            )
        )

        lines = []
        for line in line_queryset:
            lines.append(
                {
                    "source_product_info": line["source_product_info"],
                    "target_product_info": line["target_product_info"],
                    "quantity": str(line["quantity"]),
                    "added_quantity": str(line["added_quantity"]),
                    "cost": str(line["cost"]),
                    "amount": str(line["amount"]),
                    "is_reverse": line["is_reverse"],
                    "reg_no": line["reg_no"],
                }
            )

        return lines

    def update_stock_Level(self): 

        if not self.order_completed:
     
            if self.status == ProductTransform.PRODUCT_TRANSFORM_RECEIVED:

                # Update order completed and completed date
                self.order_completed = True

                lines = self.producttransformline_set.all()

                for line in lines:
                    
                    try:
                        source_product = line.source_product
                        target_product = line.target_product

                        product_map = source_product.productions.filter(product_map=target_product).first()

                        is_reverse_repackaging = False

                        if not product_map:
                            product_map = target_product.productions.filter(product_map=source_product).first()
                            is_reverse_repackaging = True

                        if not product_map: continue

                        total_units = StockLevel.objects.filter(product=target_product).aggregate(
                            units=Coalesce(Sum('units'), Decimal(0.00))
                        )['units']

                        current_stock = abs(total_units) # We don't want negative stock
                        current_cost = line.target_product.cost
                        current_stock_value = current_stock * current_cost

                        if not is_reverse_repackaging:
                            po_stock = line.quantity * product_map.quantity
                        else:
                            po_stock = line.quantity / product_map.quantity

                        po_cost = line.cost
                        po_total_cost = po_stock * po_cost

                        new_stock = current_stock + po_stock
                        
                        if new_stock:
                            new_cost = (current_stock_value + po_total_cost) / new_stock 
                        else:
                            new_cost = current_cost

                        # Save product's new cost
                        target_product.cost = new_cost
                        target_product.save()

                        StockLevel.update_level(
                            user=self.user,
                            store= self.store, 
                            product=source_product, 
                            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
                            change_source_reg_no=self.reg_no,
                            change_source_name=self.__str__(),
                            line_source_reg_no=f'{line.reg_no}0',
                            adjustment=line.quantity, 
                            update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING,
                            created_date=self.created_date
                        ) 
                        
                        StockLevel.update_level(
                            user=self.user,
                            store= self.store, 
                            product=target_product, 
                            inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REPACKAGE,
                            change_source_reg_no=self.reg_no,
                            change_source_name=self.__str__(),
                            line_source_reg_no=f'{line.reg_no}1',
                            adjustment=po_stock, 
                            update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING,
                            created_date=self.created_date
                        ) 

                        product_map = source_product.productions.filter(product_map=target_product)

                    except Exception as e:  # pylint: disable=bare-except
                        LoggerManager.log_critical_error()

    def increment_increamental_id(self, created, count_user):

        if not created: return

        last_store = ProductTransformCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_store:
            self.increamental_id = last_store.increamental_id + 1
        else:
            self.increamental_id = 1000

    def create_transfer_order_count_model(self, count_user):
        """
        Create ProductTransformCount
        """
        # We input created date to ease analytics testing
        ProductTransformCount.objects.create(
            user=count_user,
            reg_no=self.reg_no,
            created_date=self.created_date
        )

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        # Increament increamental_id
        self.increment_increamental_id(created, count_user)

        # Update stock if it's neccessary
        self.update_stock_Level()


        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(ProductTransform, self).save(*args, **kwargs)

        if created:
            self.create_transfer_order_count_model(count_user)


class ProductTransformCount(models.Model):
    user = models.ForeignKey(
        get_user_model(), 
        on_delete=models.CASCADE
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

    def __str__(self):
        return f'DS Count ({self.user})'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def increment_increamental_id(self, created):

        if not created: return

        # Get user that will be used to create increamental id
        count_user = self.user
        if self.user.user_type == EMPLOYEE_USER:
            count_user = get_user_model().objects.get(profile__employeeprofile__user=self.user)

        last_model = ProductTransformCount.objects.filter(
            user=count_user
        ).order_by('increamental_id').last()

        if last_model:
            self.increamental_id = last_model.increamental_id + 1
        else:
            self.increamental_id = 1000

    def save(self, *args, **kwargs):

        # Check if this object is being created
        created = self.pk is None

        # Increament increamental_id
        self.increment_increamental_id(created)

        super(ProductTransformCount, self).save(*args, **kwargs)


class ProductTransformLine(models.Model):
    product_transform = models.ForeignKey(ProductTransform, on_delete=models.CASCADE)
    source_product = models.ForeignKey(
        Product,  
        on_delete=models.CASCADE,
        related_name="source_product"
    )
    target_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name="target_product"
    )
    source_product_info = models.JSONField(verbose_name="source product info", default=dict)
    target_product_info = models.JSONField(verbose_name="target product info", default=dict)
    quantity = models.DecimalField(
        verbose_name="quantity", max_digits=30, decimal_places=2, default=0
    )
    added_quantity = models.DecimalField(
        verbose_name="added quantity", max_digits=30, decimal_places=2, default=0
    )
    cost = models.DecimalField(
        verbose_name="cost", max_digits=30, decimal_places=2, default=0
    )
    amount = models.DecimalField(
        verbose_name="amount", max_digits=30, decimal_places=2, default=0
    )
    is_reverse = models.BooleanField(
        verbose_name='is reverse',
        default=False
    )
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        # unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )

    def __str__(self):
        return self.target_product.name
    
    def update_is_reverse(self):
        """
        Is reverse is false if we are repackaging from sack to piece and True
        otherwise
        """
        product_map = self.source_product.productions.filter(product_map=self.target_product).first()

        is_reverse_repackaging = False
        if not product_map:
            product_map = self.target_product.productions.filter(product_map=self.source_product).first()
            is_reverse_repackaging = True

        self.is_reverse = is_reverse_repackaging

    def save(self, *args, **kwargs):

        """ Check if this object is being created """
        created = self.pk is None

        # This makes sure that product_info value is only update once
        # if not self.product_info:
        self.source_product_info = {
            "name": self.source_product.name,
            "reg_no": self.source_product.reg_no,
        }

        self.target_product_info = {
            "name": self.target_product.name,
            "reg_no": self.target_product.reg_no,
        }

        self.amount = self.cost * self.quantity

        # Update is reverse
        self.update_is_reverse()

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(ProductTransformLine, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        # if created:
        #     self.update_stock_level(created) 150000