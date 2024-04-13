from rest_framework import serializers

from sales.models import Receipt

class ReceiptEmailSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Write only fields
    email = serializers.EmailField(max_length=30, required=True)
    reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = Receipt
        fields = ('email','reg_no', )

    def validate_reg_no(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided a wrong value'

        """ Check if reg_no is too big"""
        # If you change this in the future, change also in your apps verification processes
        if reg_no > 6000000000000: 
            raise serializers.ValidationError(error_msg)
        
        return reg_no