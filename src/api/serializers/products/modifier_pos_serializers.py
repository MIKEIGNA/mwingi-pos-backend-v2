from rest_framework import serializers

from products.models import Modifier


class PosModifierListSerializer(serializers.ModelSerializer):

    # Read only fields
    reg_no = serializers.ReadOnlyField()
    modifier_options = serializers.ReadOnlyField(source='get_modifier_options')

    class Meta:
        model = Modifier
        fields = ('name', 'description', 'reg_no', 'modifier_options')