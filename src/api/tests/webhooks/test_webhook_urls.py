import datetime
import uuid
import pytz

from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from core.test_utils.create_store_models import create_new_store, create_new_tax

from core.test_utils.create_user import (
    create_new_cashier_user, 
    create_new_customer, 
    create_new_manager_user, 
    create_new_user
)

from core.test_utils.custom_testcase import APITestCase

from inventories.models import StockLevel
from products.models import Product
from profiles.models import Customer, Profile
from mysettings.models import MySetting
from sales.models import Receipt, ReceiptLine


class TpLeanUserIndexViewTestCase(APITestCase):

    def setUp(self):

        # Create a user1
        self.user = create_new_user('angelina')

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        # Create employee user
        self.manager = create_new_manager_user(
            "gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user(
            "kate", self.profile, self.store1)
        
        self.create_products()
       
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save()

    def create_products(self):

        ####################### Create a product
        self.product1 = Product.objects.create(
            profile=self.profile,
            name="Sugar 1kg",
            price=750,
            cost=100,
            sku='sku1',
            barcode='code123',
            track_stock=True,
            loyverse_variant_id = uuid.uuid4()
        )

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product1)
        stock_level.units = 60
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product1)
        stock_level.units = 40
        stock_level.save()

        ####################### Create a produc2
        self.product2 = Product.objects.create(
            profile=self.profile,
            name="Sugar 2kg",
            price=750,
            cost=120,
            sku='sku1',
            barcode='code123',
            track_stock=True,
            loyverse_variant_id = uuid.uuid4()
        )

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product2)
        stock_level.units = 100
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product2)
        stock_level.units = 80
        stock_level.save()


        ####################### Create a product3
        self.product3 = Product.objects.create(
            profile=self.profile,
            name="MM Nafuu bale",
            price=750,
            cost=130,
            sku='sku1',
            barcode='code123',
            track_stock=True,
            loyverse_variant_id = uuid.uuid4()
        )

        # Product1
        stock_level = StockLevel.objects.get(store=self.store1, product=self.product3)
        stock_level.units = 150
        stock_level.save()

        # Product2
        stock_level = StockLevel.objects.get(store=self.store2, product=self.product3)
        stock_level.units = 110
        stock_level.save()

    def test_view_returns_the_user_empoyees_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(3):
            response = self.client.get(
                reverse('api:webhook_stock_levels'))
            self.assertEqual(response.status_code, 200)

        results = {
            'count': 6, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'units': '60.00', 
                    'loyverse_store_id': str(self.store1.loyverse_store_id), 
                    'loyverse_variant_id': str(self.product1.loyverse_variant_id)
                }, 
                {
                    'units': '40.00', 
                    'loyverse_store_id': str(self.store2.loyverse_store_id), 
                    'loyverse_variant_id': str(self.product1.loyverse_variant_id)
                }, 
                {
                    'units': '100.00', 
                    'loyverse_store_id': str(self.store1.loyverse_store_id), 
                    'loyverse_variant_id': str(self.product2.loyverse_variant_id)
                }, 
                {
                    'units': '80.00', 
                    'loyverse_store_id': str(self.store2.loyverse_store_id), 
                    'loyverse_variant_id': str(self.product2.loyverse_variant_id)
                }, 
                {
                    'units': '150.00', 
                    'loyverse_store_id': str(self.store1.loyverse_store_id), 
                    'loyverse_variant_id': str(self.product3.loyverse_variant_id)
                }, 
                {
                    'units': '110.00', 
                    'loyverse_store_id': str(self.store2.loyverse_store_id), 
                    'loyverse_variant_id': str(self.product3.loyverse_variant_id)
                }
            ]
        }

        self.assertEqual(results, response.data)

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_view_for_products_returns_the_right_content_with_pagination(self):

        # First delete all products
        Product.objects.all().delete()

        model_num_to_be_created = 200

        products = []
        for i in range(int(model_num_to_be_created/2)+1):

            product = Product.objects.create(
                profile=self.profile,
                name=f'Product{i}',
                price=10+i,
                cost=5+i,
                sku=f'sku{i}',
                barcode=f'code{i}',
                track_stock=True,
                loyverse_variant_id = uuid.uuid4()
            )

            products.append(product)

        self.assertEqual(StockLevel.objects.all().count(), model_num_to_be_created+2)  

        stock_levels = StockLevel.objects.all().order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(3):
            response = self.client.get(
                reverse('api:webhook_stock_levels'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created+2)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/webhook/stock-levels/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), settings.LEAN_PAGINATION_PAGE_SIZE)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all employee profiles are listed except the first one since it's in the next paginated page #
        i = 0
        for stock in stock_levels[2:]:

            self.assertEqual(
                response_data_dict['results'][i]['units'], str(stock.units))
            self.assertEqual(
                response_data_dict['results'][i]['loyverse_store_id'], str(stock.loyverse_store_id))
            self.assertEqual(
                response_data_dict['results'][i]['loyverse_variant_id'], str(stock.loyverse_variant_id))

            i += 1

        self.assertEqual(i, settings.LEAN_PAGINATION_PAGE_SIZE)  # Confirm the number the for loop ran

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(
            reverse('api:webhook_stock_levels') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created + 2,
            'next': None,
            'previous': 'http://testserver/api/webhook/stock-levels/',
            'results': [
                {
                    'units': '0.00', 
                    'loyverse_store_id': str(stock_levels[1].loyverse_store_id), 
                    'loyverse_variant_id': str(stock_levels[1].loyverse_variant_id)
                }, 
                {
                    'units': '0.00', 
                    'loyverse_store_id': str(stock_levels[0].loyverse_store_id), 
                    'loyverse_variant_id': str(stock_levels[0].loyverse_variant_id)
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_models(self):

        # First delete all stock levels
        StockLevel.objects.all().delete()

        response = self.client.get(
            reverse('api:webhook_stock_levels'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, result)

class ApiCustomerIndexViewTestCase(APITestCase):

    def setUp(self):
        # Create a user1
        self.user = create_new_user('angelina')

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        # Create employee user
        self.manager = create_new_manager_user(
            "gucci", self.profile, self.store1)
        self.cashier = create_new_cashier_user(
            "kate", self.profile, self.store1)
        
        # Create a customer users
        self.customer1 = create_new_customer(self.profile, 'chris')
        self.customer1.loyverse_customer_id = uuid.uuid4()
        self.customer1.save()

        self.customer2 = create_new_customer(self.profile, 'alex')
        self.customer2.loyverse_customer_id = uuid.uuid4()
        self.customer2.save()

        self.customer3 = create_new_customer(self.profile, 'dan')
        self.customer3.loyverse_customer_id = uuid.uuid4()
        self.customer3.save()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save() 

    def test_view_returns_the_user_customers_only(self):

        # Count Number of Queries #
        with self.assertNumQueries(3):
            response = self.client.get(reverse('api:webhook_customers'))
            self.assertEqual(response.status_code, 200)

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.customer1.name, 
                    'email': self.customer1.email,
                    'phone': self.customer1.phone,
                    'customer_code': self.customer1.customer_code,
                    'loyverse_customer_id': str(self.customer1.loyverse_customer_id)
                },
                {
                    'name': self.customer2.name, 
                    'email': self.customer2.email,
                    'phone': self.customer2.phone,
                    'customer_code': self.customer2.customer_code,
                    'loyverse_customer_id': str(self.customer2.loyverse_customer_id)
                },
                {
                    'name': self.customer3.name, 
                    'email': self.customer3.email,
                    'phone': self.customer3.phone,
                    'customer_code': self.customer3.customer_code,
                    'loyverse_customer_id': str(self.customer3.loyverse_customer_id)
                }
            ]
        }

        self.assertEqual(response.data, result) 

    # ******************************************************************* #
    #                            Test Content                             #
    # ******************************************************************* #
    def test_if_view_returns_the_right_content_with_pagination(self):

        # First delete all customers
        Customer.objects.all().delete()

        pagination_page_size = settings.LEAN_PAGINATION_PAGE_SIZE

        model_num_to_be_created = pagination_page_size+1

        customer_names = []
        for i in range(model_num_to_be_created):
            customer_names.append(f'New Customer{i}')

        names_length = len(customer_names)
        # Confirm number of names
        self.assertEqual(names_length, model_num_to_be_created)  

        # Create and confirm customers
        for i in range(names_length):

            Customer.objects.create(
                profile=self.profile,
                name=customer_names[i],
                loyverse_customer_id = uuid.uuid4()
            )

        self.assertEqual(
            Customer.objects.filter(profile=self.profile).count(),
            names_length)  # Confirm models were created

  
        customers = Customer.objects.filter(profile=self.profile).order_by('-id')

        # ######### Test first paginated page - list ######### #

        # Count Number of Queries #
        with self.assertNumQueries(3):
            response = self.client.get(reverse('api:webhook_customers'))
            self.assertEqual(response.status_code, 200)

        response_data_dict = dict(response.data)

        self.assertEqual(response_data_dict['count'], model_num_to_be_created)
        self.assertEqual(
            response_data_dict['next'], 'http://testserver/api/webhook/customers/?page=2')
        self.assertEqual(response_data_dict['previous'], None)
        self.assertEqual(len(response_data_dict['results']), pagination_page_size)

        # For some reason, we need to reverse the order of the results dict
        # for it to match our testing environment values arrangemetn
        response_data_dict['results'].reverse()

        # check if all customers are listed except the first one since it's in the next paginated page #
        i = 0
        for customer in customers[1:]:

            self.assertEqual(
                response_data_dict['results'][i]['name'], customer.name)
            self.assertEqual(
                response_data_dict['results'][i]['loyverse_customer_id'], str(customer.loyverse_customer_id))
            
            i += 1

        # Confirm the number the for loop ran
        self.assertEqual(i, pagination_page_size)  

        # ######### Test second paginated page -  list ######### #
        response = self.client.get(reverse('api:webhook_customers') + '?page=2')
        self.assertEqual(response.status_code, 200)

        result = {
            'count': model_num_to_be_created, 
            'next': None, 
            'previous': 'http://testserver/api/webhook/customers/', 
            'results': [
                {
                    'name': customers[0].name, 
                    'email': customers[0].email,
                    'phone': customers[0].phone,
                    'customer_code': customers[0].customer_code,
                    'loyverse_customer_id': str(customers[0].loyverse_customer_id)
                }
            ]
        }
    
        self.assertEqual(response.data, result)

    def test_if_results_can_be_filtered_by_reg_no(self):

        param = f'?reg_no={self.customer1.reg_no}'
        response = self.client.get(reverse('api:webhook_customers') + param)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 1, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.customer1.name, 
                    'email': self.customer1.email,
                    'phone': self.customer1.phone,
                    'customer_code': self.customer1.customer_code,
                    'loyverse_customer_id': str(self.customer1.loyverse_customer_id)
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_view_returns_empty_when_there_are_no_models(self):

        # First delete all customers
        Customer.objects.all().delete()

        response = self.client.get(
            reverse('api:webhook_customers'), follow=True)
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 0, 
            'next': None, 
            'previous': None, 
            'results': []
        }

        self.assertEqual(response.data, result)

