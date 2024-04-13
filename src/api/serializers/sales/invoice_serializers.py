from django.conf import settings
from rest_framework import serializers

from sales.models import Invoice, Receipt

class InvoiceReceiptFormsetSerializer(serializers.ModelSerializer):

    receipt_reg_no = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Receipt
        fields = (
            'receipt_reg_no',
        )

    
class InvoiceListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(InvoiceListSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    customer_info = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source='__str__')
    
    payment_type = serializers.ReadOnlyField(source='payment_type.name')
    creation_date = serializers.SerializerMethodField()
    payment_date = serializers.SerializerMethodField()
    reg_no = serializers.ReadOnlyField()

    customer_reg_no =serializers.IntegerField(write_only=True)
    receipt_list = serializers.ListField(
        child=InvoiceReceiptFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_INVOICE_RECEIPT_COUNT,
        write_only=True
    ) 

    class Meta:
        model = Invoice
        fields = (
            'customer_info',
            'name', 
            'total_amount',
            'payment_completed',
            'payment_type',
            'creation_date',
            'payment_date',
            'reg_no',

            'customer_reg_no',
            'receipt_list'
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

    def get_payment_date(self, obj):
        return obj.get_paid_date(self.user.get_user_timezone())

class InvoiceViewSerializer(serializers.ModelSerializer):
    customer_info = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source='__str__')
    payment_completed = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()
    payment_date = serializers.SerializerMethodField()
    invoice_data = serializers.ReadOnlyField(source='get_invoice_view_data')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
        
    class Meta:
        model = Invoice
        fields = (
            'customer_info', 
            'name',
            'total_amount',
            'discount_amount',
            'tax_amount',
            'item_count',
            'payment_completed',
            'reg_no',
            'creation_date',
            'created_date',
            'payment_date',
            'invoice_data',           
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

    def get_payment_date(self, obj):
        return obj.get_paid_date(self.user.get_user_timezone())