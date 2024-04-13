from collections import defaultdict
from pprint import pprint
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db.models.functions import Cast
from django.db.models import F, CharField, Value, DecimalField


from core.number_helpers import NumberHelpers
from core.queryset_helpers import QuerysetFilterHelpers
from core.time_utils.time_localizers import utc_to_local_datetime_with_format

from accounts.utils.user_type import TOP_USER
from inventories.models.stock_models import StockLevel
from stores.models import Category, Store, Tax
from products.models import Product

# ========================== START purchase order models
class InventoryValuation(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    reg_no = models.BigIntegerField(
        verbose_name="reg no",
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    created_date = models.DateTimeField(
        verbose_name="created date", default=timezone.now, db_index=True
    )

    def __str__(self):
        return f"IV{self.store.name}"

    def get_store_data(self):
        return {"name": self.store.name, "reg_no": self.store.reg_no}

    def get_store_name(self):
        return self.store.name

    def get_created_date(self, local_timezone=settings.LOCATION_TIMEZONE):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created date to be filterable
    get_created_date.admin_order_field = 'created_date'
    
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)
    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = 'created_date'

    @staticmethod
    def create_inventory_valutions(profile, created_date):
        
        stores = Store.objects.filter(profile=profile)

        store_map = {
            store.reg_no: store for store in stores
        }

        products = Product.objects.filter(stores__in=stores)

        product_map = {
            product.reg_no: product for product in products
        }

        stock_levels = StockLevel.objects.filter(store__in=stores).values(
            'store__reg_no', 
            'product__reg_no', 
            'product__cost', 
            'price', 
            'units',
            'is_sellable' 
        )

        inventory_valuations_map = {}
        for store in stores:
            inventory_valuation = InventoryValuation.objects.create(
                user=profile.user,
                store=store,
                created_date=created_date,
            )

            inventory_valuations_map[store.reg_no] = inventory_valuation

        for stock_level in stock_levels:
            store_reg_no = stock_level['store__reg_no']
            product_reg_no = stock_level['product__reg_no']
            is_sellable = stock_level['is_sellable']
            
            store = store_map.get(store_reg_no)
            product = product_map.get(product_reg_no)
            inventory_valuation = inventory_valuations_map.get(store_reg_no)
            
            units = stock_level['units']
            cost = stock_level['product__cost']
            price = stock_level['price']

            inventory_value, retail_value, potential_profit, margin = InventoryValuationLine.calculate_inventory_valuation_line_value(
                units=units, 
                cost=cost,
                price=price
            )

            if product.category:
                category_name = product.category.name
            else:
                category_name = ''

            InventoryValuationLine.objects.create(
                inventory_valution=inventory_valuation,
                product=product,
                price=price,
                cost=cost,
                units=units,
                barcode=product.barcode,
                sku=product.sku,
                category_name=category_name,
                is_sellable=is_sellable,
                inventory_value=inventory_value,
                retail_value=retail_value,
                potential_profit=potential_profit,
                margin=margin,
            ) 

    @staticmethod
    def get_inventory_valuation_data(
        profile, 
        request_user,
        stores_reg_nos, 
        date):
        """
        Returns inventory valuation data for a specific date or for today
        
        Args:   
            profile (Profile): The user's profile
            request_user (User): The user making the request
            stores_reg_nos (list): A list of store reg_nos
            date (str): The date after which to get the inventory valuation data
        """

        # Turn today's date into a string (2023-01-29)
        today = timezone.now().strftime("%Y-%m-%d")

        if date == today:
            # Get inventory valuation data for today
            return InventoryValuation.get_inventory_valuation_data_for_today(
                profile, 
                request_user,
                stores_reg_nos
            )   

        else:
            # Get inventory valuation data for a specific date
            return InventoryValuation.get_inventory_valuation_data_history(
                profile, 
                stores_reg_nos,
                date
            )
        
    @staticmethod
    def get_inventory_valuation_data_for_today(
        profile,
        request_user, 
        stores_reg_nos):

        inventory_data = profile.get_inventory_valuation(stores_reg_nos)

        total_inventory_data = {
            'total_inventory_value': inventory_data['inventory_value'],
            'total_retail_value': inventory_data['retail_value'],
            'total_potential_profit': inventory_data['potential_profit'],
            'margin': inventory_data['margin'],
        }

        filter_data = {}
        if request_user.user_type == TOP_USER:
            filter_data['profile__user'] = request_user
        else:
            filter_data['profile__employeeprofile__user'] = request_user

        queryset = Product.objects.filter(**filter_data).order_by('name')
        
        # Use distinct to prevent unwanted dupblicates when using many to many
        queryset = queryset.distinct()

        product_data = []
        for product in queryset:
            data = product.get_inventory_valuation(stores_reg_nos)
            data.pop('variants')
            product_data.append(data)

        return {
            'total_inventory_data': total_inventory_data,
            'product_data': list(product_data)
        }

    @staticmethod
    def get_inventory_valuation_data_history(
        profile, 
        stores_reg_nos, 
        date_after):

        filter_data = {'store__profile': profile}

        if stores_reg_nos:
            filter_data['store__reg_no__in'] = stores_reg_nos

        queryset = InventoryValuationLine.objects.filter(
            **filter_data
        )

        # Filter dates if they have been provided
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name='inventory_valution__created_date',
            date_after=date_after,
            date_before=date_after,
            local_timezone=profile.user.get_user_timezone()
        ) 
        
        # Get inventory line total inventory value, total retail value, 
        # total potential profit per product using Django annotate and Trunc
        product_agg_data = queryset.filter().values(
            'product__name',
            'cost',
        ).order_by('product__name').annotate(
            inventory_value=models.Sum("inventory_value"),
            retail_value=models.Sum("retail_value"),
            potential_profit=models.Sum("potential_profit"),
            units=models.Sum("units"),
        )

        total_inventory_data = {
            'total_inventory_value': 0,
            'total_retail_value': 0,
            'total_potential_profit': 0,
            'margin': 0,
        }
        
        product_data = []
        for data in product_agg_data:

            margin = 0
            try:
                potential_profit = data['potential_profit']
                retail_value = data['retail_value']

                margin = (potential_profit * 100) / retail_value
                margin = NumberHelpers.normal_round(margin, 2)
            except: # pylint: disable=bare-except
                pass

            cost = NumberHelpers.normal_round(data['cost'], 2)
            in_stock = NumberHelpers.normal_round(data['units'], 2)
            margin = NumberHelpers.normal_round(margin, 2)
            inventory_value = NumberHelpers.normal_round(data['inventory_value'], 2)
            retail_value = NumberHelpers.normal_round(data['retail_value'], 2)
            potential_profit = NumberHelpers.normal_round(data['potential_profit'], 2)

            product_data.append(
                {
                    'name': data['product__name'],
                    'cost': str(cost),
                    'in_stock': str(in_stock),
                    'margin': str(margin),
                    'inventory_value': str(inventory_value),
                    'retail_value': str(retail_value),
                    'potential_profit': str(potential_profit),
                }
            )

            total_inventory_data['total_inventory_value'] += data['inventory_value']
            total_inventory_data['total_retail_value'] += data['retail_value']
            total_inventory_data['total_potential_profit'] += data['potential_profit']

        try:
            potential_profit = total_inventory_data['total_potential_profit']
            retail_value = total_inventory_data['total_retail_value']
            margin = NumberHelpers.normal_round((potential_profit * 100) / retail_value, 2)

            total_inventory_data['margin'] = margin

        except: # pylint: disable=bare-except
            pass

        # Round off values in total_inventory_data and change them to strings
        for key in total_inventory_data:
            total_inventory_data[key] = str(NumberHelpers.normal_round(total_inventory_data[key], 2))

        return {
            'total_inventory_data': total_inventory_data,
            'product_data': list(product_data)
        }
    
    @staticmethod
    def get_inventory_product_data(profile, date, long_report=True):

        # Turn today's date into a string (2023-01-29)
        today = timezone.now().strftime("%Y-%m-%d")

        if date == today:
            # Get inventory valuation data for today
            return InventoryValuation.get_inventory_product_data_for_today(
                profile=profile,
                long_report=long_report
            )

        else:
            # Get inventory valuation data for a specific date
            return InventoryValuation.get_inventory_product_data_history(
                profile=profile, 
                date_after=date,
                long_report=long_report
            )
    
    @staticmethod
    def get_inventory_product_data_for_today(profile, long_report):

        filter_data = {'store__profile': profile}

        queryset = StockLevel.objects.filter(
            **filter_data
        )

        # Get all inventory valuations stores
        stores = queryset.values_list('store__name', flat=True).distinct(           
        ).order_by('store__name')

        values_filters = None
        if long_report:
            values_filters = {
                'product__name',
                'store__name',
                'price',
                'product__cost',
                'units',
                'is_sellable',
                'product__barcode',
                'product__sku',
                'product__category__name',
            }

        else:
            values_filters = {
                'product__name',
                'store__name',
                'units',
            }

        data = queryset.filter(
        ).values(
            *values_filters
        ).order_by('store__name')

        # Get total units per product
        product_units_agg_data = queryset.filter().values(
            'product__name',
        ).order_by('product__name').annotate(
            units=models.Sum("units"),
        )

        # Convert the product_agg_data to a dictionary
        product_units_agg_data = {
            data['product__name']: str(data['units']) for data in product_units_agg_data
        }

        product_data = defaultdict(list)

        # Iterate through the existing data and organize it by product name
        for entry in data:
            product_name = entry['product__name']

            if long_report:
                store_info = {
                    'price': str(entry['price']), 
                    'cost': str(entry['product__cost']),
                    'units': str(entry['units']),
                    'is_sellable': entry['is_sellable'],
                    'barcode': entry['product__barcode'],
                    'sku': entry['product__sku'],
                    'category_name': entry['product__category__name'],
                }

            else:
                store_info = {
                    'units': str(entry['units']),
                }

            product_data[product_name].append(store_info)

        # Convert defaultdict to a regular dictionary
        product_data = dict(product_data)

        sorted_product_data = dict(sorted(product_data.items(), key=lambda x: x[0]))

        return {
            'stores': list(stores),
            'product_data': sorted_product_data,
            'product_units_agg_data': product_units_agg_data
        }
        
    
    @staticmethod
    def get_inventory_product_data_history(
        profile,
        date_after,
        long_report
        ):

        """
        Returns inventory valuation data for a specific date or for today
        
        Args:   
            profile (Profile): The user's profile
            stores_reg_nos (list): A list of store reg_nos
            date (str): The date after which to get the inventory valuation data
        """

        filter_data = {'store__profile': profile}

        queryset = InventoryValuationLine.objects.filter(
            **filter_data
        )

        # Filter dates if they have been provided
        queryset = QuerysetFilterHelpers.range_date_filter(
            queryset=queryset,
            field_name='inventory_valution__created_date',
            date_after=date_after,
            date_before=date_after,
            local_timezone=profile.user.get_user_timezone()
        ) 

        # Get all inventory valuations stores
        stores = queryset.values_list('store__name', flat=True).distinct(           
        ).order_by('store__name')

        values_filters = None
        if long_report:
            values_filters = {
                'product__name',
                'store__name',
                'price',
                'cost',
                'units',
                'is_sellable',
                'barcode',
                'sku',
                'category_name',
                'inventory_valution__created_date',
                'inventory_valution__reg_no'
            }

        else:
            values_filters = {
                'product__name',
                'store__name',
                'units',
            }
     
        data = queryset.filter(
        ).values(
            *values_filters
        ).order_by('store__name')

        # Get total units per product
        product_units_agg_data = queryset.filter().values(
            'product__name',
        ).order_by('product__name').annotate(
            units=models.Sum("units"),
        )

        # Convert the product_agg_data to a dictionary
        product_units_agg_data = {
            data['product__name']: str(data['units']) for data in product_units_agg_data
        }

        product_data = defaultdict(list)

        # Iterate through the existing data and organize it by product name
        for entry in data:
            product_name = entry['product__name']

            if long_report:
                store_info = {
                    'price': str(entry['price']), 
                    'cost': str(entry['cost']),
                    'units': str(entry['units']),
                    'is_sellable': entry['is_sellable'],
                    'barcode': entry['barcode'],
                    'sku': entry['sku'],
                    'category_name': entry['category_name']
                }

            else:
                store_info = {
                    'units': str(entry['units']),
                }
            
            product_data[product_name].append(store_info)

        # Convert defaultdict to a regular dictionary
        product_data = dict(product_data)

        sorted_product_data = dict(sorted(product_data.items(), key=lambda x: x[0]))

        return {
            'stores': list(stores),
            'product_data': sorted_product_data,
            'product_units_agg_data': product_units_agg_data
        }

    def save(self, *args, **kwargs):

        """ If reg_no is 0 get a unique reg_no """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = self.__class__

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(InventoryValuation, self).save(*args, **kwargs)

