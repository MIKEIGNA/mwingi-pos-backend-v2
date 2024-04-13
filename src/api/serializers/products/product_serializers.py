from collections import OrderedDict
from django.conf import settings
from rest_framework import serializers
from api.serializers.formset_serializers import (
    ProductBundleLineFormsetSerializer,
    ProductMapLineFormsetSerializer,
    StoreWebFormsetForEditSerializer, 
    StoreWebFormsetSerializer
)
from core.image_utils import Base64ImageField

from products.models import Product
from inventories.models import StockLevel


class LeanProductStoreListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        if kwargs.get('stores_reg_nos', None):
            self.stores_reg_nos = kwargs.pop('stores_reg_nos')

        super().__init__(*args, **kwargs)

    image_url = serializers.ReadOnlyField(source='get_image_url')
    stock_units = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'image_url',
            'color_code',
            'show_image',
            'name', 
            'cost', 
            'sku', 
            'sold_by_each',
            'tax_rate',
            'reg_no', 
            'stock_units',  
             
        )

    def get_stock_units(self, obj):

        units = []

        store1_reg_no = self.stores_reg_nos['store1_reg_no']
        store2_reg_no = self.stores_reg_nos['store2_reg_no']

        try:
            if (store1_reg_no):
                
                level1 = StockLevel.objects.get(
                    product=obj, 
                    store__reg_no=store1_reg_no
                ).units

                units.append({'units': str(level1)})

        except: # pylint: disable=bare-except
            units.append({'units': str(0)}) 

        try:
            if (store2_reg_no):
                
                level2 = StockLevel.objects.get(
                    product=obj, 
                    store__reg_no=store2_reg_no
                ).units

                units.append({'units': str(level2)})
                
        except: # pylint: disable=bare-except
            units.append({'units': str(0)})

        return units
    
    def get_cost_str(self, obj):
        return str(obj.cost)



class LeanProductListSerializer(serializers.ModelSerializer):

    image_url = serializers.ReadOnlyField(source='get_image_url')

    class Meta:
        model = Product
        fields = (
            'image_url',
            'color_code',
            'show_image',
            'name', 
            'cost', 
            'sku', 
            'reg_no',
        )

        


class ProductListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None
        self.store_reg_no = None

        # store_reg_no is only available during get request but raises an error
        # in a put request
        try:
            self.store_reg_no = kwargs.pop('store_reg_no')
        except: # pylint: disable=bare-except
            pass

        #if kwargs.get('store_reg_no', None):
        #    self.store_reg_no = kwargs.pop('store_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        super().__init__(*args, **kwargs)

        self.fields['price'].allow_blank = False
        self.fields['cost'].allow_blank = False

        self.fields['sku'].write_only = True
        self.fields['barcode'].write_only = True
        self.fields['sold_by_each'].write_only = True

  
    # Read only fields
    is_bundle = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    image_url = serializers.ReadOnlyField(source='get_image_url')

    valuation_info = serializers.SerializerMethodField()
    category_data = serializers.ReadOnlyField(source='get_category_data')
    index_variants_data = serializers.SerializerMethodField()

    # Write only fields
    tax_reg_no = serializers.IntegerField(write_only=True)
    category_reg_no = serializers.IntegerField(write_only=True)
    master_product_reg_no = serializers.IntegerField(write_only=True, required=False)
    uploaded_image = Base64ImageField(
        max_length=None, 
        use_url=True,
        write_only=True,
        required=False,
    )

    # List field ProductBundleLineFormsetSerializer
    bundles_info = serializers.ListField(
        child=ProductBundleLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_PRODUCT_BUNDLE_COUNT,
        write_only=True
    )
    stores_info = serializers.ListField(
        child=StoreWebFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = (
            'image_url',
            'color_code',
            'name', 
            'price',
            'average_price',
            'cost',
            'sku',
            'barcode',
            'sold_by_each',
            'is_bundle',
            'show_image',
            'reg_no',
             
            'valuation_info',
            'category_data', 
            'index_variants_data',
            
            'tax_reg_no',
            'category_reg_no',
            'master_product_reg_no',
            'uploaded_image',

            'bundles_info',
            'stores_info'
        )

    def get_index_variants_data(self, obj):
    
        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return 0

        try:
            if self.store_reg_no:
                return obj.get_index_variants_data([self.store_reg_no])
            else:
                return obj.get_index_variants_data()

        except: # pylint: disable=bare-except
            return {}

    def get_valuation_info(self, obj):
       
        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return 0

        try:

            print(f"*** {self.store_reg_no}")


            if self.store_reg_no:
                return obj.get_valuation_info([self.store_reg_no])
            else:
                return obj.get_valuation_info()
        
        except: # pylint: disable=bare-except
            return 0

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






class ProductEditSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        self.current_user_profile = None

        self.current_employee_profile = None

        if kwargs.get('product_reg_no', None):
            self.product_reg_no = kwargs.pop('product_reg_no')

        if kwargs.get('current_user_profile', None):
            self.current_user_profile = kwargs.pop('current_user_profile')

        if kwargs.get('current_employee_profile', None):
            self.current_employee_profile = kwargs.pop('current_employee_profile')

        super().__init__(*args, **kwargs)

    # Read only fields
    is_bundle = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    image_url = serializers.ReadOnlyField(source='get_image_url')
    
    category_data = serializers.ReadOnlyField(source='get_category_data')
    tax_data = serializers.ReadOnlyField(source='get_tax_data')

    variant_data = serializers.SerializerMethodField()
    bundle_data = serializers.ReadOnlyField(source='get_product_view_bundles_data')

    # Write only fields
    tax_reg_no = serializers.IntegerField(write_only=True)
    category_reg_no = serializers.IntegerField(write_only=True)
    uploaded_image = Base64ImageField(
        max_length=None, 
        use_url=True,
        write_only=True,
        required=False
    )

    # List field
    bundles_info = serializers.ListField(
        child=ProductBundleLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_PRODUCT_BUNDLE_COUNT,
        write_only=True
    )
    stores_info = serializers.ListField(
        child=StoreWebFormsetForEditSerializer(),
        allow_empty=True,
        max_length=settings.MAX_STORE_PER_ACCOUNT,
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
            'is_bundle',
            'show_product',
            'show_image',
            'image_url',
            'reg_no',

            'category_data',
            'tax_data',
            
            'variant_data',
            'bundle_data',
            'tax_reg_no',
            'category_reg_no',
            'uploaded_image',

            'bundles_info',
            'stores_info'
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

    def to_representation(self, instance):
        context = super().to_representation(instance)

        context['available_taxes'] = self.context['available_taxes']
        context['available_categories'] = self.context['available_categories']
        
        context['registered_stores'] = self.context['registered_stores']
        context['available_stores'] = self.context['available_stores']
       
        return context 

    def get_variant_data(self, obj) -> list:
       
        # When posting, obj holds an orderdict which is no use to us
        if type(obj) == OrderedDict:
            return []

        try:
            return obj.get_product_view_variants_data(
                self.current_employee_profile
            )
        
        except: # pylint: disable=bare-except
            return []



class ProductAvailableDataViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ()

    def to_representation(self, instance):
        context = super().to_representation(instance)

        context['taxes'] = self.context['taxes']
        context['categories'] = self.context['categories']
        context['stores'] = self.context['stores']
       
        return context 

class ProductMapListSerializer(serializers.ModelSerializer):

    reg_no = serializers.IntegerField(write_only=True)

    # List field ProductMapLineFormsetSerializer
    map_info = serializers.ListField(
        child=ProductMapLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_PRODUCT_BUNDLE_COUNT,
        write_only=True
    )
    
    class Meta:
        model = Product
        fields = ('reg_no', 'map_info',)

class ProductMapEditSerializer(serializers.ModelSerializer):

    name = serializers.ReadOnlyField()
    map_data = serializers.ReadOnlyField(source='get_product_view_production_data')

    # List field ProductMapLineFormsetSerializer
    map_info = serializers.ListField(
        child=ProductMapLineFormsetSerializer(),
        allow_empty=True,
        max_length=settings.MAX_PRODUCT_BUNDLE_COUNT,
        write_only=True
    ) 
    
    class Meta:
        model = Product
        fields = ('name', 'map_data', 'map_info',)   


class ProductTransformMapListSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        if kwargs.get('store_model', None):
            self.store_model = kwargs.pop('store_model')

        super().__init__(*args, **kwargs)

    transform_data = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'transform_data',     
        )

    def get_transform_data(self, obj):
        return obj.get_product_view_transform_data(self.store_model)
    