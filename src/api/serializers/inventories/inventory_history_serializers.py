from collections import OrderedDict
from django.conf import settings
from rest_framework import serializers

from inventories.models import InventoryHistory


class InventoryHistoryListSerializer(serializers.ModelSerializer):
    
    creation_date = serializers.SerializerMethodField()
    synced_date = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = InventoryHistory 
        fields = (
            'product_name',
            'store_name',
            'user_name',
            'reason',
            'change_source_reg_no',
            'change_source_desc',
            'change_source_name',
            'adjustment',
            'stock_after',
            'creation_date',
            'synced_date', 
            'reg_no'
        )

    def get_creation_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'

        return obj.get_created_date(self.user.get_user_timezone())
    
    def get_synced_date(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return '-'

        return obj.get_synced_date(self.user.get_user_timezone())
    
