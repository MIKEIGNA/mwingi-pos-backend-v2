from rest_framework import serializers

from profiles.models import EmployeeProfile

class MgLeanEmployeeProfileIndexViewSerializer(serializers.ModelSerializer):

    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = EmployeeProfile
        fields = (
            'name', 
            'reg_no',
        )

class MgEmployeeProfileIndexViewSerializer(serializers.ModelSerializer):

    # Read only fields
    name = serializers.ReadOnlyField(source='get_full_name')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_phone = serializers.ReadOnlyField(source='user.phone')
    role_name = serializers.ReadOnlyField()
    class Meta:
        model = EmployeeProfile
        fields = (
            'name', 
            'user_email',
            'user_phone',
            'role_name',
            'reg_no',
        )
         
