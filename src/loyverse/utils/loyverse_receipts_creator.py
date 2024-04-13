import datetime
from decimal import Decimal
from pprint import pprint
import dateutil

from django.contrib.auth import get_user_model
from accounts.models import UserGroup
from accounts.utils.user_type import EMPLOYEE_USER

from core.time_utils.date_helpers import DateHelperMethods
from inventories.models.stock_models import StockLevel
from stores.models import Store, StorePaymentMethod, Tax
from django.utils import timezone
from django.conf import settings
from core.logger_manager import LoggerManager

from loyverse.utils.loyverse_api import LoyverseApi
from products.models import Product
from profiles.models import Customer, EmployeeProfile, Profile

from sales.models import Receipt, ReceiptLine, ReceiptPayment

class LoyverseReceiptSync:
    
    def __init__(self, profile, hours_to_go_back=1, receipts=None) -> None:
        """
        Retrives receipts from loyverse that were created hours ago from now. The
        number of hours to go back is determined by the hours_to_go_back.

        If the receipts are not passed during initialization, they are fetched
        directly from loyverse.

        Args:
            hours_to_go_back (int): An int indicating how many hours we have to 
            go back.
            receipts (list): A list from loyverse that holds receipts data
        """
        self.profile = profile
        self.hours_to_go_back = hours_to_go_back
        self.receipts = receipts
        self.receipts_min_date = timezone.now() + datetime.timedelta(
            hours=-self.hours_to_go_back
        )

        if not receipts:
            self.receipts = self.get_receipts().get('receipts', [])

    def sync_receipts(self):
    
        receipt_numbers = Receipt.objects.filter(
            store__profile=self.profile,
            created_date__gte=self.receipts_min_date
        ).values_list('receipt_number', flat=True)

        new_receipts = [
            receipt for receipt in self.receipts \
                if not receipt['receipt_number'] in receipt_numbers
        ]

        CreateLoyverseReceipts(profile=self.profile, receipts=new_receipts).create_receipts()

    def get_receipts(self):

        back_date = (self.receipts_min_date).strftime("%Y-%m-%dT%H:%M:00.000Z")

        return LoyverseApi.get_paginated_data(
            url=f'{settings.LOYVERSE_RECEIPTS_URL}&created_at_min={back_date}', 
            response_key="receipts"
        )

class LoyverseReceiptSync2:
    
    def __init__(self, profile, min_date, max_date) -> None:
        """
        Retrives receipts from loyverse that were created hours ago from now. The
        number of hours to go back is determined by the hours_to_go_back.

        If the receipts are not passed during initialization, they are fetched
        directly from loyverse.

        Args:
            hours_to_go_back (int): An int indicating how many hours we have to 
            go back.
            receipts (list): A list from loyverse that holds receipts data
        """
        self.profile = profile
        self.min_date = min_date
        self.max_date = max_date
        self.receipts_min_date = timezone.make_aware(DateHelperMethods.get_date_from_date_str(self.min_date))
        
        self.receipts = self.get_receipts().get('receipts', [])

    def sync_receipts(self):
        pprint(self.receipts)
        CreateLoyverseReceipts(profile=self.profile, receipts=self.receipts).create_receipts()

    def get_receipts(self):

        print(f'Min date = {self.min_date}, Max = {self.max_date}, Min datetime = {self.receipts_min_date}')

        return LoyverseApi.get_paginated_data(
            url=f'{settings.LOYVERSE_RECEIPTS_URL}&created_at_min={self.min_date}&created_at_max={self.max_date}', 
            response_key="receipts"
        )


class LoyverseReceiptSync3:
    
    def __init__(self, profile, min_date, max_date, store_id) -> None:
        """
        Retrives receipts from loyverse that were created hours ago from now. The
        number of hours to go back is determined by the hours_to_go_back.

        If the receipts are not passed during initialization, they are fetched
        directly from loyverse.

        Args:
            hours_to_go_back (int): An int indicating how many hours we have to 
            go back.
            receipts (list): A list from loyverse that holds receipts data
        """
        self.profile = profile
        self.min_date = min_date
        self.max_date = max_date
        self.store_id = store_id
        self.receipts_min_date = timezone.make_aware(DateHelperMethods.get_date_from_date_str(self.min_date))
        
        self.receipts = self.get_receipts().get('receipts', [])

        print(len(self.receipts))

    def sync_receipts(self):
        CreateLoyverseReceipts(profile=self.profile, receipts=self.receipts).create_receipts()

    def get_receipts(self):

        print(f'Min date = {self.min_date}, Max = {self.max_date}, Min datetime = {self.receipts_min_date}')

        url = settings.LOYVERSE_RECEIPTS_URL

        return LoyverseApi.get_paginated_data(
            url=f'{url}&store_id={self.store_id}&created_at_min={self.min_date}&created_at_max={self.max_date}', 
            response_key="receipts"
        )

