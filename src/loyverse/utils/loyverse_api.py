from decimal import Decimal
from pprint import pprint
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import UserGroup

from core.logger_manager import LoggerManager
from inventories.models import StockLevel # pylint: disable=no-name-in-module
from accounts.utils.user_type import EMPLOYEE_USER

from loyverse.models import LoyverseAppData
from loyverse.utils.loyverse_helpers import StoreHelpers
from products.models import Product, ProductBundle
from profiles.models import Customer, EmployeeProfile
from sales.models import Receipt
from stores.models import Category, Store, Tax


class LoyverseDataOrm:

    @staticmethod
    def save_oauth_data(access_token, refresh_token, expires_in):

        try:
            loyverse_auth = LoyverseAppData.objects.get(name='main')

            loyverse_auth.access_token = access_token
            loyverse_auth.refresh_token = refresh_token
            loyverse_auth.access_token_expires_in = expires_in
            loyverse_auth.save()

            return True
            
        except: # pylint: disable=bare-except
            LoggerManager.log_critical_error()

        return False

    @staticmethod
    def retrive_oauth_data():
  
        data = {}

        try:
            loyverse_auth = LoyverseAppData.objects.get(name='main')

            data['access_token'] = loyverse_auth.access_token
            data['refresh_token'] = loyverse_auth.refresh_token
            data['expires_in'] = loyverse_auth.access_token_expires_in

        except: # pylint: disable=bare-except
            LoggerManager.log_critical_error()

        return {
            'access_token': data.get('access_token', None), 
            'refresh_token': data.get('refresh_token', None), 
            'expires_in': data.get('expires_in', None)
        }
    

class LoyverseUnpack:

    @staticmethod
    def unpack_items_json(items):
        """
        Returns a list of items with only the requied data.

        For example:

            [
                {
                    'id': 'ea0771ba-4d01-4f14-8d35-210e882cc823',
                    'name': 'Splash',
                    'sku': '10012',
                    'stores': [
                        {
                            'available_for_sale': True,
                            'low_stock': 0,
                            'optimal_stock': None,
                            'price': 300.0,
                            'pricing_type': 'FIXED',
                            'store_id': '82158310-3276-4962-8210-2ca88d7e7f13'
                        },
                        {
                            'available_for_sale': True,
                            'low_stock': None,
                            'optimal_stock': None,
                            'price': 300.0,
                            'pricing_type': 'FIXED',
                            'store_id': 'eca0890b-cbd9-4172-9b34-703ef2f84705'
                        }
                    ],
                    'variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'
                },
                ...
            ]

        """

        # Unpack items
        unpacked_items = []
        for item in items['items']:
            # if not item['is_composite'] and (item['option1_name'] == None):
            unpacked_items.append(
                {
                    'id': item['id'], 
                    'variant_id': item['variants'][0]['variant_id'], 
                    'sku': item['variants'][0]['sku'], 
                    'barcode': item['variants'][0]['barcode'], 
                    'cost': item['variants'][0]['cost'], 
                    'name': item['item_name'],
                    'tax_id': item['tax_ids'][0] if item['tax_ids'] else '',
                    'category_id': item['category_id'],
                    'is_composite': item['is_composite'],
                    'is_variant': item['option1_name'] != None,
                    'stores': item['variants'][0]['stores'],
                    'components': item['components']
                }
            )

        return unpacked_items

    @staticmethod
    def unpack_stores_json(stores):

        # Unpack stores
        unpacked_stores = []
        for item in stores['stores']:
            unpacked_stores.append(
                {
                    'loyverse_store_id': item['id'], 
                    'name': item['name']
                }
            )

        return unpacked_stores

    @staticmethod
    def unpack_customers_json(customers):

        if not customers: return []

        # Unpack customers
        unpacked_data = []
        for customer in customers['customers']:
            unpacked_data.append(
                {
                    'name': customer['name'],
                    'email': customer['email'],
                    'phone': customer['phone_number'],
                    'customer_code': customer['customer_code'],
                    'customer_id': customer['id'], 
                }
            )

        return unpacked_data
    
    @staticmethod
    def unpack_taxes_json(taxes):

        if not taxes: return []

        # Unpack customers
        unpacked_data = []
        for tax in taxes['taxes']:
            unpacked_data.append(
                {
                    'name': tax['name'],
                    'id': tax['id'],
                    'rate': tax['rate'],
                }
            )

        return unpacked_data
    
    @staticmethod
    def unpack_categories_json(categories):

        if not categories: return []

        # Unpack customers
        unpacked_data = []
        for category in categories['categories']:
            unpacked_data.append(
                {
                    'name': category['name'],
                    'id': category['id'],
                }
            )

        return unpacked_data

    @staticmethod
    def unpack_employees_json(employees):

        if not employees: return []

        # Unpack employees
        unpacked_data = []
        for employee in employees['employees']:
            unpacked_data.append(
                {
                    'name': employee['name'],
                    'email': employee['email'],
                    'phone': employee['phone_number'],
                    'employee_id': employee['id'], 
                    'store_id': employee['stores'][0] if employee['stores'] else '',
                    'stores': employee['stores']
                }
            )
            
        return unpacked_data

    @staticmethod
    def unpack_inventory_levels_json(levels):

        # Unpack levels
        unpacked_levels = []
        for item in levels['inventory_levels']:

            unpacked_levels.append(
                {
                    'variant_id': item['variant_id'],
                    'store_id': item['store_id'],
                    'in_stock': item['in_stock']
                }
            )

        return unpacked_levels


