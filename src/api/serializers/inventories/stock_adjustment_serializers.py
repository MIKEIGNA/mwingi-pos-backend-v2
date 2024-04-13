from collections import OrderedDict
from django.conf import settings

from rest_framework import serializers

from inventories.models import StockAdjustment, StockAdjustmentLine
class StockAdjustmentLineFormsetSerializer(serializers.ModelSerializer):
    product_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = StockAdjustmentLine
        fields = (
            'product_reg_no',
            'add_stock',
            'counted_stock',
            'remove_stock',
            'cost',
        )

class StockAdjustmentListSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    reason_desc = serializers.ReadOnlyField(source='get_reason_desc')
    store_name = serializers.ReadOnlyField(source='get_store_name')
    str_quantity = serializers.ReadOnlyField(source='get_str_quantity')
    reg_no = serializers.ReadOnlyField()
    creation_date = serializers.SerializerMethodField()

    store_reg_no = serializers.IntegerField(write_only=True)

    # List field
    stock_adjustment_lines = serializers.ListField(
        child=StockAdjustmentLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STOCK_ADJUSTMENT_LINE_COUNT,
        write_only=True
    ) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

        self.fields['notes'].write_only = True

    class Meta:
        model = StockAdjustment
        fields = (
            'name',
            'notes',
            'reason',
            'reason_desc',
            'store_name',
            'str_quantity',
            'reg_no',
            'creation_date',
            
            'store_reg_no',
            'stock_adjustment_lines'
        )

    def get_creation_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'
            
        return obj.get_created_date(self.user.get_user_timezone())
    
    

class StockAdjustmentViewSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='__str__')
    reason_desc = serializers.ReadOnlyField(source='get_reason_desc')
    store_name = serializers.ReadOnlyField(source='get_store_name')
    reg_no = serializers.ReadOnlyField()
    adjusted_by = serializers.ReadOnlyField(source='get_adjusted_by')
    creation_date = serializers.SerializerMethodField()
    line_data = serializers.ReadOnlyField(source='get_line_data')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = StockAdjustment
        fields = (
            'name',
            'notes',
            'reason',
            'reason_desc',
            'store_name',
            'quantity',
            'reg_no',
            'adjusted_by',
            'creation_date',
            'line_data',
        )

    def get_creation_date(self, obj):
        return obj.get_created_date(self.user.get_user_timezone())

    
    
    