class ApiEmployeeIndexViewTestCase(APITestCase):

    def setUp(self):
        # Create a user1
        self.user = create_new_user('angelina')
        self.user.loyverse_employee_id = uuid.uuid4()
        self.user.loyverse_store_id = uuid.uuid4()
        self.user.save()

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        # Create employee user
        self.employee1 = create_new_manager_user( "gucci", self.profile, self.store1)
        self.employee1.loyverse_employee_id = uuid.uuid4()
        self.employee1.loyverse_store_id = uuid.uuid4()
        self.employee1.save()

        self.employee2 = create_new_cashier_user("kate", self.profile, self.store1)
        self.employee2.loyverse_employee_id = uuid.uuid4()
        self.employee2.loyverse_store_id = uuid.uuid4()
        self.employee2.save()

        self.employee3 = create_new_cashier_user("james", self.profile, self.store1)
        self.employee3.loyverse_employee_id = uuid.uuid4()
        self.employee3.loyverse_store_id = uuid.uuid4()
        self.employee3.save()
    
        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save() 

    def test_view_returns_the_user_customers_only(self):

        # Count Number of Queries #
        # with self.assertNumQueries(2):
        response = self.client.get(reverse('api:webhook_empoyees'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 4, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'full_name': self.user.get_full_name(), 
                    'email': self.user.email,
                    'phone': int(self.user.phone),
                    'loyverse_employee_id': str(self.user.loyverse_employee_id),
                    'loyverse_store_id': str(self.user.loyverse_store_id)
                },
                {
                    'full_name': self.employee1.get_full_name(), 
                    'email': self.employee1.email,
                    'phone': int(self.employee1.phone),
                    'loyverse_employee_id': str(self.employee1.loyverse_employee_id),
                    'loyverse_store_id': str(self.employee1.loyverse_store_id)
                },
                {
                    'full_name': self.employee2.get_full_name(), 
                    'email': self.employee2.email,
                    'phone': int(self.employee2.phone),
                    'loyverse_employee_id': str(self.employee2.loyverse_employee_id),
                    'loyverse_store_id': str(self.employee2.loyverse_store_id)
                },
                {
                    'full_name': self.employee3.get_full_name(), 
                    'email': self.employee3.email,
                    'phone': int(self.employee3.phone),
                    'loyverse_employee_id': str(self.employee3.loyverse_employee_id),
                    'loyverse_store_id': str(self.employee3.loyverse_store_id)
                }
            ]
        }

        self.assertEqual(response.data, result) 