class LoyverseApi:

    @staticmethod
    def get_paginated_data(url, response_key, access_token=None):

        if not access_token:
            access_token = LoyverseDataOrm.retrive_oauth_data()['access_token']
        
        response_json = {response_key: []}

        print(f'Url {url}')


        # Return empty when we are testing
        if settings.TESTING_MODE:
            return response_json

        if access_token:

            reqs = 0

            my_headers = {'Authorization' : f'Bearer {access_token}'}
            response = requests.get(
                url=url, 
                headers=my_headers,
                timeout=settings.PYTHON_REQUESTS_TIMEOUT
            )

            reqs +=1

            if response.status_code == 200:

                response_json[response_key].extend(response.json()[response_key])
                cursor =  response.json().get('cursor', None)

                while cursor:
                    cursored_url = f'{url}&cursor={cursor}'
                    response = requests.get(
                        url=cursored_url, 
                        headers=my_headers,
                        timeout=settings.PYTHON_REQUESTS_TIMEOUT
                    )
                    reqs +=1

                    if response.status_code == 200:
                        response_json[response_key].extend(
                            response.json()[response_key]
                        )
                        cursor =  response.json().get('cursor', None)

                    else:
                        cursor = None

                        LoggerManager.log_critical_error(
                            additional_message=f'LoyverseApi - get_paginated_data() 1 Response code was {response.status_code}'
                        )

            else:

                print(response)

                LoggerManager.log_critical_error(
                            additional_message=f'LoyverseApi - get_paginated_data() 2 Response code was {response.status_code}'
                        )

        else:
            LoggerManager.log_page_critical_error_depreciated(
                origin='LoyverseApi - get_paginated_data() 3',
                message='Access token has not been found'
            )

        return response_json

    @staticmethod
    def get_loyverse_headers():
        access_token = access_token = LoyverseDataOrm.retrive_oauth_data()['access_token']
        return {'Authorization' : f'Bearer {access_token}'}
    
    @staticmethod
    def get_items():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_ITEMS_URL, 
            response_key="items"
        )
    
    @staticmethod
    def get_employees():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_EMPLOYEE_URL, 
            response_key="employees"
        )

    @staticmethod
    def get_stores():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_STORES_URL, 
            response_key="stores"
        )

    @staticmethod
    def get_taxes():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_TAXES_URL, 
            response_key="taxes"
        )

    @staticmethod
    def get_categoreis():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_CATEGORIES_URL, 
            response_key="categories"
        )

    @staticmethod
    def get_customers():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_CUSTOMER_URL, 
            response_key="customers"
        )
    
    @staticmethod
    def get_inventory_levels():
        return LoyverseApi.get_paginated_data(
            url=settings.LOYVERSE_INVENTORY_URL, 
            response_key="inventory_levels"
        )

    @staticmethod
    def get_receipts():
        """
        Returns all loyverse receipts that were created yestarday
        """
        date_for_analysis = LoyverseAppData.objects.get().receipt_anlayze_iso_date()

        return LoyverseApi.get_paginated_data(
            url=f'{settings.LOYVERSE_RECEIPTS_URL}&created_at_min={date_for_analysis}', 
            response_key="receipts"
        )
    
    @staticmethod
    def get_inventory(profile):
        stores = LoyverseApi.get_stores()
        employees = LoyverseApi.get_employees()
        taxes = LoyverseApi.get_taxes()
        categories = LoyverseApi.get_categoreis()
        customers = LoyverseApi.get_customers()
        items = LoyverseApi.get_items()
        levels = LoyverseApi.get_inventory_levels()

        return LoyverseSyncData(
            profile=profile,
            stores=stores,
            employees=employees,
            taxes=taxes,
            categories=categories,
            customers=customers,
            items=items,
            levels=levels
        ).sync_data()

    @staticmethod
    def sync_employees(profile):
        employees = LoyverseApi.get_employees()

        LoyverseSyncData(profile=profile, employees=employees).sync_data()

    @staticmethod
    def sync_stock_levels(profile):
        levels = LoyverseApi.get_inventory_levels()

        LoyverseSyncData(profile=profile, levels=levels).sync_data()

    @staticmethod
    def sync_items(profile):
        items = LoyverseApi.get_items()
        
        LoyverseSyncData(profile=profile, items=items).sync_data()

    @staticmethod
    def sync_stores(profile):
        stores = LoyverseApi.get_stores()
        LoyverseSyncData(profile=profile, stores=stores).sync_data()

    @staticmethod
    def sync_customers(profile):
        customers = LoyverseApi.get_customers()
        LoyverseSyncData(profile=profile, customers=customers).sync_data()


    

