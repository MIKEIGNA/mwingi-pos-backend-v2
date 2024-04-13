from decimal import Decimal, InvalidOperation

from django.db import models
from django.db.models.aggregates import Count
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce

from accounts.utils.currency_choices import CURRENCY_CHOICES
from accounts.utils.validators import validate_code
from core.image_utils import ModelImageHelpers
from core.queryset_helpers import QuerysetFilterHelpers
from core.time_utils.date_helpers import DateHelperMethods
from core.time_utils.time_localizers import utc_to_local_datetime_with_format
from firebase.models import FirebaseDevice


from profiles.models import Profile
from stores.models import Store, Tax, Category

"""
=============== Product ===============
"""
def product_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/images/profiles/<profiile.reg_no>_<filename>.jpg

    path = '{}{}_{}'.format(
        settings.IMAGE_SETTINGS['product_images_dir'], instance.reg_no, filename)

    return path 

class Product(models.Model):
    # This field is required by all models that will use ApiImageUploader()
    # to upload images using REST Api
    IMAGE_SUB_DIRECTORY = settings.IMAGE_SETTINGS['product_images_dir']

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    stores = models.ManyToManyField(Store)
    tax = models.ForeignKey(
        Tax,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    variants = models.ManyToManyField('ProductVariant', blank=True,)
    bundles = models.ManyToManyField('ProductBundle', blank=True,)
    productions = models.ManyToManyField('ProductProductionMap', blank=True,)
    modifiers = models.ManyToManyField('Modifier', blank=True,)
    image = models.ImageField(
        upload_to=product_directory_path,
        default=settings.IMAGE_SETTINGS['no_image_url'],
        verbose_name='image',
    )
    color_code = models.CharField(
        verbose_name='color code',
        max_length=7,
        default=settings.DEFAULT_COLOR_CODE,
        validators=[validate_code, ],
    )
    name = models.CharField(
        verbose_name='name',
        max_length=100,
        # db_collation="case_insensitive"
    )
    cost = models.DecimalField(
        verbose_name='cost',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    price = models.DecimalField(
        verbose_name='price',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    average_price = models.DecimalField(
        verbose_name='average price',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    sku = models.CharField(
        verbose_name='sku',
        max_length=50,
        blank=True,
        default=''
    )
    barcode = models.CharField(
        verbose_name='barcode',
        max_length=50,
        blank=True,
        default=''
    )
    sold_by_each = models.BooleanField(
        verbose_name='sold by each',
        default=True
    )
    is_bundle = models.BooleanField(
        verbose_name='is bundle',
        default=False
    )
    track_stock = models.BooleanField(
        verbose_name='track stock',
        default=True 
    )
    variant_count = models.IntegerField(
        verbose_name='variant count',
        default=0,
    )
    production_count = models.IntegerField(
        verbose_name='production count',
        default=0,
    )
    is_variant_child = models.BooleanField(
        verbose_name='is variant child',
        default=False
    )
    show_product = models.BooleanField(
        verbose_name='show product',
        default=True
    )
    show_image = models.BooleanField(
        verbose_name='show image',
        default=False
    )
    is_transformable = models.BooleanField(
        verbose_name='is_transformable',
        default=False
    )
    tax_rate = models.DecimalField(
        verbose_name='tax rate',
        max_digits=30,
        decimal_places=2
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
    )
    loyverse_variant_id = models.UUIDField(
        verbose_name='loyverse variant id',
        # editable=False,
        db_index=True,
        null=True,
        blank=True,
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
        default=timezone.now
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

    def __str__(self):
        return str(self.name)

    def get_name(self):
        return self.name

    def get_profile(self):
        """ Returns the product's profile"""
        return self.profile

    def get_currency(self):
        return self.profile.get_currency()

    def get_price_and_currency(self):
        return f"{CURRENCY_CHOICES[self.profile.get_currency()][1]} {self.price}"

    def get_price_and_currency_desc(self):
        return f"Price: {CURRENCY_CHOICES[self.profile.get_currency()][1]} {self.price}"

    def get_currency_initials(self):
        return self.profile.get_currency_initials()

    def get_category_data(self):
        if self.category:
            return {
                'name': self.category.name,
                'reg_no': self.category.reg_no
            }
        return {}

    def get_tax_data(self):
        if self.tax:
            return {
                'name': self.tax.name,
                'rate': str(self.tax.rate),
                'reg_no': self.tax.reg_no 
            }
        return {}

    def get_sales_count(self):

        total_units_sum = self.receiptline_set.all().aggregate(
            Sum('units')).get('units__sum', 0)

        return total_units_sum if total_units_sum else 0

    def get_sales_total(self):

        # When we use django's aggregate and Sum for this operation, we lose the decimal
        # precision. THats why we are adding the prices on our own
        sales = self.receiptline_set.all().values('price')

        sales_total = 0
        for sale in sales:
            sales_total += sale['price']

        return '{} {}'.format(CURRENCY_CHOICES[self.profile.get_currency()][1], sales_total)

    def get_inventory_valuation(self, store_reg_nos = None):
        """
        Returns a product's inventory valuation
        """
        data = {}

        if self.variant_count:
            data = self._get_inventory_valuation_for_variant(store_reg_nos)
        else:
            data = self._get_inventory_valuation_for_single_product(store_reg_nos)

        return {
            'name': self.name,
            'in_stock': str(data['in_stock']),
            'cost': str(self.cost),
            'inventory_value': str(data['inventory_value']),
            'retail_value': str(data['retail_value']),
            'potential_profit': str(data['potential_profit']),
            'margin': str(data['margin']),
            'variants': data.get('variants', None)
        }

    def _get_inventory_valuation_for_single_product(self, store_reg_nos = None):
        """
        Returns a single product's inventory valuation
        """

        levels = self.stocklevel_set.filter(
            units__gte=0.1,
            price__gte=1,
            inlude_in_price_calculations=True,
            store__reg_no__in=store_reg_nos
        ).values_list('price', flat=True)

        average_price = 0
        if levels:
            average_price = round(sum(levels)/len(levels), 2)
        
        if store_reg_nos:
            stock_queryset = self.stocklevel_set.filter(
                store__reg_no__in=store_reg_nos
            )
        else:
            stock_queryset = self.stocklevel_set.all()

        total_units_sum = stock_queryset.aggregate(
                Sum('units')).get('units__sum', 0)

        in_stock = total_units_sum if total_units_sum else 0
        inventory_value = in_stock * self.cost
        retail_value = in_stock * average_price
        potential_profit = retail_value - inventory_value

        try:
            margin = (potential_profit * 100) / retail_value
        except: 
            margin = 0

        return {
            'name': self.name,
            'in_stock': round(in_stock, 2),
            'cost': round(self.cost, 2),
            'inventory_value': round(inventory_value, 2),
            'retail_value': round(retail_value, 2),
            'potential_profit': round(potential_profit, 2),
            'margin': round(margin, 2),
        }

    def _get_inventory_valuation_for_variant(self, store_reg_nos = None):
        """
        Returns inventory valuation from variant parent and it's children
        """
        variants_queryset = Product.objects.filter(productvariant__product=self)

        if store_reg_nos:
            variants_queryset = variants_queryset.filter(
                stores__reg_no__in=store_reg_nos
            )

        variants_queryset = variants_queryset.order_by('id')

        # Use distinct to prevent unwanted dupblicates when using many to many
        variants = variants_queryset.distinct()

        variants_data = [v.get_inventory_valuation(store_reg_nos) for v in variants]

        in_stock =0
        inventory_value = 0
        retail_value = 0
        for variant in variants_data:
            
            in_stock += Decimal(variant['in_stock'])
            inventory_value += Decimal(variant['inventory_value'])
            retail_value += Decimal(variant['retail_value'])
                    
        potential_profit = retail_value - inventory_value

        try:
            margin = (potential_profit * 100) / retail_value
        except InvalidOperation:
            margin = 0
        except ZeroDivisionError:
            margin = 0

        return {
            'name': self.name,
            'in_stock': in_stock,
            'cost': self.cost,
            'inventory_value': inventory_value,
            'retail_value': retail_value,
            'potential_profit': potential_profit,
            'margin': round(margin, 2),
            'variants': variants_data
        }

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_image_url(self):
        """
        Return image url or an empty string
        """
        try:
            return self.image.url
        except: # pylint: disable=bare-except
            return ""

    def get_modifier_list(self):

        queryset = self.modifiers.all().order_by('id').values_list('reg_no')

        modifiers = [mod[0] for mod in queryset]

        return modifiers

    def create_product_count(self, created):

        # Create ProductCount
        if created:
            # We input created date to ease analytics testing
            ProductCount.objects.create(
                profile=self.profile,
                tax=self.tax,
                category=self.category,
                name=self.name,
                cost=self.cost,
                price=self.price,
                reg_no=self.reg_no,
                created_date=self.created_date)

    def add_store_and_create_stock_level(self, store):
        """
        Adds store to model's stores
        """
        if store: self.stores.add(self.store)

    def remove_store_and_delete_stock_level(self, store):
        """
        Adds store to model's stores and creates a store current
        """
        # To avoid circular import error
        from inventories.models import StockLevel

        if store:
            self.stores.remove(self.store)

            StockLevel.objects.filter(store=store, product=self).delete()

    def get_variants_data_from_store(self, store_reg_no):
        """
        Returns a dict with variant data for a product from a store 

        Args:
            store_reg_no
        """

        data = {}

        # Get option data
        options = self.productvariantoption_set.all().order_by('id')

        i=0
        option_data = []
        for opt in options:
            
            # Get option choice data
            choices = opt.productvariantoptionchoice_set.all().order_by('id')

            choice_option_data = []
            for choice in choices:
                choice_option_data.append(
                    {'name': choice.name, 'reg_no': choice.reg_no}
                )

            option_data.append(
                { 
                    'name': opt.name, 
                    'reg_no': opt.reg_no,
                    'values': choice_option_data,
                }
            )

            i+=0

        # Get option choice data
        variants = Product.objects.filter(
            productvariant__product=self, stores__reg_no=store_reg_no
        ).order_by('id')

        variant_data = [
            {
                'name': variant.name,
                'price': str(variant.price),
                'cost': str(variant.cost),
                'sku': variant.sku,
                'barcode': variant.barcode,
                'stock_level': variant.get_store_stock_units(store_reg_no),
                'show_product': variant.show_product,
                'reg_no': variant.reg_no,
            } for variant in variants]

        data['options'] = option_data
        data['variants'] = variant_data

        return data

    def get_total_stock_level(self, store_reg_nos=None):
        """
        Returns a string with the total stock level for a product from the stores
        whose reg nos are in store_reg_nos

        Args:
            store_reg_nos - A list of stores reg nos
        """

        total_stock_units = 0

        if store_reg_nos:

            total_stock_units = self.stocklevel_set.filter(
                product=self, store__reg_no__in=store_reg_nos
                ).aggregate(
                    Sum('units')).get('units__sum', 0)

        else:
            total_stock_units = self.stocklevel_set.filter(
                product=self).aggregate(Sum('units')).get('units__sum', 0)

        total_stock_units = total_stock_units if total_stock_units else 0

        return str(total_stock_units)

    def get_store_stock_units(self, store_reg_no):

        result = {
            'units': '0',
            'minimum_stock_level': '0'
        }

        try:
           
            stock = self.stocklevel_set.get(
                product=self, 
                store__reg_no=store_reg_no
            )
                
            result['units'] = str(stock.units)
            result['minimum_stock_level'] = str(stock.minimum_stock_level)
        
        except: # pylint: disable=bare-except
            pass

        return result 
    
    def get_store_stock_level_data(self, store_reg_no):

        result = {
            'units': '0',
            'minimum_stock_level': '0',
            'is_sellable': False,
            'price': '0.00',
        }

        try:
           
            stock = self.stocklevel_set.get(
                product=self, 
                store__reg_no=store_reg_no
            )
                
            result['units'] = str(stock.units)
            result['minimum_stock_level'] = str(stock.minimum_stock_level)
            result['is_sellable'] = str(stock.is_sellable)
            result['price'] = str(stock.price)
        
        except: # pylint: disable=bare-except
            pass

        return result 

    def get_index_variants_data(self, store_reg_nos=None):
        """
        Used by product api web index pages

        Returns a dict with variant data for a product from the stores
        whose reg nos are in store_reg_nos

        Args:
            store_reg_nos - A list of stores reg nos
        """

        # Get option choice data
        if store_reg_nos:
            variants = Product.objects.filter(
                productvariant__product=self, stores__reg_no__in=store_reg_nos
            ).order_by('id')

        else:
            variants = Product.objects.filter(
                productvariant__product=self
            ).order_by('id')

        variant_data = [
            {
                'name': variant.name,
                'valuation_info': variant.get_valuation_info(store_reg_nos),
            } for variant in variants]

        return variant_data

    def get_valuation_info(self, store_reg_nos=None):
        """
        Used by product api web index pages

        Returns a dict with the product's price, cost and total stock levelfrom 
        the stores whose reg nos are in store_reg_nos

        Args:
            store_reg_nos - A list of stores reg nos
        """
        total_units_sum = Decimal(self.get_total_stock_level(store_reg_nos))

        in_stock = total_units_sum if total_units_sum else 0
        inventory_value = in_stock * self.cost
        retail_value = in_stock * self.price

        potential_profit = retail_value - inventory_value

        try:
            margin = round((potential_profit * 100) / retail_value, 2)
        except: # pylint: disable=bare-except 
            margin = 0

        return {
            'stock_units': str(total_units_sum),
            'margin': str(margin).replace('.00', '')
        }

    # TODO Test this
    def get_product_view_variants_data(self, employee_profile=None):
        """
        Returns a dict with variant data for a product in product view
        """
        queryset = None
        if employee_profile:
            queryset = Product.objects.filter(
                stores__employeeprofile=employee_profile,
                productvariant__product=self
            ).distinct()
        else:
            queryset = Product.objects.filter(productvariant__product=self)

        variants = queryset.order_by('id')

        variant_data = [
            {
                'name': variant.name,
                'price': str(variant.price),
                'cost': str(variant.cost),
                'sku': variant.sku,
                'barcode': variant.barcode,
                'reg_no': variant.reg_no,
                'registered_stores': variant.get_product_view_stock_level_list(employee_profile)
            } for variant in variants]

        return variant_data

    # TODO Test this 
    def get_product_view_bundles_data(self):

        queryset = ProductBundle.objects.filter(product=self).values(
            'product_bundle__name',
            'product_bundle__sku',
            'product_bundle__reg_no',
            'quantity'
        )

        data = []
        for q in queryset:
            data.append({
                'name': q['product_bundle__name'],
                'sku': q['product_bundle__sku'],
                'reg_no': q['product_bundle__reg_no'],
                'quantity': str(q['quantity']),
            })

        return data
    
    # TODO Test this
    def get_product_view_production_data(self):

        queryset = ProductProductionMap.objects.filter(product=self).values(
            'name',
            'product_map__name',
            'product_map__sku',
            'product_map__reg_no',
            'is_auto_repackage',
            'quantity'
        ).order_by('id')

        data = []
        for q in queryset:
            data.append({
                'name': q['product_map__name'],
                'sku': q['product_map__sku'],
                'reg_no': q['product_map__reg_no'],
                'is_auto_repackage': q['is_auto_repackage'],
                'quantity': str(q['quantity']),
            })
            
        return data
    
    def get_product_view_transform_data(self, store, filter_for_repackaging=False):

        from inventories.models import StockLevel

        queryset = ProductProductionMap.objects.filter(product=self).order_by('id').values(
            'name',
            'product_map__name',
            'product_map__sku',
            'product_map__reg_no',
            'quantity'
        ) 

        if filter_for_repackaging:
            queryset = queryset.filter(is_auto_repackage=True)

        parent_product_map = []
        for q in queryset:
            parent_product_map.append({
                'name': q['product_map__name'],
                'sku': q['product_map__sku'],
                'reg_no': q['product_map__reg_no'],
                'current_quantity': str(StockLevel.objects.get(
                    product__reg_no=q['product_map__reg_no'], 
                    store=store,
                ).units),
                'equivalent_quantity': str(q['quantity'])
            })

        dd = Product.objects.filter(productions__product_map=self.pk).order_by('name')

        child_product_map = []
        for d in dd:

            if d == self: continue

            product_map_quantity = d.productions.get(product_map=self).quantity
            
            equivalent_quantity = 1/product_map_quantity

            child_product_map.append(
                {
                    'name': d.name,
                    'sku': d.sku,
                    'reg_no': d.reg_no,
                    'current_quantity': str(StockLevel.objects.get(
                        product=d, 
                        store=store,
                    ).units),
                    'equivalent_quantity': str(equivalent_quantity)
                }  
            )

        product_map = None
        is_reverse = False

        if parent_product_map:
            product_map =  parent_product_map
        else:
            product_map = child_product_map
            is_reverse = True

        data = {
            'name': self.name,
            'reg_no': self.reg_no,
            'cost': str(self.cost),
            'current_quantity': str(self.stocklevel_set.get(product=self, store=store).units),
            'is_reverse': is_reverse,
            'product_map': product_map,
            
        }

        return data

    def get_product_view_stock_level_list(self, employee_profile=None):
        """
        Returns a list with dicts that have store names and reg_nos
        """
        queryset = None
        if employee_profile:
            queryset = self.stocklevel_set.filter(store__employeeprofile=employee_profile)
        else:
            queryset = self.stocklevel_set.all()

        queryset = queryset.filter(store__is_deleted=False)
        
        queryset = queryset.order_by('store__name').values(
            'store__name', 
            'store__reg_no', 
            'minimum_stock_level', 
            'units', 
            'is_sellable',
            'price'

        )

        stores = [
            {
                'store_name': s['store__name'], 
                'store_reg_no': s['store__reg_no'],
                'minimum_stock_level': str(s['minimum_stock_level']),
                'units': str(s['units']),
                'is_sellable': s['is_sellable'],
                'price': str(s['price']),
            } for s in queryset]

        return stores

    def update_variant_product_to_match_parent(self):
        """
        Performs for parent products
        
        Syncs some variant product fields with that of parents
        """

        if not self.is_variant_child and self.variant_count > 0:
            # This update will be done silently without calling each variant
            # product's save method
            Product.objects.filter(productvariant__product=self).update(
                track_stock=self.track_stock
            )
        
    def sync_variant_with_parent(self, created):
        """
        Performs for variant products

        Syncs some variant product fields with that of parents
        """
        if self.is_variant_child and not created:

            # During creation, this method is called multiple times. During the
            # very first calls, product variant has not been created so this raises
            # an error
            try:
                self.track_stock = Product.objects.get(variants=self.productvariant).track_stock
            except Product.productvariant.RelatedObjectDoesNotExist:
                pass

    def update_category_product_count(self):
        """
        This updates category's save proudct count
        """

        if self.is_variant_child: # Ignore variant childs
            return

        if self.category:
            self.category.save()

        return

    def update_categories_after_product_save(self, created, old_category):
        """
        This updates category's save proudct count
        """

        if self.is_variant_child:  # Ignore variant childs
            return

        if created:
            self.update_category_product_count()

        else:
            new_category = self.category

            if old_category == new_category:
                return

            else:
                if old_category:
                    old_category.save()

                if new_category:
                    new_category.save()

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a product creation message. Otherwise we
        send a category edit message
        """
        from firebase.message_sender_product import ProductMessageSender

        if created:
            ProductMessageSender.send_product_creation_update_to_users(self)
        else:
            ProductMessageSender.send_product_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Call this method before deleting the model
        Send a tax delete message.
        """
        from firebase.message_sender_product import ProductMessageSender

        stores = self.stores.all()

        for store in stores:
            tokens = FirebaseDevice.objects.filter(store=store).values_list('token')

        ProductMessageSender.send_product_deletion_update_to_users(self, tokens)

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):

        product_data = {}
        variant_data = []
        if self.variant_count:
            product_data, variant_data = self._get_report_data_for_variant_product(
                local_timezone,
                date_after=date_after,
                date_before=date_before,
                store_reg_nos=store_reg_nos,
                user_reg_nos=user_reg_nos
            )
            
        else:
            product_data = self._get_report_data_for_single_product(
                self,
                local_timezone,
                date_after=date_after,
                date_before=date_before,
                store_reg_nos=store_reg_nos,
                user_reg_nos=user_reg_nos
            )

        return {
            'is_variant': self.variant_count > 0,
            'product_data': product_data,
            'variant_data': variant_data 
        }     

    def _get_report_data_for_single_product(
        self, 
        product,
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):
        """
        Returns product sales data if they are available. If there is no data,
        None is returned instead
        """

        # We import here to avoid cyclic imports error
        from sales.models import ReceiptLine
        
        queryset = ReceiptLine.objects.filter(product=product)

        if not queryset:
            return None

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

        queryset = queryset.aggregate(
            items_sold=Coalesce(Sum('units'), Decimal(0.00)), 
            net_sales=Coalesce(Sum('price'), Decimal(0.00)), 
            cost=Coalesce(Sum('cost'), Decimal(0.00)),
        )

        if self.sold_by_each:
            items_sold = round(queryset['items_sold'], 0)
        else:
            items_sold = round(queryset['items_sold'], 2)

        net_sales = round(queryset['net_sales'], 2)
        cost = round(queryset['cost'], 2)
        profit = net_sales - cost

        return {
            'name': product.name,
            'items_sold': str(items_sold),
            'net_sales': str(net_sales),
            'cost': str(cost),
            'profit': str(round(profit, 2))
        }

    def _get_report_data_for_variant_product(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):

        queryset = Product.objects.filter(productvariant__product=self)

        items_sold = 0
        net_sales = 0 
        cost = 0
        profit = 0 

        variant_data = []
        for variant in queryset:
            data = self._get_report_data_for_single_product(
                variant,
                local_timezone,
                date_after=date_after,
                date_before=date_before,
                store_reg_nos=store_reg_nos,
                user_reg_nos=user_reg_nos
            )
            
            # Make sure variant has data
            if data:
                variant_data.append(data)

                items_sold += Decimal(data['items_sold'])
                net_sales += Decimal(data['net_sales'])
                cost += Decimal(data['cost'])
                profit += Decimal(data['profit'])


        product_data =  {
            'name': self.name,
            'items_sold': str(items_sold),
            'net_sales': str(net_sales),
            'cost': str(cost),
            'profit': str(profit)
        }

        return product_data, variant_data

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

    
    # TODO #2 Test this add_stores_to_product
    def add_stores_to_product(self, created):
        """
        Add product to stores if the product is being created for the first time
        """
       
        stores_ids = Store.objects.filter(profile=self.profile).values_list(
            'id', flat=True
        )

        current_stores_ids = self.stores.all().values_list('id', flat=True)
        
        store_ids_to_add = []
        for store_id in stores_ids:
            if store_id not in current_stores_ids:
                store_ids_to_add.append(store_id)

        self.stores.add(*store_ids_to_add)

        # self.create_stock_levels_for_products_that_dont_have()
    def create_stock_levels_for_products_that_dont_have(self):

        from inventories.models import StockLevel

        stores = self.stores.all()

        for store in stores:
            created_stock_level = StockLevel.objects.get_or_create(
                store=store,
                product=self,
                price=self.price,
            )

    def get_stock_levels(self):

        levels = self.stocklevel_set.all().values(
            'is_sellable',
            'price',
            'loyverse_store_id'
        )

        data = [
            {
                'is_sellable': l['is_sellable'],
                'price': str(l['price']),
                'loyverse_store_id': str(l['loyverse_store_id'])
            }
            for l in levels
        ]

        return list(data)
    
    def update_product_average_price(self):
        """
        Updates product price to the average of all stores stock levels
        """
        levels = self.stocklevel_set.filter(
            units__gte=0.1,
            price__gte=1,
            inlude_in_price_calculations=True
        ).values_list('price', flat=True)

        if levels:
            self.average_price = round(sum(levels)/len(levels), 2)

    

    def save(self, *args, **kwargs):
        # Make sure track stock is always True
        self.track_stock = True

        # This prevents NOT NULL constraint failed: products_product.barcode
        if self.barcode == None: self.barcode = ''
        if self.cost == None: self.cost = Decimal('0.00')

        self.average_price = self.price

        # Prevent vatiant products from having tax and category assigned to them
        if self.is_variant_child:
            self.tax = None
            self.category = None

        if self.tax:
            self.tax_rate = self.tax.rate
            self.loyverse_tax_id = self.tax.loyverse_tax_id
        else:
            self.tax_rate = Decimal('0.00')
            self.loyverse_tax_id = None

        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        """ Check if this object is being created """
        created = self.pk is None

        # Get old category before saving product
        old_category = None
        if not created and not self.is_variant_child:
            old_category = Product.objects.get(
                reg_no=self.reg_no
            ).category

        # Syncs some variant product fields with that of parents
        self.sync_variant_with_parent(created)
        
        # Don't update average price when product is being created
        if not created:
            self.update_product_average_price()


        time_now = timezone.now()


        # print(f"Product created1 {created} > {self.pk}, {time_now}")
        
        # Call the "real" save() method.
        super(Product, self).save(*args, **kwargs)

        

        # Create initial image during model creation
        self.create_inital_image(created)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """

        # Syncs some variant product fields with that of parents
        self.update_variant_product_to_match_parent()

        self.create_product_count(created)

        # Update categories' product counts
        self.update_categories_after_product_save(created, old_category)

        self.add_stores_to_product(created)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        # print(f"Product created2 {created} > {self.pk}, {time_now}")
        # self.send_firebase_update_message(created)

    def delete(self, *args, **kwargs):

        # Perform this method before product delete
        self.send_firebase_delete_message()

        # Call the "real" delete() method.
        super(Product, self).delete(*args, **kwargs)
        
        # Update category's product count
        self.update_category_product_count()

    def soft_delete(self):
        """
        Soft deletes the store
        """

        # Perform this method before product delete
        self.send_firebase_delete_message()

        self.is_deleted = True
        self.deleted_date = timezone.now()
        self.save()

        
"""
=============== ProductCount ===============
"""
class ProductCount(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    tax = models.ForeignKey(
        Tax,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name='name',
        max_length=100,
    )
    cost = models.DecimalField(
        verbose_name='cost',
        max_digits=30,
        decimal_places=2
    )
    price = models.DecimalField(
        verbose_name='price',
        max_digits=30,
        decimal_places=2
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
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


"""
=============== ProductBundle ===============
"""
class ProductBundle(models.Model):
    product_bundle = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(verbose_name='quantity',default=0)

    def __str__(self):
        """ Returns the variant's name as a string"""
        return f'Bundle {self.product_bundle.name}'
    

"""
=============== ProductProduction ===============
"""

class ProductProductionMap(models.Model):
    name = models.CharField(verbose_name='name', max_length=100)
    product_map = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(verbose_name='quantity',default=0)
    is_auto_repackage = models.BooleanField(
        verbose_name='is_auto_repackage',
        default=False
    )

    def __str__(self):
        """ Returns the product's name as a string"""
        return f'Production {self.product_map.name}'
    
"""
=============== ProductVariantOption ===============
"""
class ProductVariantOption(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='name',max_length=100)
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
    )

    def save(self, *args, **kwargs):

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(ProductVariantOption, self).save(*args, **kwargs)

"""
=============== ProductVariantOptionChoice ===============
"""
class ProductVariantOptionChoice(models.Model):
    product_variant_option = models.ForeignKey(ProductVariantOption,on_delete=models.CASCADE)
    name = models.CharField(verbose_name='name',max_length=100)
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
    )

    def save(self, *args, **kwargs):

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(ProductVariantOptionChoice, self).save(*args, **kwargs)


"""
=============== ProductVariant ===============
"""
class ProductVariant(models.Model):
    product_variant = models.OneToOneField(Product, on_delete=models.CASCADE)
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
    )

    def __str__(self):
        """ Returns the variant's name as a string"""
        return f'Variant {self.product_variant.name}'

    def save(self, *args, **kwargs):

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            self.reg_no = self.product_variant.reg_no

        # Call the "real" save() method.
        super(ProductVariant, self).save(*args, **kwargs)



"""
=============== Modifier ===============
"""
class Modifier(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    stores = models.ManyToManyField(Store)
    name = models.CharField(
        verbose_name='name',
        max_length=100,
    )
    description = models.CharField(
        verbose_name='description',
        max_length=100,
        default=''
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        """ Returns the store's name as a string"""
        return str(self.name)

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_modifier_options_count(self):
        """
        Returns the number of employees in the store
        """
        return self.modifieroption_set.all().count()

    def get_modifier_options(self):

        queryset = self.modifieroption_set.all().order_by('id')

        opts = [
            {
                'name': q.name, 
                'price': str(q.price), 
                'reg_no': str(q.reg_no)
            } for q in queryset]

        return opts

    def get_store_count(self):
        """
        Returns the number of employees in the store
        """
        return self.stores.all().count()

    def update_description(self):
        """
        Creates modifier description from the modifiers options
        """
        
        mod_options = self.modifieroption_set.all().order_by('id').values_list('name')

        names = [op[0] for op in mod_options]

        full_names = ''

        i=0
        for name in names:
            if i==0:
                full_names += name
            else:
                full_names += f', {name}'

            i+=1

        description_limit = settings.MAX_MODIFIER_DESCRIPTION_LIMIT

        if len(full_names) > description_limit:
            self.description = f'{full_names[0: description_limit]} ...'
        else:
            self.description = full_names

    def send_firebase_update_message(self, created):
        """
        If created is true, we send a tax creation message. Otherwise we
        send a tax edit message
        """
        from firebase.message_sender_modifier import ModifierMessageSender

        if created:
            ModifierMessageSender.send_modifier_creation_update_to_users(self)
        else:
            ModifierMessageSender.send_modifier_edit_update_to_users(self)

    def send_firebase_delete_message(self):
        """
        Send a tax delete message.
        """
        from firebase.message_sender_modifier import ModifierMessageSender
        
        ModifierMessageSender.send_modifier_deletion_update_to_users(self)

    def get_report_data(
        self, 
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):

        queryset = self.modifieroption_set.all().order_by('id')

        total_gross_sales = 0
        total_quantity = 0

        data = []
        for option in queryset:
            option_data = self._get_report_data_for_modifier_option(
                option=option,
                local_timezone=local_timezone,
                date_after=date_after,
                date_before=date_before,
                store_reg_nos=store_reg_nos,
                user_reg_nos=user_reg_nos
            ) 

            # Make sure variant has data
            if option_data:
                data.append(option_data)

                total_gross_sales += Decimal(option_data['gross_sales'])
                total_quantity += option_data['quantity']

        return {
            'name': self.name,
            'gross_sales': str(total_gross_sales),
            'quantity': total_quantity,
            'options': data 
        }

    def _get_report_data_for_modifier_option(
        self, 
        option,
        local_timezone,
        date_after=None, 
        date_before=None, 
        store_reg_nos=None, 
        user_reg_nos=None):
        """
        Returns product sales data if they are available. If there is no data,
        None is returned instead
        """

        # We import here to avoid cyclic imports error
        from sales.models import ReceiptLine
        
        queryset = ReceiptLine.objects.filter(modifier_options=option)

        if not queryset:
            return None

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

        queryset = queryset.aggregate(
            gross_sales=Coalesce(Sum('modifier_options__price'), Decimal(0.00)), 
            quantity=Coalesce(Count('modifier_options'), 0)
        )

        return {
            'name': option.name,
            'gross_sales': str(round(queryset['gross_sales'], 2)),
            'quantity': queryset['quantity'],
        }

    def save(self, *args, **kwargs):
        """
        We disable modifiers from being able to be created
        """

        ### We disable

        # Call the "real" save() method.
        # super(Modifier, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Call the "real" delete() method.
        super(Modifier, self).delete(*args, **kwargs)
        
        self.send_firebase_delete_message()


"""
=============== ModifierOption ===============
"""
class ModifierOption(models.Model):
    modifier = models.ForeignKey(Modifier, on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name='name',
        max_length=100,
    )
    price = models.DecimalField(
        verbose_name='price',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
    )

    def __str__(self):
        """ Returns the store's name as a string"""
        return str(self.name)

    def update_modifier_description(self, created):
        self.modifier.save()

    def save(self, *args, **kwargs):

        # If reg_no is 0 get a unique one
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            # Get the model class
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        """ Check if this object is being created """
        created = self.pk is None

        # Call the "real" save() method.
        super(ModifierOption, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.update_modifier_description(created)

    def delete(self, *args, **kwargs):

        super(ModifierOption, self).delete(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.update_modifier_description(True)