class ApiTaxIndexViewTestCase(APITestCase):

    def setUp(self):
        # Create a user1
        self.user = create_new_user('angelina')

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        # Create a customer users
        self.tax1 = create_new_tax(self.profile, self.store1, 'Standard1')
        self.tax1.loyverse_tax_id = uuid.uuid4()
        self.tax1.save()

        self.tax2 = create_new_tax(self.profile, self.store1, 'Standard2')
        self.tax2.loyverse_tax_id = uuid.uuid4()
        self.tax2.save()

        self.tax3 = create_new_tax(self.profile, self.store1, 'Standard3')
        self.tax3.loyverse_tax_id = uuid.uuid4()
        self.tax3.save()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save() 

    def test_view_returns_the_user_customers_only(self):

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(reverse('api:webhook_taxes'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.tax1.name, 
                    'rate': str(self.tax1.rate),
                    'loyverse_tax_id': str(self.tax1.loyverse_tax_id)
                },
                {
                    'name': self.tax2.name, 
                    'rate': str(self.tax2.rate),
                    'loyverse_tax_id': str(self.tax2.loyverse_tax_id)
                },
                {
                    'name': self.tax3.name, 
                    'rate': str(self.tax3.rate),
                    'loyverse_tax_id': str(self.tax3.loyverse_tax_id)
                }
            ]
        }

        self.assertEqual(response.data, result) 

