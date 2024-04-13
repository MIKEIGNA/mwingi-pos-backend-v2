import requests
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from accounts.utils.user_type import TOP_USER
from accounts.utils.currency_choices import CURRENCY_CHOICES

from core.time_utils.date_helpers import DateHelperMethods

from core.time_utils.time_localizers import utc_to_local_datetime_with_format
from products.models import ModifierOption, Product
from profiles.models import Customer, LoyaltySetting, Profile
from stores.models import Discount, Store, Tax, StorePaymentMethod
from inventories.models import InventoryHistory, StockLevel

# ========================== START receipt models
class Receipt(models.Model):
    # To avoid mismatch errors, this constants number values should match
    # PAYMENT_CHOICES ordering 
    MONEY_TRANS = 0
    DEBT_TRANS = 1
    LOYALTY_TRANS = 2
    MULTIPLE_TRANS = 3

    TRACNSACTION_CHOICES = [
        (MONEY_TRANS, 'Money transaction'),
        (DEBT_TRANS, 'Debt transaction'),
        (LOYALTY_TRANS, 'Loyalty transaction'),
        (MULTIPLE_TRANS, 'Multiple transaction')
    ]
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    ) 
    discount = models.ForeignKey(
        Discount,
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
    customer_info = models.JSONField(
        verbose_name='customer_info', default=dict)
    subtotal_amount = models.DecimalField(
        verbose_name='subtotal amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        verbose_name='total amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        verbose_name='discount amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        verbose_name='tax amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    given_amount = models.DecimalField(
        verbose_name='given amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    change_amount = models.DecimalField(
        verbose_name='change amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    loyalty_points_amount = models.DecimalField(
        verbose_name='loyalty points amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    total_cost = models.DecimalField(
        verbose_name='total cost',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    transaction_type = models.IntegerField(
        verbose_name='transaction type',
        choices=TRACNSACTION_CHOICES,
        default=0
    )
    payment_completed = models.BooleanField(
        verbose_name='payment completed',
        default=False
    )
    customer_points_update_completed = models.BooleanField(
        verbose_name='customer points update completed',
        default=False
    )
    # Should be true if transaction_type was DEBT_TRANS when receipt was originally made
    # and should not change even after payment has been complted.
    is_debt = models.BooleanField(
        verbose_name='is debt',
        default=False
    )
    # A receipt is cloased when a payment has aready been made.
    receipt_closed = models.BooleanField(
        verbose_name='receipt closed',
        default=False
    )
    is_refund = models.BooleanField(
        verbose_name='refund completed',
        default=False
    )
    was_refunded = models.BooleanField(
        verbose_name='was refunded',
        default=False
    )
    
    item_count = models.IntegerField(
        verbose_name='item count',
        default=0
    )
    local_reg_no = models.BigIntegerField(
        verbose_name='local reg no',
        default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )
    receipt_number = models.CharField(
        verbose_name='receipt number',
        max_length=30,
        # unique=True,
        default='',
    )
    receipt_number_for_testing = models.CharField(
        verbose_name='receipt number for testing',
        max_length=30,
        default='',
        blank=True,
    )
    refund_for_receipt_number = models.CharField(
        verbose_name='refund for receipt number',
        max_length=30,
        default='',
        blank=True,
    )
    refund_for_reg_no = models.BigIntegerField(
        verbose_name='refund for reg no',
        default=0
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True
    )
    created_date_timestamp = models.BigIntegerField(
        verbose_name='created date timestamp',
        default=0
    )


    loyverse_store_id = models.UUIDField(
        verbose_name='loyverse store id',
        db_index=True,
        null=True,
        blank=True,
    )
    changed_stock = models.BooleanField(
        verbose_name='changed stock',
        default=True
    )
    stock_marked_for_change = models.BooleanField(
        verbose_name='stock marked for change',
        default=False,
        null=True,
        blank=True,
    )
    show_discount_breakdown = models.BooleanField(
        verbose_name='show_discount_breakdown',
        default=False,
    )

    # This field should never be updated. It should never be changed from 
    # what it was when the receipt was created
    sync_date = models.DateTimeField(
        verbose_name='sync date',
        default=timezone.now,
        db_index=True
    )

    # Fields to be used for faster queries
    user_reg_no = models.BigIntegerField(
        verbose_name='user reg no',
        default=0,
    )
    store_reg_no = models.BigIntegerField(
        verbose_name='store reg no',
        default=0,
    )

    # The following fields are filled from the tims response
    tims_rel_doc_number = models.CharField(
        verbose_name='tims rel doc number',
        default='',
        blank=True,
        max_length=35,
        db_index=True
    )
    tims_cu_serial_number = models.CharField(
        verbose_name='tims cu serial number',
        default='',
        blank=True,
        max_length=100
    )
    tims_cu_invoice_number = models.CharField(
        verbose_name='tims cu invoice number',
        default='',
        blank=True,
        max_length=35
    )
    tims_verification_url = models.CharField(
        verbose_name='tims verification url',
        default='',
        blank=True,
        max_length=150
    )
    tims_description = models.CharField(
        verbose_name='tims description',
        default='',
        blank=True,
        max_length=100
    )
    tims_success = models.BooleanField(
        verbose_name='tims success',
        default=False,
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=['user_reg_no', 'store_reg_no', 'created_date']),
        ]

    def __str__(self):
        if self.receipt_number:
            return f'Receipt#: {self.receipt_number}'
        
        return f'Receipt#: {self.local_reg_no}'

    def get_name(self):
        return self.__str__() 

    def get_profile(self):
        """ Returns the sale's store's profile"""
        return self.store.profile

    def get_sale_maker_desc(self):
        """ Returns the sale's user's name"""
        return "Served by: {}".format(self.user.get_full_name())

    def get_customer_name_desc(self):
        """ Returns the receipts's host's name"""

        if self.customer:
            return "Customer: {}".format(self.customer.name)
        else:
            return ''
    
    # TODO: Test this
    def get_customer_name_and_points_desc(self):
    
        if self.customer:

            loyalty = LoyaltySetting.objects.get(profile=self.customer.profile).value

            if loyalty:
                return "Customer: {} ({} Points)".format(
                    self.customer.name, 
                    self.customer.points
                )
            else:
                return f"Customer: {self.customer.name}"
        else:
            return ''

    def get_sale_type(self):
        return 'Refund' if self.is_refund else 'Sale'

    def get_item_units(self):

        total_units_sum = self.receiptline_set.all().aggregate(
            Sum('units')).get('units__sum', 0)

        return total_units_sum if total_units_sum else 0

    def get_item_units_desc(self):
        return f"Total Items: {self.get_item_units()}"

    def get_payment_type(self):

        payments_list = ReceiptPayment.objects.filter(receipt=self).values_list(
            'payment_method__name',
            flat=True
        )

        return ', '.join(payments_list)

    def get_total_amount_desc(self):
        return f"Total Amount: {format(CURRENCY_CHOICES[0][1])} {self.total_amount}"

    def get_subtotal_amount_and_currency(self):
        return f"{CURRENCY_CHOICES[0][1]} {self.subtotal_amount}"

    def get_total_amount_and_currency(self):
        return f"{CURRENCY_CHOICES[0][1]} {self.total_amount}"

    def get_discount_amount_and_currency(self):
        return f"{CURRENCY_CHOICES[0][1]} {self.discount_amount}"

    def get_tax_amount_and_currency(self):
        return f"{CURRENCY_CHOICES[0][1]} {self.tax_amount}"

    def get_created_date(self, local_timezone=settings.LOCATION_TIMEZONE):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_sync_date(self, local_timezone=settings.LOCATION_TIMEZONE):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.sync_date, local_timezone)
    # Make created date to be filterable
    get_sync_date.admin_order_field = 'sync_date'
    
    def get_admin_created_date(self):
        """Return the creation date in local time format"""
        return self.get_created_date(settings.LOCATION_TIMEZONE)
    # Make created_date to be filterable
    get_admin_created_date.admin_order_field = 'created_date'

    # TODO Test this
    def get_payment_list(self):

        # Payment list
        payment_list = ReceiptPayment.objects.filter(receipt=self).values_list(
            'payment_method__name',
            'payment_method__payment_type',
            'payment_method__reg_no',
            'amount'
        )

        payment_list = [
            {
                'name': payment[0],
                'payment_type': payment[1],
                'reg_no': str(payment[2]),
                'amount': str(payment[3]),
            }
            for payment in payment_list
        ]

        return payment_list

    def get_receipt_view_data(self):
        """
        This is used by both web and api views
        """
        
        # Sales
        sales_queryset = list(
            self.receiptline_set.all().order_by('id'
                                                ).values(
                'product_info',
                'price',
                'discount_amount',
                'tax_rate', 
                'sold_by_each',
                'is_variant',
                'units',
                'refunded_units',
                'modifier_options_info',
                'total_amount',
                'gross_total_amount',
                'reg_no' 
            ) 
        )

        # For some reason, if the price, is 4000.00, the api serializer displayse
        # 4000.0 . To avoid that problem, we turn price into a string here before
        # being used by api serializer
        sales = []
        for sale in sales_queryset:
            sales.append(
                {
                    'product_info': sale['product_info'],
                    'price': str(sale['price']),
                    'discount_amount': str(sale['discount_amount']),
                    'tax_rate': str(sale['tax_rate']),
                    'sold_by_each': sale['sold_by_each'],
                    'is_variant': sale['is_variant'],
                    'units': str(sale['units']),
                    'refunded_units': str(sale['refunded_units']),
                    'modifier_options_info': sale['modifier_options_info'],
                    'total_amount': str(sale['total_amount']), 
                    'gross_total_amount': str(sale['gross_total_amount']), 
                    'reg_no': sale['reg_no']
                }
            )

        data = {
            'sale_maker_desc': self.get_sale_maker_desc(),
            'payment_list': self.get_payment_list(),
            'table_content': sales
        }

        return data

    def calculate_and_update_total_cost(self):

        total_cost = self.receiptline_set.all().aggregate(
            cost_total=Coalesce(Sum('cost_total'), Decimal(0.00))
        )['cost_total']

        Receipt.objects.filter(pk=self.pk).update(total_cost=total_cost)

    def update_debt_fields(self):

        # This ensures that is_debt wont be changed later when payment type has
        # been updated
        if self.transaction_type == Receipt.DEBT_TRANS:
            self.is_debt = True

    def create_customer_debt(self, created):

        # Create CustomerDebt
        if created and self.customer and not self.payment_completed:
            CustomerDebt.objects.create(
                customer=self.customer,
                receipt=self,
                debt=self.subtotal_amount,
                reg_no=self.reg_no,
                created_date=self.created_date
            )

    def update_receipt_count_and_close_sale(self):

        if not self.receipt_closed:

            """
            When an receipt has just been created, obviously ReceiptCount wont have
            been created so this code update will fail. 
            This is intended to update ReceiptCount's payment_completed when
            the earlier payment was not completed but now has been completed
            """
            try:
                receipt_count = ReceiptCount.objects.get(reg_no=self.reg_no)
                receipt_count.payment_completed = self.payment_completed
                receipt_count.save()

            except:  # pylint: disable=bare-except
                pass

            if self.payment_completed:
                self.receipt_closed = True

                if self.customer:
                    CustomerDebt.objects.filter(receipt=self).delete()

                self.update_customer_points(True)

        else:
            # This ensures that once a payment has been made, the action cannot
            # be reversed
            self.payment_completed = True

    def perform_credit_payment_completed(self, payment_list):
        """
        If payment type is correct and payment has not been completed, payment
        is accecepted
        """
        if self.payment_completed: return True
        if not payment_list: return False

        payment_data = []
        for payment in payment_list:

            payment_method = self.store.profile.get_store_payment_method_from_reg_no(
                payment['payment_method_reg_no']
            )

            if not payment_method: return False

            if payment_method.payment_type == StorePaymentMethod.DEBT_TYPE:
                return False

            payment_data.append(
                {
                    'payment_method': payment_method,
                    'payment_type': payment_method.payment_type,
                    'amount': payment['amount']
                }
            )

        # Delete old payments and create new ones
        self.receiptpayment_set.all().delete()

        self.loyalty_points_amount = Decimal(0.00)
        for payment in payment_data:

            ReceiptPayment.objects.create(
                receipt=self,
                payment_method=payment['payment_method'],
                amount=payment['amount']
            )

            if payment['payment_type'] == StorePaymentMethod.POINTS_TYPE:
                self.loyalty_points_amount += Decimal(payment['amount'])

        if len(payment_data) > 1:
            self.transaction_type = Receipt.MULTIPLE_TRANS
        else:

            if payment_data[0]['payment_type'] == StorePaymentMethod.POINTS_TYPE:
                self.transaction_type = Receipt.LOYALTY_TRANS

            elif payment_data[0]['payment_type'] == StorePaymentMethod.DEBT_TYPE:
                self.transaction_type = Receipt.DEBT_TRANS

            else:
                self.transaction_type = Receipt.MONEY_TRANS


        self.payment_completed = True
        self.save()

        return True
    
    @staticmethod
    def get_receipts_data(store, reg_nos_list):

        param = f'?reg_nos={",".join([str(r) for r in reg_nos_list])}'

        if settings.TESTING_MODE:
            # Include an appropriate `Authorization:` header on all requests.
            token = Token.objects.get(user__email='john@gmail.com')
            client = APIClient()
            client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

            response = client.get(
                reverse('api:pos_receipt_index', args=(store.reg_no,))+param)
            
        else:

            # receipt1.save()
            url = f'{settings.MY_SITE_URL}/api/pos/receipts/{store.reg_no}/{param}'

            access_token=Token.objects.filter(user__profile=store.profile).first()

            if access_token:
                my_headers = {'Authorization' : f'Token {access_token}'}
                response = requests.get(
                    url=url, 
                    headers=my_headers,
                    timeout=settings.PYTHON_REQUESTS_TIMEOUT
                )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def get_refunded_receipts_from_url(self):
        return Receipt.get_receipts_data(
            self.store, 
            [self.reg_no, self.refund_for_reg_no]
        )

  

        # if settings.TESTING_MODE:
        #     # Include an appropriate `Authorization:` header on all requests.
        #     token = Token.objects.get(user__email='john@gmail.com')
        #     client = APIClient()
        #     client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        #     param = f'?reg_nos={self.reg_no},{self.refund_for_reg_no}'
        #     response = client.get(
        #         reverse('api:pos_receipt_index', args=(self.store.reg_no,))+param)
            
        # else:

        #     # receipt1.save()
        #     url = f'{settings.MY_SITE_URL}/api/pos/receipts/{self.store.reg_no}/?reg_nos={self.reg_no},{self.refund_for_reg_no}'

        #     access_token=Token.objects.filter(user__profile=self.store.profile).first()

        #     if access_token:
        #         my_headers = {'Authorization' : f'Token {access_token}'}
        #         response = requests.get(
        #             url=url, 
        #             headers=my_headers,
        #             timeout=settings.PYTHON_REQUESTS_TIMEOUT
        #         )

        # if response.status_code == 200:
        #     return response.json()
        # else:
        #     return None
    
    def perform_new_refund(
            self, 
            discount_amount,
            tax_amount,
            subtotal_amount,
            total_amount,
            loyalty_points_amount,
            item_count,
            local_reg_no,
            receipt_number,
            created_date_timestamp,
            receipt_line_data):
        

        print("We are in perform_new_refund")
        
        for refund_line in receipt_line_data:
            line = ReceiptLine.objects.filter(reg_no=refund_line['line_reg_no']).first()

            if line:
                if (line.refunded_units + refund_line['refund_units']) > line.units:
                    return []
        
        refund_receipt = Receipt.objects.create(
            shift=None,
            user=self.user,
            store=self.store,
            customer=self.customer,
            customer_info=self.customer_info,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            given_amount=0,
            change_amount=0,
            subtotal_amount=subtotal_amount,
            total_amount=total_amount,
            loyalty_points_amount=loyalty_points_amount,
            transaction_type=self.transaction_type,
            payment_completed=True,
            refund_for_receipt_number=self.receipt_number,
            refund_for_reg_no=self.reg_no,
            item_count=item_count,
            local_reg_no=local_reg_no,
            receipt_number=receipt_number,
            receipt_number_for_testing=receipt_number,
            created_date_timestamp=created_date_timestamp
        )


        print("We lines are being created now")

        for line in receipt_line_data:
            
            refunded_price = line['price']
            refunded_total_amount = line['total_amount']
            refunded_gross_total_amount = line['gross_total_amount']
            refunded_discount_amount = line['discount_amount']
            refunded_units = line['refund_units']
            reg_no = line['line_reg_no']

            refunded_receipt_line = ReceiptLine.objects.get(reg_no=reg_no)
  
            # TODO make the parent receipt to call save so that save mehtod can be
            # called which will call firebase
            ReceiptLine.objects.filter(reg_no=reg_no).update(
                refunded_units=F('refunded_units') + refunded_units
            )

            ReceiptLine.objects.create(
                receipt=refund_receipt,
                parent_product=refunded_receipt_line .parent_product,
                product=refunded_receipt_line.product,
                product_info=refunded_receipt_line.product_info,
                modifier_options_info=refunded_receipt_line.modifier_options_info,
                price=refunded_price,
                total_amount=refunded_total_amount,
                gross_total_amount=refunded_gross_total_amount,
                is_variant=refunded_receipt_line.is_variant,
                sold_by_each=refunded_receipt_line.sold_by_each,
                discount_amount=refunded_discount_amount,
                units=refunded_units,
                tax=refunded_receipt_line.tax,
            )


        print("Was the refund receipt created?")


        self.was_refunded = True
        self.save()

        print("Wass #######")

        # refund_receipt.send_firebase_refund_message()


        return refund_receipt.get_refunded_receipts_from_url()
    
    
    def perform_refund(self):
        """
        1. Updates product's stock levels
        2. Update receipt and receipt count's self.is_refund
        """

        # Only continue if refund has not been done before
        if self.is_refund:
            return

        # This prevents a refund from being performed more than ones
        self.is_refund = True
        self.save()

        receipt_lines = self.receiptline_set.all()
        for line in receipt_lines:
            line.update_product_stock_units(refund=True)

        try:
            receipt_count = ReceiptCount.objects.get(reg_no=self.reg_no)
            receipt_count.is_refund = self.is_refund
            receipt_count.save()
        except:  # pylint: disable=bare-except
            pass 

    def update_customer_points(self, created):

        if not created or not self.customer or self.customer_points_update_completed:
            return
     
        if self.transaction_type == Receipt.DEBT_TRANS:
            return

        profile = None
        if self.user.user_type == TOP_USER:
            profile = self.user.profile
        else:
            profile = self.user.employeeprofile.profile

        # Calculate points
        value = LoyaltySetting.objects.get(profile=profile).value
        # To prevent a nasty race condition between customer debt's signals and
        # this method both calling customer save, We retrive the user afresh
        customer = Customer.objects.get(pk=self.customer.pk)

        if not value > 1:
            return


        if self.loyalty_points_amount > 0:
            points = (value * self.loyalty_points_amount)//100

            customer.points -= self.loyalty_points_amount
            customer.save()

        else:
            points = (value * self.subtotal_amount)//100

            customer.points += points
            customer.save()

        # This ensures that once an update has been made, the action cannot
        # be done agion
        self.customer_points_update_completed = True

    def create_receipt_count(self, created):

        # Create ReceiptCount
        if created:
            # We input created date to ease analytics testing
            ReceiptCount.objects.create(
                user=self.user,
                store=self.store,
                customer=self.customer,
                subtotal_amount=self.subtotal_amount,
                total_amount=self.total_amount,
                discount_amount=self.discount_amount,
                tax_amount=self.tax_amount,
                transaction_type=self.transaction_type,
                payment_completed=self.payment_completed,
                is_refund=self.is_refund,
                reg_no=self.reg_no,
                created_date=self.created_date
            )

    def format_date_fields(self):
        """
        If we have a valid created_date_timestamp, we get created date from it. 
        If the created_date_timestamp is wrong, we replace it with the default 
        created_date's timestamp 
        """

        self.created_date, self.created_date_timestamp = DateHelperMethods.date_and_timestamp_equilizer(
            self.created_date, self.created_date_timestamp
        )
        
    def send_firebase_update_message(self, created):
        """
        If created is true, we send a receipt creation message. Otherwise we
        send a receipt edit message
        """
        from firebase.message_sender_receipt import ReceiptMessageSender

        if created:
            ReceiptMessageSender.send_receipt_creation_update_to_user(self)
        else:
            ReceiptMessageSender.send_receipt_edit_update_to_user(self)

    def send_firebase_refund_message(self):
        """
        Sends a receipt refund message
        """

        print("$$$$$$$$$$$$$$$$$$")
        from firebase.message_sender_receipt import ReceiptMessageSender

        ReceiptMessageSender.send_receipt_refund_update_to_user(self)

    def get_line_items(self):

        sales_queryset = list(
            self.receiptline_set.all().values(
                'product_info',
                'units',
                'price',
                'total_amount',
                'gross_total_amount',
                'discount_amount',
                'cost_total',
                'cost',
                'tax_info',  
            )
        )

        sales = [
            {
                'product_info': sale['product_info'],
                'units': str(sale['units']),
                'price': str(sale['price']),
                'total_amount': str(sale['total_amount']),
                'gross_total_amount': str(sale['gross_total_amount']),
                'discount_amount': str(sale['discount_amount']),
                'cost': str(sale['cost']),
                'cost_total': str(sale['cost_total']),
                'tax_info': sale['tax_info'],
            }
            for sale in sales_queryset
        ]

        return sales
    
    def send_receipt_to_connector(self):
        """
        Sends receipt data to the Mwingi connector in the background
        """

        from accounts.tasks import (
            send_data_to_connector_task,
            MWINGI_CONN_RECEIPT_REQUEST
        )

        # When testing, don't perform task in the background
        if settings.TESTING_MODE:
            send_data_to_connector_task(
                request_type=MWINGI_CONN_RECEIPT_REQUEST,
                model_reg_no=self.reg_no
            )
        
        else:
            send_data_to_connector_task.delay(
                request_type=MWINGI_CONN_RECEIPT_REQUEST,
                model_reg_no=self.reg_no
            )

    @staticmethod
    def get_receipt_number_field_to_use_during_testing():
        """
        Returns the field to use when getting receipt numbers during testing
        involving stock change
        """
        receipt_number_field = 'receipt_number'
        if settings.TESTING_MODE:
            receipt_number_field = 'receipt_number_for_testing'
        return receipt_number_field
    
    def resave_customer_info(self):

        if self.customer:
            Receipt.objects.filter(pk=self.pk).update(
                customer_info={
                    'name': self.customer.name, 
                    'email': self.customer.email,
                    'phone': self.customer.phone,
                    'tax_pin': self.customer.tax_pin,
                    'reg_no': self.customer.reg_no
                }
            )

    def save(self, *args, **kwargs):

        """ Check if this object is being created """
        created = self.pk is None

        if self.refund_for_receipt_number or self.refund_for_reg_no:
            self.is_refund = True

        if self.store:
            self.loyverse_store_id = self.store.loyverse_store_id

        # Get the customer info
        if self.customer:
            self.customer_info = {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'tax_pin': self.customer.tax_pin,
                'reg_no': self.customer.reg_no
            }

        # Save fields to facilitate faster queries by eliminating joins
        self.user_reg_no = self.user.reg_no
        self.store_reg_no = self.store.reg_no
        
        self.update_debt_fields()

        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Creates the right created date and created_date_timestamp
        self.format_date_fields()

        # Update receipt count and close receipt if payment has been closed
        self.update_receipt_count_and_close_sale()

        # We keep checking for duplicates because of the loyverse issue
        receipt_exits = Receipt.objects.filter(
            receipt_number=self.receipt_number,
        ).exclude(pk=self.pk).exists()

        if receipt_exits:
            return
        
        # Call the "real" save() method.
        super(Receipt, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.create_customer_debt(created)
        self.update_customer_points(created)
        self.create_receipt_count(created)
        # self.send_firebase_update_message(created)

class ReceiptCount(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    subtotal_amount = models.DecimalField(
        verbose_name='subtotal amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        verbose_name='total amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        verbose_name='discount amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        verbose_name='tax amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    transaction_type = models.IntegerField(
        verbose_name='transaction type',
        choices=Receipt.TRACNSACTION_CHOICES,
        default=0
    )
    payment_completed = models.BooleanField(
        verbose_name='payment completed',
        default=False
    )
    is_refund = models.BooleanField(
        verbose_name='refund completed',
        default=False
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
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

    def save(self, *args, **kwargs):

        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        super(ReceiptCount, self).save(*args, **kwargs)

# ========================== END receipt models


# ========================== START receipt line models

class ReceiptLine(models.Model): 
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, db_index=True)
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    tax = models.ForeignKey(
        Tax,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
    )
    parent_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent_product"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_info = models.JSONField(
        verbose_name='product info', 
        default=dict,
        blank=True,
    )
    tax_info = models.JSONField(
        verbose_name='tax info', 
        default=dict,
        blank=True,
    )
    modifier_options = models.ManyToManyField(
        ModifierOption,
        null=True,
        blank=True,)
    modifier_options_info = models.JSONField(
        verbose_name='modifier options info', 
        default=list,
        blank=True,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        verbose_name='price',
        max_digits=30,
        decimal_places=2,
        default=0,
    ) 
    cost = models.DecimalField(
        verbose_name='cost',
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    cost_total = models.DecimalField(
        verbose_name='cost total',
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    total_amount = models.DecimalField(
        verbose_name='total amount',
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    gross_total_amount = models.DecimalField(
        verbose_name='gross total amount',
        max_digits=30,
        decimal_places=2,
        default=0,
    )
    discount_amount = models.DecimalField(
        verbose_name='discount amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    is_variant = models.BooleanField(verbose_name='is variant', default=False)
    sold_by_each = models.BooleanField(
        verbose_name='sold by each',
        default=True
    )
    units = models.DecimalField(
        verbose_name='units',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    refunded_units = models.DecimalField(
        verbose_name='refunded units',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True,
    )


    

    # Fields to be used for faster queries
    user_reg_no = models.BigIntegerField(
        verbose_name='user reg no',
        default=0,
    )
    store_reg_no = models.BigIntegerField(
        verbose_name='store reg no',
        default=0,
    )
    product_name = models.CharField(
        verbose_name='product name',
        max_length=100,
        default=''
    )
    category_name = models.CharField(
        verbose_name='category name',
        max_length=100,
        default=''
    )
    user_name = models.CharField(
        verbose_name='user name',
        max_length=100,
        default=''
    )
    tax_name = models.CharField(
        verbose_name='tax name',
        max_length=100,
        default=''
    )
    tax_rate = models.DecimalField(
        verbose_name='tax rate',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    receipt_number = models.CharField(
        verbose_name='receipt number',
        max_length=30,
        default='',
        blank=True,
    )
    refund_for_receipt_number = models.CharField(
        verbose_name='refund for receipt number',
        max_length=30,
        default='',
        blank=True,
    )

    #### Fields for tally
    synced_with_tally = models.BooleanField(
        verbose_name='synced with tally',
        default=False
    )

    def __str__(self):
        return f'(ReceiptLine) {self.receipt_number}'

    def get_name(self):
        return self.__str__()

    def get_profile(self):
        """ Returns the receiptline's product's profile"""
        return self.product.profile

    def get_receiptline_maker(self):
        """ Returns the receiptline's user's name"""
        return self.user.get_full_name()

    def get_receiptline_maker_desc(self):
        """ Returns the receiptline's user's name"""
        return "Made by: {}".format(self.user.get_full_name())

    def get_units(self):
        return self.units

    def get_units_desc(self):
        return "Units: {}".format(self.units)

    def get_price_and_currency(self):
        return f"{CURRENCY_CHOICES[self.product.get_currency()][1]} {self.price}"

    def get_price_and_currency_desc(self):
        return f"Price: {CURRENCY_CHOICES[self.product.get_currency()][1]} {self.price}"

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def update_product_stock_units(self, refund=False):
        """
        Updates product's or bundled product stock units
        """
    
        if not self.product:
            return
        
        change_source_name = self.receipt.__str__()

        if self.product.track_stock:

            # Update stock level
            if self.receipt.is_refund:
                StockLevel.update_level(
                    user=self.user,
                    store=self.store, 
                    product=self.product, 
                    inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_REFUND,
                    change_source_reg_no=self.receipt.reg_no,
                    change_source_name=change_source_name,
                    line_source_reg_no=self.reg_no,
                    adjustment=self.units, 
                    update_type=StockLevel.STOCK_LEVEL_UPDATE_ADDING,
                    created_date=self.created_date
                )

            else:

                StockLevel.update_level(
                    user=self.user,
                    store=self.store, 
                    product=self.product, 
                    inventory_history_reason=InventoryHistory.INVENTORY_HISTORY_SALE,
                    change_source_reg_no=self.receipt.reg_no,
                    change_source_name=change_source_name,
                    line_source_reg_no=self.reg_no,
                    adjustment=self.units, 
                    update_type=StockLevel.STOCK_LEVEL_UPDATE_SUBSTRACTING,
                    created_date=self.created_date
                )

    def create_receiptline_count(self, created):

        # Create ReceiptLineCount
        if created:
            # We input created date to ease analytics testing
            ReceiptLineCount.objects.create(
                user=self.user,
                store=self.store,
                product=self.product,
                customer=self.customer,
                price=self.price,
                discount_amount=self.discount_amount,
                units=self.units,
                reg_no=self.reg_no,
                created_date=self.created_date
            )

    def save(self, *args, **kwargs):

        if self.product:
            self.product_info={
                'name': self.product.name, 
                'reg_no': self.product.reg_no,
                'loyverse_variant_id': str(self.product.loyverse_variant_id),
            }

        if self.tax:
            self.tax_info={
                'name': self.tax.name, 
                'rate': str(self.tax.rate),
                'loyverse_tax_id': str(self.tax.loyverse_tax_id),
            }

        # Save fields to facilitate faster queries by eliminating joins
        self.user = self.receipt.user
        self.user_name = self.user.get_full_name()
        self.user_reg_no = self.user.reg_no

        self.store = self.receipt.store
        self.store_reg_no = self.store.reg_no

        self.product_name = self.product.name if self.product else ''

        if self.product:
            if self.product.category:
                self.category_name = self.product.category.name if self.product else ''

        self.tax_name = self.tax.name if self.tax else '0'
        self.tax_rate = self.tax.rate if self.tax else 0

        self.receipt_number = self.receipt.receipt_number
        self.refund_for_receipt_number = self.receipt.refund_for_receipt_number


        self.customer = self.receipt.customer

        # Determine sale name
        if self.product:
            self.name = f'(ReceiptLine) {self.product.name}'

        else:
            self.name = '(ReceiptLine) Delete product'

        # Update cost
        # This is a mistake that was made when creating the receiptline. But ww
        # have to live with it. 
        if self.product:
            self.cost = Decimal(self.product.cost) * Decimal(self.units)
            self.cost_total = self.cost

        # Create date
        if not self.created_date:
            self.created_date = self.receipt.created_date

        # Updates product's stock units
        # self.update_product_stock_units(refund=self.receipt.is_refund)
   
        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        """ Check if this object is being created """
        created = self.pk is None

        # Call the "real" save() method.
        super(ReceiptLine, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.create_receiptline_count(created)


class ReceiptLineCount(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        verbose_name='price',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        verbose_name='discount amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    units = models.IntegerField(
        verbose_name='units',
        default=0,
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,
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




# ========================== START invoice models
class Invoice(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    receipts = models.ManyToManyField(Receipt)
    payment_type = models.ForeignKey(StorePaymentMethod, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    customer_info = models.JSONField(
        verbose_name='customer_info', default=dict)
    total_amount = models.DecimalField(
        verbose_name='total amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        verbose_name='discount amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        verbose_name='tax amount',
        max_digits=30,
        decimal_places=2,
        default=0
    )
    item_count = models.IntegerField(
        verbose_name='item count',
        default=0
    )
    payment_completed = models.BooleanField(
        verbose_name='payment completed',
        default=False
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True
    )
    created_date = models.DateTimeField(
        verbose_name='created date',
        default=timezone.now,
        db_index=True
    )
    paid_date = models.DateTimeField(
        verbose_name='paid date',
        default=timezone.now,
        db_index=True
    )
    reg_no = models.BigIntegerField(
        verbose_name='reg no',
        unique=True,  # GetUniqueRegNoForModel makes sure it's unique
        editable=False,
    )

    def __str__(self):
        return f'Invoice#: {self.reg_no}'

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def get_paid_date(self, local_timezone):
        """Return the paid date in local time format"""
        return utc_to_local_datetime_with_format(self.paid_date, local_timezone)
    # Make paid_date to be filterable
    get_paid_date.admin_order_field = 'created_date'

    

    def calculate_and_update(self):

        aggre = self.receipts.aggregate(
            total_amount=Sum('total_amount'), 
            discount_amount=Sum('discount_amount'), 
            tax_amount=Sum('tax_amount'), 
            item_count=Sum('item_count'), 
        )

        # Turn decimal values into strings
        total = {k: str(round(v, 2)) if v else Decimal('0.00') for k, v in aggre.items()}

        self.total_amount = total['total_amount']
        self.discount_amount = total['discount_amount']
        self.tax_amount = total['tax_amount']
        self.item_count = total['item_count']

        self.save()

    def mark_as_paid(self, store_payment_method):

        receipts = self.receipts.filter(payment_completed=False)

        if receipts:

            pay_method = StorePaymentMethod.objects.get(
                profile=self.profile,
                payment_type=store_payment_method
            )

            for receipt in receipts:

                # Set payment completed
                receipt.perform_credit_payment_completed(
                    [
                        {
                            'payment_method_reg_no': pay_method.reg_no,
                            'amount': receipt.total_amount
                        }
                    ]
                )
            self.payment_type = pay_method
            self.paid_date = timezone.now()
            self.payment_completed = True

            self.save()

    def get_invoice_view_data(self, local_timezone):

        data = []
        for receipt in self.receipts.order_by('id'):

            receipt_data = receipt.get_receipt_view_data()
            receipt_data['created_date'] = receipt.get_created_date(local_timezone)

            data.append(receipt_data)

        return data

    def save(self, *args, **kwargs):

        """ Check if this object is being created """
        created = self.pk is None

        if created:
            self.customer_info = {
                'name': self.customer.name, 
                'email': self.customer.email,
                'phone': self.customer.phone,
                'reg_no': self.customer.reg_no
            }
        
        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        # Call the "real" save() method.
        super(Invoice, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """

# ========================== END invoice models

# ========================== START receipt payment models
class ReceiptPayment(models.Model):
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(StorePaymentMethod, on_delete=models.CASCADE)
    amount = models.DecimalField(
        verbose_name='amount',
        max_digits=30,
        decimal_places=2,
        default=0,
    )

    def __str__(self):
        return self.payment_method.__str__()

# ========================== END receipt line models


# ========================== START customer debt models
class CustomerDebt(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )
    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.CASCADE,
    )
    debt = models.DecimalField(
        verbose_name='debt',
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
        default=timezone.now
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'

    def create_customer_debt_count(self, created):

        # Create CustomerDebtCount
        if created:
            # We input created date to ease analytics testing
            CustomerDebtCount.objects.create(
                customer=self.customer,
                receipt=self.receipt,
                debt=self.debt,
                reg_no=self.reg_no,
                created_date=self.created_date
            )

    def save(self, *args, **kwargs):
        """ If reg_no is 0 get a unique one """
        if not self.reg_no:
            from core.reg_no_generator import GetUniqueRegNoForModel

            """ Get the model class """
            model = (self.__class__)

            self.reg_no = GetUniqueRegNoForModel(model)

        """ Check if this object is being created """
        created = self.pk is None

        # Call the "real" save() method.
        super(CustomerDebt, self).save(*args, **kwargs)

        """
        To avoid using post save signal we use our custom way to know if the model
        is being created
        """
        self.create_customer_debt_count(created)


class CustomerDebtCount(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    receipt = models.OneToOneField(
        Receipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    debt = models.DecimalField(
        verbose_name='debt',
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
        default=timezone.now
    )

    def get_created_date(self, local_timezone):
        """Return the creation date in local time format"""
        return utc_to_local_datetime_with_format(self.created_date, local_timezone)
    # Make created_date to be filterable
    get_created_date.admin_order_field = 'created_date'


# ========================== START customer debt models
