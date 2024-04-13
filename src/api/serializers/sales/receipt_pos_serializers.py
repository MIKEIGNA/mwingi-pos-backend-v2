from collections import OrderedDict
from django.conf import settings
from rest_framework import serializers
from products.models import Product
from profiles.models import Customer

from sales.models import Receipt, ReceiptLine
from stores.models import StorePaymentMethod


class ReceiptCustomerFormsetSerializer(serializers.ModelSerializer):

    # We use this name to differentiate theis field with reg_no which is
    # uneditable in Customer model
    customer_reg_no = serializers.IntegerField(write_only=True)
    class Meta:
        model = Customer
        fields = (
            'name',
            'customer_reg_no', 
        )

class ReceiptLineProductFormsetSerializer(serializers.ModelSerializer):

    # We use this name to differentiate theis field with reg_no which is
    # uneditable in product model
    product_reg_no = serializers.IntegerField(write_only=True)
    class Meta:
        model = Product
        fields = (
            'name',
            'product_reg_no', 
        )

class StorePaymentMethodFormsetSerializer(serializers.ModelSerializer):

    amount = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        required=True, 
        write_only=True
    )
    payment_method_reg_no =serializers.IntegerField(write_only=True)
    class Meta:
        model = StorePaymentMethod
        fields = (
            'amount',
            'payment_method_reg_no', 
        )

class ReceiptLineFormsetSerializer(serializers.ModelSerializer):

    tax_reg_no = serializers.IntegerField(write_only=True)
    parent_product_reg_no = serializers.IntegerField(write_only=True)
    product_details = serializers.DictField(
        child=ReceiptLineProductFormsetSerializer(),
    ) 
    modifier_option_reg_nos = serializers.ListField(
        child=serializers.IntegerField()
    )
    modifier_options_details = serializers.ListField(
        child=serializers.CharField(),
    )
    # We redefine reg_no to by pass the required
    reg_no = serializers.ReadOnlyField()
    
    class Meta:
        model = ReceiptLine
        fields = (
            'tax_reg_no',
            'parent_product_reg_no',
            'product_details',
            'modifier_option_reg_nos',
            'modifier_options_details',

            'price',
            'is_variant',
            'sold_by_each',
            'discount_amount', 
            'units', 
            'reg_no'
        )

class PosReceiptListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(PosReceiptListSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)


    customer_info = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source='__str__')
    receipt_closed = serializers.ReadOnlyField()
    is_refund = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()
    receipt_data = serializers.ReadOnlyField(source='get_receipt_view_data')

    # List field
    customer_details = serializers.DictField(
        child=ReceiptCustomerFormsetSerializer(),
        allow_empty=True,
        write_only=True
    ) 
    payment_methods = serializers.ListField(
        child=StorePaymentMethodFormsetSerializer(),
        allow_empty=True,
        max_length=100,
        write_only=True
    ) 
    receipt_lines = serializers.ListField(
        child=ReceiptLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_RECEIPT_LINE_COUNT,
        write_only=True
    )

    class Meta:
        model = Receipt
        fields = (
            'customer_info', 
            'name',
            'receipt_number',
            'refund_for_receipt_number', 
            'discount_amount',
            'tax_amount',
            'subtotal_amount',
            'total_amount',
            'given_amount',
            'change_amount',
            'transaction_type',
            'payment_completed',
            'receipt_closed',
            'is_refund',
            'item_count',
            'local_reg_no',
            'reg_no',
            'id',
            'creation_date',
            'created_date_timestamp',
            'receipt_data',
            'customer_details',
            'payment_methods',
            'receipt_lines',          
        )
 
    def get_creation_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-' 

        return obj.get_created_date(obj.user.get_user_timezone())
   
class PosReceiptCompletePaymentViewSerializer(serializers.ModelSerializer):

    payment_methods = serializers.ListField(
        child=StorePaymentMethodFormsetSerializer(),
        allow_empty=True,
        max_length=100,
        write_only=True
    ) 
    class Meta:
        model = Receipt
        fields = (
            'given_amount',
            'change_amount',
            'transaction_type',
            'payment_completed',
            'payment_methods'
        )

class PosReceiptRefundViewSerializer(serializers.ModelSerializer):
    request_refund = serializers.BooleanField(write_only=True)
    class Meta:
        model = Receipt
        fields = ('request_refund',)




class PosReceiptRefundPerLineFormsetSerializer(serializers.ModelSerializer):

    refund_units = serializers.IntegerField(write_only=True)
    line_reg_no = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ReceiptLine
        fields = (
            'price',
            'total_amount',
            'gross_total_amount',
            'discount_amount',
            'refund_units',
            'line_reg_no'
        )

class PosReceiptRefundPerLineViewSerializer(serializers.ModelSerializer):

    receipt_lines = serializers.ListField(
        child=PosReceiptRefundPerLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_RECEIPT_LINE_COUNT,
        write_only=True
    )
    
    class Meta:
        model = Receipt
        fields = (
            'discount_amount',
            'tax_amount',
            'subtotal_amount',
            'total_amount',
            'item_count',
            'local_reg_no',
            'receipt_number',
            'created_date_timestamp',
            'receipt_lines',        
        )
