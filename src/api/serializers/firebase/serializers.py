from rest_framework import serializers

from firebase.models import FirebaseDevice

class FirebaseDeviceSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['token'].required=True

    # Write only fields
    store_reg_no = serializers.IntegerField(write_only=True)

    class Meta:
        model = FirebaseDevice
        fields = ('token', 'store_reg_no', )

    def validate_store_reg(self, reg_no):
        
        """Raise a serializers.ValidationError if the reg_no is too big
           number. 
        """
        error_msg = 'You provided a wrong value'

        """ Check if reg_no is too big"""
        # If you change this in the future, change also in your apps verification processes
        if reg_no > 6000000000000: 
            raise serializers.ValidationError(error_msg)
        
        return reg_no


