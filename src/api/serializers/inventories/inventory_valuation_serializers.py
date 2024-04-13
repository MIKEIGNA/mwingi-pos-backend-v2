from rest_framework import serializers

from products.models import Product
from profiles.models import Profile

class InventoryValuationListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.stores_reg_nos = kwargs.pop('stores_reg_nos')
        super().__init__(*args, **kwargs)

    inventory_valuation = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'inventory_valuation',
        )

    def get_inventory_valuation(self, obj):
        return obj.get_inventory_valuation(self.stores_reg_nos)

  
class InventoryValuationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ()

    def to_representation(self, instance):
        context = super().to_representation(instance)

        context['total_inventory_data'] = self.context['total_inventory_data']
        context['product_data'] = self.context['product_data']
        context['stores'] = self.context['stores']
       
        return context