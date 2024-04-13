from rest_framework import serializers

from sales.models import Receipt


class TimsReceiptViewUpdateLineFormsetSerializer(serializers.ModelSerializer):

    receipt_number = serializers.CharField(max_length=30, write_only=True)

    class Meta:
        model = Receipt
        fields = (
            'receipt_number',
            'tims_cu_serial_number',
            'tims_cu_invoice_number',
            'tims_verification_url',
            'tims_description',
        )

class TimsReceiptViewUpdateSerializer(serializers.Serializer):
    # List field
    tims_data = serializers.ListField(
        child=TimsReceiptViewUpdateLineFormsetSerializer(),
        allow_empty=True,
        max_length=1000,
        write_only=True
    )