class LoyverseSyncData:

    def __init__(
            self, 
            profile, 
            stores=None, 
            employees=None,
            taxes=None, 
            categories=None, 
            customers=None, 
            items=None,
            levels=None) -> None:
        
        # Unpack json dsata
        self.profile = profile
        self.stores = LoyverseUnpack.unpack_stores_json(stores) if stores else []
        self.employees = LoyverseUnpack.unpack_employees_json(employees) if employees else []
        self.taxes = LoyverseUnpack.unpack_taxes_json(taxes) if taxes else []
        self.categories = LoyverseUnpack.unpack_categories_json(categories) if categories else []
        self.customers = LoyverseUnpack.unpack_customers_json(customers) if customers else []
        self.items = LoyverseUnpack.unpack_items_json(items) if items else []
        self.levels = LoyverseUnpack.unpack_inventory_levels_json(levels) if levels else []

    def sync_data(self):

        self.create_customers()
        self.create_stores()
        self.create_employees()
        self.create_taxes()
        self.create_categories()
        self.create_products()
        self.create_stock_level()
        self.attach_tax_and_categories_to_product()

        return True
    
    def create_stock_level(self): 
        """
        Updates only stock levels that don't match with loyverse 
        """
        
        def get_unique_id(id1, id2):
            return f"{str(id1)}={str(id2)}"

        new_level_dict = {
            get_unique_id(s['variant_id'], s['store_id']): {
                'variant_id': s['variant_id'],
                'store_id': s['store_id'],
                'in_stock': s['in_stock'],
            }
            for s in self.levels
        }

        local_level_list = list(StockLevel.objects.filter(store__profile=self.profile).order_by('id').values(
            'product__loyverse_variant_id',
            'store__loyverse_store_id',
            'units' 
        ))

        local_level_dict = {
            get_unique_id(s['product__loyverse_variant_id'], s['store__loyverse_store_id']): {
                'variant_id': s['product__loyverse_variant_id'],
                'store_id': s['store__loyverse_store_id'],
                'in_stock': s['units'],
            }
            for s in local_level_list
        }

        stock_level_updated = False
        for key, value in new_level_dict.items():

            if key in local_level_dict:
                
                stock_level_updated = True

                pos_local_stock = round(Decimal(value["in_stock"]), 2)
                local_in_stock = round(Decimal(local_level_dict[key]["in_stock"]), 2)

                if pos_local_stock != local_in_stock: 

                    stock_levels = StockLevel.objects.filter(
                        store__profile=self.profile,
                        store__loyverse_store_id = value['store_id'],
                        product__loyverse_variant_id = value['variant_id']
                    )

                    if stock_levels:
                        stock_level = stock_levels[0]

                        stock_level.units = value['in_stock']
                        stock_level.save()

        # Only update the product average prices if we have updated the stock levels
        if stock_level_updated: self.update_product_average_prices()

        return True
    
    def update_product_average_prices(self):
    
        products = Product.objects.filter(profile=self.profile)

        for product in products: product.update_product_average_price()

    def create_employees(self):
        """
        Creates tax if they don't exist
        """

        def update_stores_for_employees(employee_profile, stores_loyverse_ids):

            stores = Store.objects.filter(
                profile=self.profile,
                loyverse_store_id__in=stores_loyverse_ids
            )

            employee_profile.stores.add(*stores)

        
        self.stores_map = self.__get_stores_map()

        new_employees_dict = {}
        for employee in self.employees:
            name=employee['name']
            email=employee['email']
            phone=employee['phone']
            employee_id=employee['employee_id']
            store_id=employee['store_id']
            loyverse_store_ids = employee['stores']

            if not email:
                email = f"{name.lower().replace(' ', '_')}@mwingi.africa"

            new_employees_dict[str(employee_id)] = {
                'name': name,
                'email': email,
                'phone': phone,
                'employee_id': employee_id,
                'store_id': store_id,
                'loyverse_store_ids': loyverse_store_ids,

            }

        local_employees_list = list(get_user_model().objects.all().values(
            'loyverse_employee_id', 
            'first_name'
        ))

        local_employees_dict = {str(s['loyverse_employee_id']): s['first_name'] for s in local_employees_list}

        for key, employee in new_employees_dict.items():
            name=employee['name']
            email=employee['email']
            phone=employee['phone'] if employee['phone'] else 0
            employee_id=employee['employee_id']
            store_id=employee['store_id']
            loyverse_store_ids = employee['loyverse_store_ids']

            if not key in local_employees_dict: 
                
                try:

                    user_parms = {
                        'first_name': name,
                        'last_name': '',
                        'email': email,
                        'phone': phone,
                        'user_type': EMPLOYEE_USER,
                        'loyverse_employee_id': employee_id,
                        'gender':0, 
                        'password': '12345678'
                    }

                    if store_id:
                        user_parms['loyverse_store_id'] = store_id

                    user = get_user_model().objects.create_user(**user_parms)

                    role_reg_no = UserGroup.objects.get(
                        master_user__profile=self.profile,
                        ident_name='Cashier'
                        ).reg_no
                    
                    employee_data = {
                        'user': user,
                        'profile': self.profile,
                        'phone': phone,
                        'reg_no': user.reg_no,
                        'role_reg_no': role_reg_no,
                        'loyverse_employee_id': employee_id,
                    }

                    if store_id:
                        employee_data['loyverse_store_id'] = store_id

                    employee_profile = EmployeeProfile.objects.create(**employee_data)

                    update_stores_for_employees(
                        employee_profile=employee_profile,
                        stores_loyverse_ids=loyverse_store_ids
                    )

                except: # pylint: disable=bare-except
                    print(f"Error {email}")
                    LoggerManager.log_critical_error()

            else:
                # Update user data
                user_data = {
                    'first_name': name,
                    'loyverse_employee_id': employee_id,
                }

                if store_id:
                    user_data['loyverse_store_id'] = store_id

                get_user_model().objects.filter(
                    email=email
                ).update(**user_data)

                # Update employee data
                employee_data = {
                    'loyverse_employee_id': employee_id,
                }

                if store_id:
                    employee_data['loyverse_store_id'] = store_id


                employee_profiles = EmployeeProfile.objects.filter(
                    user__email=email
                )

                if employee_profiles:

                    employee_profile = employee_profiles[0]

                    employee_profiles.update(**employee_data)

                    update_stores_for_employees(
                        employee_profile=employee_profile,
                        stores_loyverse_ids=loyverse_store_ids
                    )


    def create_customers(self):
        """
        Creates customer if they don't exist
        """
        new_customers_dict = {
            str(s['customer_id']): {
                    'name': s['name'],
                    'email': s['email'],
                    'phone': s['phone'],
                    'customer_code': s['customer_code']
                } for s in self.customers}

        local_customers_list = list(Customer.objects.filter(profile=self.profile).values(
            'loyverse_customer_id', 
            'name'
        ))

        local_customers_dict = {str(s['loyverse_customer_id']): s['name'] for s in local_customers_list}

        for key, value in new_customers_dict.items():

            if not key in local_customers_dict:

                try:

                    Customer.objects.create(
                        profile=self.profile,
                        name=value['name'],
                        email=value['email'],
                        phone=value['phone'],
                        customer_code=value['customer_code'],
                        loyverse_customer_id=key
                    )

                except: # pylint: disable=bare-except
                    LoggerManager.log_critical_error()

    def create_stores(self):
        """
        Syncs loyverse stores with local stores. Creates a new store if it's in 
        loyverse and it's not in our server
        """
        new_stores_dict = {str(s['loyverse_store_id']): s['name'] for s in self.stores}

        local_stores_list = list(Store.objects.filter(profile=self.profile).order_by('id').values(
            'loyverse_store_id', 
            'name'
        ))

        local_stores_dict = {str(s['loyverse_store_id']): s['name'] for s in local_stores_list}

        for key, value in new_stores_dict.items():
            if not key in local_stores_dict:
                Store.objects.create(
                    profile=self.profile,
                    name = value,
                    loyverse_store_id = key,
                )
            else:
                Store.objects.filter(loyverse_store_id=key).update(name=value)

    def create_taxes(self):
        """
        Creates tax if they don't exist
        """
        new_taxes_dict = {
            str(s['id']): {
                    'name': f"{s['name']} - {s['rate']}",
                    'rate': s['rate'],
                    'loyverse_tax_id': s['id'],
                } for s in self.taxes}

        local_taxes_list = list(Tax.objects.filter(profile=self.profile).values(
            'loyverse_tax_id', 
            'rate',
            'name'
        ))

        local_taxes_dict = {str(s['loyverse_tax_id']): {'name': s['name'], 'rate': s['rate']} for s in local_taxes_list}

        for key, value in new_taxes_dict.items():

            tax_name = value['name']
            tax_rate = value['rate']
            loyverse_tax_id = value['loyverse_tax_id']

            if not key in local_taxes_dict:
                
                try:
                    Tax.objects.create(
                        profile=self.profile,
                        name=tax_name,
                        rate=tax_rate,
                        loyverse_tax_id=loyverse_tax_id
                    )

                except: # pylint: disable=bare-except
                    LoggerManager.log_critical_error()

            else:

                if local_taxes_dict[key]['name'] != tax_name:
                    Tax.objects.filter(
                        profile=self.profile,
                        loyverse_tax_id=key
                    ).update(name=tax_name, rate=tax_rate)

    def create_categories(self):
        """
        Creates categories if they don't exist
        """
        new_categories_dict = {
            str(s['id']): {
                    'name': f"{s['name']}",
                    'loyverse_category_id': s['id'],
                } for s in self.categories}

        local_categories_list = list(Category.objects.filter(profile=self.profile).values(
            'loyverse_category_id', 
            'name'
        ))

        local_categories_dict = {str(s['loyverse_category_id']): {'name': s['name']} for s in local_categories_list}

        for key, value in new_categories_dict.items():
            
            category_name = value['name']
            loyverse_category_id = value['loyverse_category_id']

            if not key in local_categories_dict:
                
                try:
                    Category.objects.create(
                        profile=self.profile,
                        name=category_name,
                        loyverse_category_id=loyverse_category_id
                    )

                except: # pylint: disable=bare-except
                    LoggerManager.log_critical_error()

            else:

                if local_categories_dict[key]['name'] != category_name:
                    Category.objects.filter(
                        profile=self.profile, 
                        loyverse_category_id=key
                    ).update(
                        name=category_name
                    )

    def create_products(self):

        non_composite_items = []
        composite_items = []

        for item in self.items:
            if item['is_composite']:
                composite_items.append(item)
            else:
                non_composite_items.append(item)

        self.create_products_and_stock_levels(non_composite_items)
        self.create_products_and_stock_levels(composite_items)

    def create_products_and_stock_levels(self, items):

        new_products_dict = {
            str(s['variant_id']): {
                'name': s['name'],
                'sku': s['sku'],
                'barcode': s['barcode'],
                'cost': s['cost'],
                'price': s['stores'][0]['price'],
                'id': s['id'],
                'variant_id': s['variant_id'],
                'is_composite': s['is_composite'],
                'is_variant': s['is_variant'],
                'tax_id': s['tax_id'],
                'category_id': s['category_id'],
                'stores': s['stores'],
                'components': s['components'],
                'stores_map': [s['store_id'] for s in s['stores']],
            }
            for s in items
        }

        local_products_list = Product.objects.filter(profile=self.profile).order_by('id').values(
            'name',
            'sku',
            'barcode',
            'id',
            'loyverse_variant_id',
        )

        local_products_dict = {
            str(s['loyverse_variant_id']): {
                'stores': []
            }
            for s in local_products_list
        }

        stock_levels = list(StockLevel.objects.filter(product__profile=self.profile).order_by('id').values(
            'product__loyverse_variant_id', 
            'store__loyverse_store_id'
        ))

        for stock in stock_levels:
            variant_id = str(stock['product__loyverse_variant_id'])

            if str(stock['product__loyverse_variant_id']) in local_products_dict:
                local_products_dict[variant_id]['stores'].append(str(stock['store__loyverse_store_id']))

        for key, value in new_products_dict.items():

            is_composite = True if value['is_composite'] else False 

            if key in local_products_dict:
                
                store_list1 = value['stores_map']
                store_list2 = local_products_dict[key]['stores']

                store_list1.sort()
                store_list2.sort()

                products = Product.objects.filter(
                    profile=self.profile,
                    loyverse_variant_id = value['variant_id']
                )

                if products:
                    product = products[0]

                    product.name = value['name'] # *
                    # product.is_composite=value['is_composite']
                    # product.is_variant=value['is_variant']
                    # product.tax_id=value['tax_id']
                    product.barcode=value['barcode'] # *
                    # product.cost=value['cost'] # *
                    product.price=value['price']
                    product.save() # *

                    collected_store_ids = StoreHelpers.get_store_local_ids(value['stores'])

                    # Adds or removes stores from the passed model
                    StoreHelpers.add_or_remove_stores(product, collected_store_ids)

                    if is_composite:
                        try:
                            self.create_bundles(product, value['components'])
                        except Exception as e:
                            print(e)

                elif is_composite:
                    print("Calling 2")

                    products = Product.objects.filter(
                        profile=self.profile,
                        loyverse_variant_id=value['variant_id']
                    )

                    product = products[0]
                    try:
                        self.create_bundles(product, value['components'])
                    except Exception as e:
                        print(e)
            
            else:
                pass

                product = Product.objects.create(
                    profile=self.profile,
                    name=value['name'],
                    sku=value['sku'],
                    barcode=value['barcode'],
                    cost=value['cost'],
                    price=value['price'],
                    loyverse_variant_id=value['variant_id'],
                )

                collected_store_ids = StoreHelpers.get_store_local_ids_and_sellable_data(value['stores'])

                #Adds or removes stores from the passed model
                StoreHelpers.add_or_remove_stores(product, collected_store_ids)

                if is_composite:
                    try:
                        self.create_bundles(product, value['components'])
                    except Exception as e:
                        print(e)

        # self.update_product_prices()

    def create_bundles(self, master_product, compontents):
        """
        Args:
            master_product (Product): The master product model that will have bundles
            components (list): A list of dics that has quantity and variant id
            for the bundles. 
            
            Example of components:
            [
                {'quantity': 10, 'variant_id': '1ec7f40d-750a-449e-a53d-2e7bb8476a51'},
                {'quantity': 10, 'variant_id': '7dd713a0-d4d8-4fdd-932d-be06bca84f75'}
            ] 
        """
        # We first get the product data so that incase there is a problem, we will
        # know sooner. 
        # This makes sure that we only start creating a bundle after we have all
        # the required products
        bundles_data = []
        for component in compontents:
            product = Product.objects.get(
                profile=self.profile,
                loyverse_variant_id=component['variant_id']
            )

            bundles_data.append(
                {
                    'product_model': product,
                    'quantity': component['quantity']
                }
            )

        # To reduce db queries, we first create the bundles and then we will
        # insert them in the db once.
        product_bundles = []
        for bundle in bundles_data:

            # Don't create if we already have a similar bundle in the master 
            # product
            bundle_exists = master_product.bundles.filter(
                product_bundle=bundle['product_model']
            ).exists()

            if bundle_exists: continue

            bundle = ProductBundle.objects.create(
                product_bundle=bundle['product_model'],
                quantity=bundle['quantity']
            )

            product_bundles.append(bundle)

        master_product.bundles.add(*product_bundles)

    def attach_tax_and_categories_to_product(self):

        new_products_dict = {
            str(s['variant_id']): {
                'name': s['name'],
                'sku': s['sku'],
                'barcode': s['barcode'],
                'cost': s['cost'],
                'price': s['stores'][0]['price'],
                'id': s['id'],
                'variant_id': s['variant_id'],
                'is_composite': s['is_composite'],
                'is_variant': s['is_variant'],
                'tax_id': s['tax_id'],
                'category_id': s['category_id'],
                'stores': s['stores'],
                'components': s['components'],
                'stores_map': [s['store_id'] for s in s['stores']],
            }
            for s in self.items
        }

        local_products_list = Product.objects.filter(
            profile=self.profile
        ).order_by('id').values(
            'name',
            'sku',
            'barcode',
            'id',
            'loyverse_variant_id',
        )

        local_products_dict = {
            str(s['loyverse_variant_id']): {
                'stores': []
            }
            for s in local_products_list
        }

        stock_levels = list(StockLevel.objects.filter(product__profile=self.profile).order_by('id').values(
            'product__loyverse_variant_id', 
            'store__loyverse_store_id'
        ))

        for stock in stock_levels:
            variant_id = str(stock['product__loyverse_variant_id'])

            if str(stock['product__loyverse_variant_id']) in local_products_dict:
                local_products_dict[variant_id]['stores'].append(str(stock['store__loyverse_store_id']))

        for key, value in new_products_dict.items():

            products = Product.objects.filter(
                profile=self.profile, 
                loyverse_variant_id = value['variant_id']
            )

            if products:
                product = products[0]

                # Get tax
                tax = None
                if value['tax_id']:
                    taxes = Tax.objects.filter(
                        profile=self.profile, 
                        loyverse_tax_id=value['tax_id']
                    )
                    tax = taxes[0] if taxes else None

                # Get categories
                category = None
                if value['category_id']:
                    categories = Category.objects.filter(
                        profile=self.profile, 
                        loyverse_category_id=value['category_id']
                    )
                    category = categories[0] if categories else None

                # Save product
                product.tax = tax
                product.category = category
                product.save()

                # Call category save to update category
                if category:
                    category.save()


    def __get_stores_map(self):

        stores = Store.objects.filter(profile=self.profile).order_by('id')

        stores_map = {str(store.loyverse_store_id):store for store in stores}

        return stores_map



