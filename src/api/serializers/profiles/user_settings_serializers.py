from rest_framework import serializers

from profiles.models import LoyaltySetting, ReceiptSetting, UserGeneralSetting

class LoyaltySettingViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = LoyaltySetting
        fields = ('value',)


class ReceiptSettingListSerializer(serializers.ModelSerializer):

    store_name = serializers.ReadOnlyField(source='store.name')
    class Meta:
        model = ReceiptSetting
        fields = (
            'store_name',
            'reg_no'
        )

class ReceiptSettingViewSerializer(serializers.ModelSerializer):

    store_name = serializers.ReadOnlyField(source='store.name')
    class Meta:
        model = ReceiptSetting
        fields = (
            'store_name', 
            'header1', 
            'header2', 
            'header3', 
            'header4', 
            'header5', 
            'header6',

            'footer1', 
            'footer2', 
            'footer3', 
            'footer4', 
            'footer5', 
            'footer6', 
        )


class UserGeneralSettingViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGeneralSetting
        fields = (
            'enable_shifts',
            'enable_open_tickets',
            'enable_low_stock_notifications', 
            'enable_negative_stock_alerts'
        )