class InventoryValuationLine(models.Model):
    inventory_valution = models.ForeignKey(InventoryValuation, on_delete=models.CASCADE)
    store  = models.ForeignKey(Store, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(
        verbose_name="price", max_digits=30, decimal_places=2, default=0.00
    )
    cost = models.DecimalField(
        verbose_name="cost", max_digits=30, decimal_places=2, default=0.00
    )
    units = models.DecimalField(
        verbose_name="units", max_digits=30, decimal_places=2, default=0.00
    )
    barcode = models.CharField(
        verbose_name='barcode',
        max_length=50,
        blank=True,
        default=''
    )
    sku = models.CharField(
        verbose_name='sku',
        max_length=50,
        blank=True,
        default=''
    )
    category_name = models.CharField(
        verbose_name='category name',
        max_length=50,
        blank=True,
        default=''
    )
    is_sellable = models.BooleanField(
        verbose_name='is sellable',
        default=True
    )
    inventory_value = models.DecimalField(
        verbose_name="inventory value", max_digits=30, decimal_places=2, default=0.00
    )
    retail_value = models.DecimalField(
        verbose_name="retail value", max_digits=30, decimal_places=2, default=0.00
    )
    potential_profit = models.DecimalField(
        verbose_name="potential profit", max_digits=30, decimal_places=2, default=0.00
    )
    margin = models.DecimalField(
        verbose_name="margin", max_digits=30, decimal_places=2, default=0.00
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )
    tax = models.ForeignKey(
        Tax, on_delete=models.CASCADE, null=True, blank=True
    )
    created_date = models.DateTimeField(
        verbose_name="created date", 
        default=timezone.now, 
        db_index=True
    )

    # Fields to be used for faster filtering
    store_reg_no = models.BigIntegerField(
        verbose_name="store reg no",
        default=0,
        editable=False,
    )
    product_reg_no = models.BigIntegerField(
        verbose_name="product reg no",
        default=0,
        editable=False,
    )
    is_recaclulated = models.BooleanField(
        verbose_name='is recaclulated',
        default=False
    )
    
    def __str__(self):
        return self.product.name
    
    @staticmethod
    def calculate_inventory_valuation_line_value(units, cost, price):

        inventory_value = units * cost
        retail_value = units * price
        potential_profit = retail_value - inventory_value

        margin = 0
        try:
            margin = (potential_profit * 100) / retail_value
        except: # pylint: disable=bare-except
            pass
        
        return inventory_value, retail_value, potential_profit, margin
    
    def recalculate_inventory_valuation_line(self):

        inventory_value, retail_value, potential_profit, margin = InventoryValuationLine.calculate_inventory_valuation_line_value(
            units=self.units, 
            cost=self.cost,
            price=self.price
        )
        
        self.inventory_value = inventory_value
        self.retail_value = retail_value
        self.potential_profit = potential_profit
        self.margin = margin
        self.is_recaclulated = True

        print(f"Recalculated InventoryValuationLine {self.product.name}")
        print(f'inventory_value: {inventory_value}')
        print(f'retail_value: {retail_value}')
        print(f'potential_profit: {potential_profit}')
        print(f'margin: {margin}')
        self.save()

    def save(self, *args, **kwargs):

        self.store = self.inventory_valution.store
        self.store_reg_no = self.store.reg_no

        self.product_reg_no = self.product.reg_no
    
        # Call the "real" save() method.
        super(InventoryValuationLine, self).save(*args, **kwargs)

        