class LoyverseReceiptSync4:
    
    def __init__(self, min_date, max_date) -> None:
        """
        Retrives receipts from loyverse that were created hours ago from now. The
        number of hours to go back is determined by the hours_to_go_back.

        If the receipts are not passed during initialization, they are fetched
        directly from loyverse.

        Args:
            hours_to_go_back (int): An int indicating how many hours we have to 
            go back.
            receipts (list): A list from loyverse that holds receipts data
        """
        self.min_date = min_date
        self.max_date = max_date
    
        self.receipts = self.get_receipts().get('receipts', [])
  
    def sync_receipts(self):
        profile = Profile.objects.get(
            user__email=settings.LOYVERSE_OWNER_EMAIL_ACCOUNT
        )
        CreateLoyverseReceipts(profile=profile, receipts=self.receipts).create_receipts()

    def get_receipts(self):

        print(f'Min date = {self.min_date}, Max = {self.max_date}')
        return LoyverseApi.get_paginated_data(
            url=f'{settings.LOYVERSE_RECEIPTS_URL}&created_at_min={self.min_date}&created_at_max={self.max_date}', 
            response_key="receipts"
        )



    

class CreateLoyverseReceipts:

    def __init__(self, profile, receipts) -> None:
        """
        Creates multipile LoyverseReceipt model from the receipts data

        Args:
            profile (Profile): Profile model
            receipts (list): Loyverse's receipt data
        """
        self.profile = profile

        # Loyvserse returns a list that starts with the latest record. Incase we
        # have a refund, this will be a problem since the refund will be created
        # in our system before the receipt being refunded. To fix this, we reverse
        # the list so that the sale is always created first before the refund
        self.receipts = receipts
        self.receipts.reverse() # We reverse the list so that we can have

        self.mpesa_store_ids_to_update = {}

        product_data = Product.objects.filter(profile=profile)
    
        self.product_map_data = {
            str(product.loyverse_variant_id): {
                'barcode': product.barcode,
                'model': product
            }  for product in product_data}

    def round_number(self, number):
        """
        Returns a rounded off decimal number into 2 decimal places
        """
        return round(Decimal(number), 2)

    def round_number_as_str(self, number):
        """
        Returns a string of a rounded off decimal number into 2 decimal places
        """
        return str(round(Decimal(number), 2))

    def get_taxes(self, data, tax_key):
        """
        data (dict): A dict of that has sales data 
        tax_key (str): The name of the key that holds tax data in a list 
        Return:
            list - A list with taxes data
        """
        taxes = [
            {
                'name': tax['name'],
                'rate': str(tax['rate']),
                'amount': str(self.round_number(tax['money_amount']))

            } for tax in data[tax_key] ]

        return taxes
    
    def get_tax_amount_for_receipt_line(self, data):
        """
        Get tax details for a a single receipt line

        Returns a tuple with (tax_amount, tax_name, tax_rate)
        """

        tax_amount = 0
        tax_name = ''
        tax_rate = 0

        taxes = self.get_taxes(data=data, tax_key='line_taxes')

        if taxes:
            tax_data = taxes[0]

            tax_amount = tax_data['amount']
            tax_name = tax_data['name']
            tax_rate = tax_data['rate']

        return {
            'name': tax_name,
            'rate': Decimal(tax_rate),
            'amount': Decimal(tax_amount)
        }

    def get_payments(self, receipt):
        """
        Return:
            list - A list with receipt payments data
        """

        payments = [
            {
                'name': payment['name'],
                'amount': str(self.round_number(payment['money_amount'])), 
            } for payment in receipt['payments'] ]

        return payments

    def get_line_items(self, receipt):
        """
        Return:
            list - A list with receipt line items data
            Decimal - Total cost for the receipt
        """

        total_cost_for_receipt = 0.0
        line_items = []
        for item in receipt['line_items']:
            hs_code = self.product_map_data.get(str(item['variant_id']), '')
            quantity = Decimal(item['quantity'])
            price = Decimal(item['price'])
            total_discount = Decimal(item['total_discount'])
            # total_tax = Decimal(item['total_tax'])
            total_amount = Decimal(item['total_money'])

            # Get tax details
            tax_data = self.get_tax_amount_for_receipt_line(data=item)

            vat_name = tax_data['name']
            vat_rate = Decimal(tax_data['rate'])
            vat_amount = Decimal(tax_data['amount'])

            data = {
                'item_name': item['item_name'],
                'hs_code': hs_code,
                'quantity': str(quantity),
                'price': str(price),
                'total_amount': str(self.round_number(total_amount)),
                'total_discount': str(self.round_number(total_discount)),
                'vat_name': vat_name,
                'vat_rate': str(vat_rate),
                'vat_amount': str(vat_amount),
                'variant_id': str(item['variant_id']),
            }

            line_items.append(data)

            total_cost_for_receipt += item['cost_total']

        return line_items, total_cost_for_receipt

    def get_customer_details(self, receipt):
        """
        Returns a dict with customer data or an empty dict when there is no
        customer with the provided customer id from the receipt
        """

        customer_id = receipt['customer_id']

        customer_model = None
        customer_info = {}

        if customer_id:

            customers = Customer.objects.filter(
                profile=self.profile,
                loyverse_customer_id=customer_id
            )

            if customers:
                customer_model = customers[0]

                customer_info['name'] = customer_model.name
                customer_info['reg_no'] = customer_model.reg_no

        return customer_model, customer_info

    def create_receipts(self):

        i=0
        for receipt in self.receipts: 
            self.create_receipt(receipt=receipt)

            i+=1

    def create_receipt(self, receipt):
        """
        Creates the LoyverseReceipt model from the loyverse receipt data

        1. Ignores cancelled receipts
        2. Ignores empty line_items and instead send's an email alert.
        3. Ignores the receipt if we already have a receipt with the same receipt
           number.
        4. If it's a refund, update tims_rel_doc_number with the data from the 
           receipt being refunded.
        5. After creation, update the mpesa daily log that matches the new 
           receipt's store and date
        """
        receipt_number = receipt['receipt_number']

        # if receipt_number in ['324-1545']: return

        if receipt['cancelled_at']: return

        if len(receipt['line_items']) == 0:
            # LoyverseReceiptEmpty.objects.get_or_create(receipt_number=receipt_number)
            return

        # Don't create receipt if it already exists
        receipt_exits = Receipt.objects.filter(
            store__profile=self.profile,
            receipt_number=receipt_number
        ).exists()
        
        if receipt_exits: return
   
        customer_model, customer_info = self.get_customer_details(receipt=receipt)

        refund_for = receipt['refund_for']
        refund_for = refund_for if refund_for else ''
        
        store_id = receipt['store_id']
        employee_id = receipt['employee_id']

        created_date = dateutil.parser.isoparse(receipt['receipt_date'])

        
        changed_stock = True if created_date.year < 2024 else False

        total_money = self.round_number(receipt['total_money'])
        total_tax=self.round_number(receipt['total_tax'])
        total_discount=self.round_number(receipt['total_discount'])
        total_subtotal = total_money + total_discount

        store = None
        try:
            store = Store.objects.get(
                profile=self.profile,
                loyverse_store_id=store_id
            )

        except Exception: # pylint: disable=bare-except

            created_date = timezone.make_aware(
                DateHelperMethods.get_date_from_date_str('2023-12-01T00:00:00.000Z')
            )

            store = Store.objects.create(
                profile=self.profile,
                name=store_id[:10],
                loyverse_store_id=store_id,
                is_deleted=True,
                created_date=created_date,
                deleted_date=created_date
            )

        try:
            user = get_user_model().objects.get(
                loyverse_employee_id=receipt['employee_id']
            )
            
        except:

            first_name = employee_id[:10]
            user_parms = {
                'first_name': first_name,
                'last_name': first_name,
                'email': f'{first_name}@gmail.com',
                'phone': 0,
                'user_type': EMPLOYEE_USER,
                'loyverse_employee_id': employee_id,
                'loyverse_store_id': store_id,
                'gender':0, 
                'password': '12345678'
            }

            user = get_user_model().objects.create_user(**user_parms)

            role_reg_no = UserGroup.objects.get(
                master_user__profile=self.profile,
                ident_name='Cashier'
            ).reg_no

            employee_data = {
                'user': user,
                'profile': self.profile,
                'phone': 0,
                'reg_no': user.reg_no,
                'role_reg_no': role_reg_no,
                'loyverse_employee_id': employee_id,
                'loyverse_store_id': store_id,
            }

            employee_profile = EmployeeProfile.objects.create(**employee_data)

        try:

            

            receipt_model = Receipt.objects.create(
                user=user,
                store=store,
                customer=customer_model,
                customer_info=customer_info,
                discount_amount=total_discount,
                tax_amount=total_tax,
                given_amount=0.00,
                change_amount=0.00,
                subtotal_amount=total_subtotal,
                total_amount=total_money,
                transaction_type=Receipt.MONEY_TRANS,
                payment_completed=True,
                local_reg_no=222,
                receipt_number=receipt_number,
                refund_for_receipt_number=refund_for ,
                created_date=created_date,
                changed_stock=changed_stock,
            )

            # This means the receipt save was rejected since the receipt was a 
            # duplicate
            if receipt_model.pk == None: return

            pay_method = StorePaymentMethod.objects.get(
                profile__store=store,
                payment_type=StorePaymentMethod.CASH_TYPE
            )

            ReceiptPayment.objects.create(
                receipt=receipt_model,
                payment_method=pay_method,
                amount=total_money
            )

            self.create_receipt_lines(receipt_model, receipt['line_items'])

            # Update cost
            receipt_model.calculate_and_update_total_cost()

            # Send receipt data to connector
            receipt_model.send_receipt_to_connector()
          
        except Exception as e:
            print(f'Error {e}')
            addition_message = {
                'receipt_number': receipt_number,
                'employee_id': receipt['employee_id'],
                'store_id': store_id
            }
            
            LoggerManager.log_critical_error(additional_message=str(addition_message))
        
    def create_receipt_lines(self, receipt_model, line_items):
   
        for index, item in enumerate(line_items):

            try:

                # This is to ensure that the created_date is unique for rceipt
                # that have the same product more than once

                created_date = receipt_model.created_date+ datetime.timedelta(microseconds=index)

                try:
                    product = Product.objects.get(
                        profile=self.profile,
                        loyverse_variant_id=item['variant_id']
                    )
                except: # pylint: disable=bare-except

                    product = Product.objects.create(
                        profile=receipt_model.store.profile,
                        name="Faceed out product",
                        sku=item['item_name'],
                        barcode=item['item_name'],
                        loyverse_variant_id=item['variant_id'],
                        price=item['price'],
                        cost=item['cost'],
                        is_deleted=True,
                    )

                quantity = item['quantity']
                price = item['price']
                cost = product.cost

                # cost = item['cost']
                # cost_total = item['cost_total']
                gross_total_money = item['gross_total_money']
                total_money = item['total_money']
                total_discount = item['total_discount']

                tax = None
                if item['line_taxes']:
                    taxes = Tax.objects.filter(
                        profile=self.profile,
                        loyverse_tax_id=item['line_taxes'][0]['id']
                    )
                    if taxes:
                        tax = taxes[0]

                self.receiptline =  ReceiptLine.objects.create(
                    receipt=receipt_model,
                    tax=tax,
                    product=product,
                    price=price,
                    cost=cost,
                    # cost_total=cost_total,
                    total_amount=total_money,
                    gross_total_amount=gross_total_money,
                    discount_amount=total_discount,
                    units=quantity,
                    created_date=created_date,  
                )

                # Only update the price if the stock level product price is 
                    # different from the price in the receipt line
                stock_level = StockLevel.objects.filter(
                    store=receipt_model.store,
                    product=product
                ).first()

                if stock_level: 
                    current_price = stock_level.price

                    if current_price != price:
                        StockLevel.objects.filter(
                            store=receipt_model.store,
                            product=product
                        ).update(price=price)

                        # This forces the an update to the product price
                        product.save()

            except Exception as e:
                print("Error creating receipt line ", e)
                LoggerManager.log_critical_error()

 