from django.conf import settings
from rest_framework import serializers
from products.models import Modifier, Product, ProductProductionMap

from stores.models import Store


MAX_STORE_LEVEL_VALUE = 1000000

class StoreFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = Store
        fields = ('reg_no',)

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class StoreWebFormsetSerializer(serializers.ModelSerializer):

    is_sellable = serializers.BooleanField(required=True, write_only=True)
    price = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        required=True, 
        write_only=True
    )
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = Store
        fields = ('is_sellable', 'price', 'reg_no',)

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no
    

class StoreWebFormsetForEditSerializer(serializers.ModelSerializer):

    is_sellable = serializers.BooleanField(required=True, write_only=True)
    price = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        required=True, 
        write_only=True
    )

    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)

    is_dirty = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = Store
        fields = ('is_sellable', 'price', 'reg_no', 'is_dirty')

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class StoreWebVariantFormsetSerializer(serializers.ModelSerializer):

    in_stock = serializers.IntegerField(
        write_only=True, 
        max_value=MAX_STORE_LEVEL_VALUE
    )
    minimum_stock_level = serializers.IntegerField(
        write_only=True, 
        max_value=MAX_STORE_LEVEL_VALUE
    )
    
    # We redefine reg_no to by pass the unique validator
    store_reg_no = serializers.IntegerField(required=True, write_only=True)
    product_reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = Store
        fields = ('in_stock', 'minimum_stock_level', 'store_reg_no',)

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no



class ModifierFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    class Meta:
        model = Modifier
        fields = ('reg_no',)

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class VariantProuctFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    minimum_stock_level = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        required=True, 
        write_only=True
    )
    stock_units = serializers.DecimalField(
        max_digits=30,
        decimal_places=2,
        required=True, 
        write_only=True
    )
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    class Meta:
        model = Product
        fields = (
            'name',
            'price',
            'cost',
            'sku',
            'barcode',
            'show_product',
            'minimum_stock_level',
            'stock_units',
            'reg_no',
            'is_dirty'
        )

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no



class VariantWebProuctCreateFormsetSerializer(serializers.ModelSerializer):

    stores_info = serializers.ListField(
        child=StoreWebFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = (
            'name',
            'price',
            'cost',
            'sku',
            'barcode',
            'stores_info',
        )

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class VariantWebProuctEditFormsetSerializer(serializers.ModelSerializer):
    
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    
    stores_info = serializers.ListField(
        child=StoreWebFormsetSerializer(),
        allow_empty=False,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    )

    is_dirty = serializers.BooleanField(required=True, write_only=True)
    class Meta:
        model = Product
        fields = (
            'name',
            'price',
            'cost',
            'sku',
            'barcode',
            'show_product',
            'reg_no',
            'stores_info',
            'is_dirty'
        )

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class ProductBundleLineFormsetSerializer(serializers.ModelSerializer):
    
    quantity = serializers.IntegerField(
        write_only=True, 
        max_value=MAX_STORE_LEVEL_VALUE
    )
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    
    class Meta:
        model = Product
        fields = ('quantity', 'reg_no', 'is_dirty')

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no


class ProductMapLineFormsetSerializer(serializers.ModelSerializer):
    
    quantity = serializers.IntegerField(
        write_only=True, 
        max_value=MAX_STORE_LEVEL_VALUE
    )
    is_auto_repackage= serializers.BooleanField(required=True, write_only=True)
    # We redefine reg_no to by pass the unique validator
    reg_no = serializers.IntegerField(required=True, write_only=True)
    is_dirty = serializers.BooleanField(required=True, write_only=True)
    
    class Meta:
        model = ProductProductionMap
        fields = ('quantity', 'is_auto_repackage', 'reg_no', 'is_dirty')

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided wrong stores'

        """ Check if reg_no is too big"""
        if reg_no > 6000000000000: # If you change this in the future, change also in your apps verification processes
            raise serializers.ValidationError(error_msg)
        
        return reg_no