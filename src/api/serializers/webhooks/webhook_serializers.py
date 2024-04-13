from products.models import Product
from rest_framework import serializers

from django.contrib.auth import get_user_model

from inventories.models import StockLevel
from profiles.models import Customer, EmployeeProfile
from sales.models import Receipt
from stores.models import Store, Tax

class ApiStockLevelIndexViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = StockLevel
        fields = (
            'units', 
            'loyverse_store_id',
            'loyverse_variant_id',
        )

class ApiCustomerIndexViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = (
            'name',
            'email',
            'phone', 
            'customer_code',
            'loyverse_customer_id'
        )

class ApiEmployeeIndexViewSerializer(serializers.ModelSerializer):

    full_name = serializers.ReadOnlyField(source='get_full_name')

    class Meta:
        model = get_user_model()
        fields = (
            'full_name',
            'email',
            'phone', 
            'loyverse_employee_id',
            'loyverse_store_id'
        )

class ApiTaxIndexViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tax
        fields = (
            'name',
            'rate',
            'loyverse_tax_id'
        )

class ApiStoreIndexViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = Store
        fields = (
            'name',
            'loyverse_store_id'
        )



class ApiProductIndexViewSerializer(serializers.ModelSerializer):

    stores = serializers.ReadOnlyField(source='get_stock_levels')

    class Meta:
        model = Product
        fields = (
            'name',
            'loyverse_variant_id',
            'sku',
            'barcode',
            'cost',
            'loyverse_tax_id',
            'is_bundle',
            'variant_count',
            'stores',
        )


class ApiReceiptIndexViewSerializer(serializers.ModelSerializer):

    line_items = serializers.ReadOnlyField(source='get_line_items')

    class Meta:
        model = Receipt
        fields = (
            'receipt_number',
            'refund_for_receipt_number',
            'loyverse_store_id',
            'total_amount',
            'subtotal_amount',
            'discount_amount',
            'tax_amount',
            'customer_info',
            'created_date',
            'line_items'
        )