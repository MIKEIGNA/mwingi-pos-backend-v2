from collections import OrderedDict
from django.conf import settings
from rest_framework import serializers
from api.serializers.formset_serializers import (
    ModifierFormsetSerializer, 
    VariantProuctFormsetSerializer
)

from products.models import Product
from inventories.models import StockLevel

class PosProductListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None

        if kwargs.get('store_reg_no', None):
            self.store_reg_no = kwargs.pop('store_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

        self.fields['price'].allow_blank = False
        self.fields['cost'].allow_blank = False

        self.fields['stock_level'].read_only = True

  
    # Read only fields
    is_bundle = serializers.ReadOnlyField()
    variant_count = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    image_url = serializers.ReadOnlyField(source='get_image_url')

    stock_level = serializers.SerializerMethodField()
    category_data = serializers.ReadOnlyField(source='get_category_data')
    tax_data = serializers.ReadOnlyField(source='get_tax_data')
    modifier_data = serializers.ReadOnlyField(source='get_modifier_list')
    variant_data = serializers.SerializerMethodField()

    # Write only fields
    minimum_stock_level = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        write_only=True
    )
    stocks_units = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        write_only=True
    )
    tax_reg_no = serializers.IntegerField(write_only=True)
    category_reg_no = serializers.IntegerField(write_only=True)

    # List field
    modifiers_info = serializers.ListField(
        child=ModifierFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_MODIFIER_COUNT,
        write_only=True
    ) 
    
    class Meta:
        model = Product
        fields = (
            'image_url',
            'color_code',
            'name', 
            'price',
            'cost',
            'sku',
            'barcode',
            'sold_by_each',
            'is_bundle',
            'track_stock',
            'variant_count',
            'show_product',
            'show_image',
            'reg_no',
             
            'minimum_stock_level',
            'stocks_units',
            'stock_level',
            'category_data', 
            'tax_data',
            'modifier_data',
            'variant_data',
            
            'tax_reg_no',
            'category_reg_no',

            'modifiers_info'
        )

    def get_variant_data(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return {}

        try:
            return obj.get_variants_data_from_store(self.store_reg_no)

        except: # pylint: disable=bare-except
            return {}

    def get_stock_level(self, obj):

        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return {}

        return obj.get_store_stock_units(self.store_reg_no)
    
    def validate_name(self, name):
        
        # Check if the user already has a product with the same name
        product_exists = Product.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if product_exists:
            msg = 'You already have a product with this name.'
            raise serializers.ValidationError(msg)
    
        return name   
class PosProductEditSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None

        if kwargs.get('product_reg_no', None):
            self.product_reg_no = kwargs.pop('product_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

    # Write only fields
    minimum_stock_level = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        write_only=True
    )
    stocks_units = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        write_only=True
    )
    tax_reg_no = serializers.IntegerField(write_only=True)
    category_reg_no = serializers.IntegerField(write_only=True)

    # List field
    modifiers_info = serializers.ListField(
        child=ModifierFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_MODIFIER_COUNT,
        write_only=True
    )
    variants_info = serializers.ListField(
        child=VariantProuctFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_VARIANT_COUNT,
        write_only=True
    )

    class Meta:
        model = Product
        fields = (
            'color_code',
            'name', 
            'price',
            'cost',
            'sku',
            'barcode',
            'sold_by_each',
            'track_stock',
            'show_product',
            'show_image',
            
            'minimum_stock_level',
            'stocks_units',
            'tax_reg_no',
            'category_reg_no',

            'modifiers_info',
            'variants_info'
        )

    def validate_name(self, name):
        
        # Check if the user already has a product (other than this one) with the same name
        product_exists = Product.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.product_reg_no).exists()
            
        if product_exists:
            msg = 'You already have a product with this name.'
            raise serializers.ValidationError(msg)

        return name
class PosProductImageEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('image',)

