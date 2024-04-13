from rest_framework import serializers

from clusters.models import StoreCluster
from stores.models import Store


class StoreClusterFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = Store
        fields = ('reg_no',)

class StoreClusterLeanListSerializer(serializers.ModelSerializer):

    class Meta:
        model = StoreCluster
        fields = (
            'name',
            'reg_no', 
        ) 

class StoreClusterListSerializer(serializers.ModelSerializer):
    stores = serializers.ReadOnlyField(source='get_registered_cluster_stores_data')

    class Meta:
        model = StoreCluster
        fields = (
            'name',
            'stores',
            'reg_no', 
        ) 

class StoreClusterCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, required=True)
    stores_info = serializers.ListField(
        child=StoreClusterFormsetSerializer(),
        allow_empty=False,
        max_length=1000,
        write_only=True
    )

    class Meta:
        model = StoreCluster
        fields = (
            'name',
            'stores_info'
        )

class StoreClusterViewSerializer(serializers.ModelSerializer):
    available_stores = serializers.ReadOnlyField(source='get_available_stores_data')
    cluster_stores = serializers.ReadOnlyField(source='get_registered_cluster_stores_data')
    
    # List field
    stores_info = serializers.ListField(
        child=StoreClusterFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['reg_no'].read_only=True

    class Meta:
        model = StoreCluster
        fields = (
            'name',
            'available_stores',
            'cluster_stores',
            'reg_no', 
            'stores_info'
        ) 