class ApiStoreIndexViewTestCase(APITestCase):

    def setUp(self):
        # Create a user1
        self.user = create_new_user('angelina')

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        self.store3 = create_new_store(self.profile, 'Shoe Store')
        self.store3.loyverse_store_id = uuid.uuid4()
        self.store3.save()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save() 

    def test_view_returns_the_user_customers_only(self):

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(reverse('api:webhook_stores'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 3, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.store1.name, 
                    'loyverse_store_id': str(self.store1.loyverse_store_id)
                },
                {
                    'name': self.store2.name, 
                    'loyverse_store_id': str(self.store2.loyverse_store_id)
                },
                {
                    'name': self.store3.name, 
                    'loyverse_store_id': str(self.store3.loyverse_store_id)
                }
            ]
        }

        self.assertEqual(response.data, result) 

class ApiProductIndexViewTestCase(APITestCase):

    def setUp(self):
        # Create a user1
        self.user = create_new_user('angelina')

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        self.store3 = create_new_store(self.profile, 'Shoe Store')
        self.store3.loyverse_store_id = uuid.uuid4()
        self.store3.save()


        self.create_products()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save() 


    def create_products(self):

        # Create a products
        # ------------------------------ Product 1
        product = Product.objects.create(
            profile=self.profile,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=product, store=self.store1)
        stock.units = 5100
        stock.save()

        stock = StockLevel.objects.get(product=product, store=self.store2)
        stock.units = 6100
        stock.save()

        # ------------------------------ Product 1
        product2 = Product.objects.create(
            profile=self.profile,
            name="Conditioner",
            price=2000,
            cost=800,
            sku='sku2',
            barcode='code123',
            sold_by_each=False,
            loyverse_variant_id=uuid.uuid4()
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.units = 2100
        stock.save()

        stock = StockLevel.objects.get(product=product2, store=self.store2)
        stock.units = 3100
        stock.save()

        # Create customers
        self.tax1 = create_new_tax(self.profile, self.store1, 'Standard1')
        self.tax1.loyverse_tax_id = uuid.uuid4()
        self.tax1.save()

        self.tax2 = create_new_tax(self.profile, self.store1, 'Standard2')
        self.tax2.loyverse_tax_id = uuid.uuid4()
        self.tax2.save()

        product.tax = self.tax1
        product.save()

        product2.tax = self.tax2
        product2.save()

        self.product1 = Product.objects.get(name="Shampoo")
        self.product2 = Product.objects.get(name="Conditioner")

    def test_view_returns_the_user_customers_only(self):

        # Count Number of Queries #
        # with self.assertNumQueries(3):
        response = self.client.get(reverse('api:webhook_products'))
        self.assertEqual(response.status_code, 200)

        result = {
            'count': 2, 
            'next': None, 
            'previous': None, 
            'results': [
                {
                    'name': self.product1.name, 
                    'loyverse_variant_id': str(self.product1.loyverse_variant_id), 
                    'sku': self.product1.sku, 
                    'barcode': self.product1.barcode, 
                    'cost': str(self.product1.cost), 
                    'loyverse_tax_id': str(self.tax1.loyverse_tax_id), 
                    'is_bundle': self.product1.is_bundle, 
                    'variant_count': self.product1.variant_count, 
                    'stores': self.product1.get_stock_levels()
                }, 
                {
                    'name': self.product2.name, 
                    'loyverse_variant_id': str(self.product2.loyverse_variant_id),
                    'sku': self.product2.sku, 
                    'barcode': self.product2.barcode, 
                    'cost': str(self.product2.cost), 
                    'loyverse_tax_id': str(self.tax2.loyverse_tax_id), 
                    'is_bundle': self.product2.is_bundle, 
                    'variant_count': self.product2.variant_count, 
                    'stores': self.product2.get_stock_levels()
                }
            ]
        }

        self.assertEqual(response.data, result) 

class ApiReceiptIndexViewTestCase(APITestCase):

    def setUp(self):
        # Create a user1
        self.user = create_new_user('angelina')

        self.profile = Profile.objects.get(user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT)

        # Create stores
        self.store1 = create_new_store(self.profile, 'Computer Store')
        self.store1.loyverse_store_id = uuid.uuid4()
        self.store1.save()

        self.store2 = create_new_store(self.profile, 'Toy Store')
        self.store2.loyverse_store_id = uuid.uuid4()
        self.store2.save()

        self.create_products()

        # Turn off maintenance mode#
        ms = MySetting.objects.get(name='main')
        ms.maintenance = False
        ms.save() 


    def create_products(self):

        # Create a products
        # ------------------------------ Product 1
        product = Product.objects.create(
            profile=self.profile,
            name="Shampoo",
            price=2500,
            cost=1000,
            sku='sku1',
            barcode='code123',
            loyverse_variant_id=uuid.uuid4()
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=product, store=self.store1)
        stock.units = 5100
        stock.save()

        stock = StockLevel.objects.get(product=product, store=self.store2)
        stock.units = 6100
        stock.save()

        # ------------------------------ Product 1
        product2 = Product.objects.create(
            profile=self.profile,
            name="Conditioner",
            price=2000,
            cost=800,
            sku='sku2',
            barcode='code123',
            sold_by_each=False,
            loyverse_variant_id=uuid.uuid4()
        )

        # Update stock units for store 1 and 2
        stock = StockLevel.objects.get(product=product2, store=self.store1)
        stock.units = 2100
        stock.save()

        stock = StockLevel.objects.get(product=product2, store=self.store2)
        stock.units = 3100
        stock.save()

        # Create customers
        self.tax1 = create_new_tax(self.profile, self.store1, 'Standard1')
        self.tax1.loyverse_tax_id = uuid.uuid4()
        self.tax1.save()

        self.tax2 = create_new_tax(self.profile, self.store1, 'Standard2')
        self.tax2.loyverse_tax_id = uuid.uuid4()
        self.tax2.save()

        product.tax = self.tax1
        product.save()

        product2.tax = self.tax2
        product2.save()

        self.product1 = Product.objects.get(name="Shampoo")
        self.product2 = Product.objects.get(name="Conditioner")

    def create_receipt(self):

        september_16 = timezone.make_aware(
            value=datetime.datetime(2022, 9, 16, 3, 5),
            timezone=pytz.utc
        )


        # Create receipt1
        receipt1 = Receipt.objects.create(
            user=self.profile.user,
            store=self.store1,
            customer_info={},
            discount_amount=401.00,
            tax_amount=60.00,
            given_amount=2500.00,
            change_amount=500.00,
            subtotal_amount=2000,
            total_amount=1599.00,
            transaction_type=Receipt.MONEY_TRANS,
            payment_completed=True,
            local_reg_no=111,
            receipt_number='110-1000',
            refund_for_receipt_number='109-1000',
            created_date=september_16
        )
        
        # Create receipt line1
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=self.product1,
            product_info={'name': self.product1.name},
            price=1750,
            units=7
        )
    
        # Create receipt line2
        ReceiptLine.objects.create(
            receipt=receipt1,
            product=self.product2,
            product_info={'name': self.product2.name},
            price=2500,
            units=10
        )

    def test_view_returns_the_user_customers_only(self):

        self.create_receipt()

        # Count Number of Queries #
        with self.assertNumQueries(4):
            response = self.client.get(reverse('api:webhook_receipts'))
            self.assertEqual(response.status_code, 200)

        receipt = Receipt.objects.get()

        result = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'created_date':  '2024-01-16T03:05:00Z',
                    'customer_info': receipt.customer_info,
                    'discount_amount': str(receipt.discount_amount),
                    'line_items': receipt.get_line_items(),
                    'loyverse_store_id': str(receipt.loyverse_store_id),
                    'receipt_number': receipt.receipt_number,
                    'refund_for_receipt_number': receipt.refund_for_receipt_number,
                    'subtotal_amount': str(receipt.subtotal_amount),
                    'tax_amount': str(receipt.tax_amount),
                    'total_amount': str(receipt.total_amount)
                }
            ]
        }

        self.assertEqual(response.data, result)

    def test_results_can_be_filtered_by_date(self):

        self.create_receipt()

        # Test correct datetime
        param = '?datetime_after=2024-01-16 6:00&datetime_before=2024-01-16 6:10'
        response = self.client.get(reverse('api:webhook_receipts') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)

        # Test exact datetime
        param = '?datetime_after=2024-01-16 6:05&datetime_before=2024-01-16 6:05'
        response = self.client.get(reverse('api:webhook_receipts') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 1)

        # Test wrong datetime
        param = '?datetime_after=2024-01-16 6:00&datetime_before=2024-01-16 6:04'
        response = self.client.get(reverse('api:webhook_receipts') + param)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['count'], 0)

