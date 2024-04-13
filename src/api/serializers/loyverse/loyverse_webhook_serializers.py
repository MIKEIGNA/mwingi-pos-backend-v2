from rest_framework import serializers

# pylint: disable=abstract-method
class ApiLoyverseInventoryLevelFormsetSerializer(serializers.Serializer):
    variant_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    store_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    in_stock = serializers.CharField(max_length=100, required=False, allow_blank=True)
    updated_at = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
class LoyverseWebhookInventoryLevelUpdateSerializer(serializers.Serializer):
    merchant_id = serializers.CharField(max_length=100, required=True)
    type = serializers.CharField(max_length=100, required=True)
    created_at = serializers.CharField(max_length=100, required=True)
    inventory_levels = serializers.ListField(
        child=ApiLoyverseInventoryLevelFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

class ApiLoyverseCustomerFormsetSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    name = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True, 
        allow_null= True
    )
    email = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True, 
        allow_null= True
    )
    phone_number = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True, 
        allow_null= True
    )
    customer_code = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True, 
        allow_null= True
    )
    permanent_deletion_at = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        allow_null=True
    )

class ApiLoyverseUpdateFormsetSerializer(serializers.Serializer):
    store_id = serializers.CharField(max_length=100, required=False, allow_blank=True)

class LoyverseWebhookReceiptUpdateSerializer(serializers.Serializer):
    receipts = serializers.ListField(
        child=ApiLoyverseUpdateFormsetSerializer(),
        allow_empty=True,
        max_length=20000,
        write_only=True
    )

class LoyverseWebhookProductUpdateSerializer(serializers.Serializer):
    products = serializers.ListField(
        child=ApiLoyverseUpdateFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

class LoyverseWebhookCustomerUpdateSerializer(serializers.Serializer):
    customers = serializers.ListField(
        child=ApiLoyverseUpdateFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

class LoyverseWebhookTaxUpdateSerializer(serializers.Serializer):
    taxes = serializers.ListField(
        child=ApiLoyverseUpdateFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )

class LoyverseAppDataUpdateSerializer(serializers.Serializer):
    access_token = serializers.CharField(max_length=100, required=True)
    refresh_token = serializers.CharField(max_length=100, required=True)

