from rest_framework import serializers

from sales.models import Receipt

class ReceiptListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ReceiptListSerializer, self).__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    customer_info = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source='__str__')
    reg_no = serializers.ReadOnlyField()

    sale_maker = serializers.ReadOnlyField(source='user.get_full_name')
    store_name = serializers.ReadOnlyField(source='store.name')
    payment_type = serializers.ReadOnlyField(source='get_payment_type')
    sale_type = serializers.ReadOnlyField(source='get_sale_type')
    creation_date = serializers.SerializerMethodField()
    synced_date = serializers.SerializerMethodField()

    class Meta:
        model = Receipt
        fields = (
            'customer_info',
            'name', 
            'total_amount',
            'is_refund',
            'sale_maker',
            'store_name',
            'payment_type',
            'sale_type',
            'reg_no',
            'creation_date',
            'synced_date', 
        ) 

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())
    
    def get_synced_date(self, obj):
        return obj.get_sync_date(self.user.get_user_timezone())
    

class ReceiptViewSerializer(serializers.ModelSerializer):
    customer_info = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source='__str__')
    receipt_closed = serializers.ReadOnlyField()
    is_refund = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()
    receipt_data = serializers.ReadOnlyField(source='get_receipt_view_data')
    store_till_number = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
        
    class Meta:
        model = Receipt
        fields = (
            'customer_info', 
            'name',
            'refund_for_receipt_number',
            'discount_amount',
            'tax_amount',
            'subtotal_amount',
            'total_amount',
            'given_amount',
            'change_amount',
            'payment_completed',
            'receipt_closed',
            'is_refund',
            'item_count',
            'local_reg_no',
            'reg_no',
            'creation_date',
            'created_date_timestamp',
            'receipt_data',   
            'tims_success',
            'tims_cu_serial_number',
            'tims_cu_invoice_number',
            'tims_rel_doc_number',
            'tims_verification_url',
            'store_till_number', 
            'show_discount_breakdown'   
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())
    
    def get_store_till_number(self, obj):
        return obj.store.till_number