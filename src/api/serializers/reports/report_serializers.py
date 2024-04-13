from pprint import pprint
from django.contrib.auth import get_user_model

from rest_framework import serializers
from core.utils.list_utils import ListUtils
from products.models import Modifier, Product

from profiles.models import Profile
from stores.models import Category, Discount, StorePaymentMethod, Tax

class SaleSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ()

    def to_representation(self, instance):
        context = super().to_representation(instance)

        context['total_sales_data'] = self.context['total_sales_data']
        context['sales_data'] = self.context['sales_data']
        context['users'] = self.context['users']
        context['stores'] = self.context['stores']
       
        return context

class UserReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
        
    class Meta:
        model = get_user_model()
        fields = ('report_data', )
        
    
    def get_report_data(self, obj) -> list:

        return obj.get_report_data(
            self.user.get_user_timezone(),
            date_after=self.date_after, 
            date_before=self.date_before, 
            store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no)
        )


class CategoryReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')
        self.user_reg_no = kwargs.pop('user_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = Category
        fields = ('report_data', )
        
    def get_report_data(self, obj) -> list:

        return obj.get_report_data(
            self.user.get_user_timezone(),
            date_after=self.date_after, 
            date_before=self.date_before, 
            store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no),
            user_reg_nos=ListUtils.extract_numbers_from_string(self.user_reg_no)
        )

class DiscountReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')
        self.user_reg_no = kwargs.pop('user_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
    class Meta:
        model = Discount
        fields = ('report_data', )
        
    
    def get_report_data(self, obj) -> list:

        return obj.get_report_data(
            self.user.get_user_timezone(),
            date_after=self.date_after, 
            date_before=self.date_before, 
            store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no),
            user_reg_nos=ListUtils.extract_numbers_from_string(self.user_reg_no)
        )

class TaxReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')
        self.user_reg_no = kwargs.pop('user_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
    class Meta:
        model = Tax
        fields = ('report_data', )
        
    
    def get_report_data(self, obj) -> list:

        return obj.get_report_data(
            self.user.get_user_timezone(),
            date_after=self.date_after, 
            date_before=self.date_before, 
            store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no),
            user_reg_nos=ListUtils.extract_numbers_from_string(self.user_reg_no)
        )

class ProductReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')
        self.user_reg_no = kwargs.pop('user_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)
    class Meta:
        model = Product
        fields = ('report_data', )
        
    def get_report_data(self, obj) -> list:

        # return obj.get_report_data(
        #     self.user.get_user_timezone(),
        #     date_after=self.date_after, 
        #     date_before=self.date_before, 
        #     store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no),
        #     user_reg_nos=ListUtils.extract_numbers_from_string(self.user_reg_no)
        # )

        return {
                'is_variant': False, 
                'product_data': {
                    'name': "Product 1",
                    'items_sold': '7', 
                    'net_sales': '17500.00',
                    'cost': '7000.00',  
                    'profit': '10500.00'
                }, 
                'variant_data': []
            }

class ModifierReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')
        self.user_reg_no = kwargs.pop('user_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)


    class Meta:
        model = Modifier
        fields = ('report_data', )
        
    def get_report_data(self, obj) -> list:

        return obj.get_report_data(
            self.user.get_user_timezone(),
            date_after=self.date_after, 
            date_before=self.date_before, 
            store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no),
            user_reg_nos=ListUtils.extract_numbers_from_string(self.user_reg_no)
        )


class StorePaymentMethodReportListSerializer(serializers.ModelSerializer):

    report_data = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):

        self.date_after = kwargs.pop('date_after')
        self.date_before = kwargs.pop('date_before')
        self.store_reg_no = kwargs.pop('store_reg_no')
        self.user_reg_no = kwargs.pop('user_reg_no')

        super().__init__(*args, **kwargs)

        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    class Meta:
        model = StorePaymentMethod
        fields = ('report_data', )
        
    def get_report_data(self, obj) -> list:

        return obj.get_report_data(
            self.user.get_user_timezone(),
            date_after=self.date_after, 
            date_before=self.date_before, 
            store_reg_nos=ListUtils.extract_numbers_from_string(self.store_reg_no),
            user_reg_nos=ListUtils.extract_numbers_from_string(self.user_reg_no)
        )
       