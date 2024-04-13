from rest_framework import serializers

from stores.models import Category

class LeanCategoryListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('name', 'reg_no',)

class CategoryListSerializer(serializers.ModelSerializer):

    product_count = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()
    
    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        super().__init__(*args, **kwargs)



    class Meta:
        model = Category
        fields = ('name', 'color_code', 'product_count', 'reg_no',)
        
    
    def validate_name(self, name):
        
        # Check if the user already has a category with the same name
        category_exists = Category.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exists()
            
        if category_exists:
            
            msg = 'You already have a category with this name.'
            raise serializers.ValidationError(msg)

        return name


class CategoryEditViewSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        
        self.current_user_profile = kwargs.pop('current_user_profile')
        self.category_reg_no = kwargs.pop('category_reg_no')
        super().__init__(*args, **kwargs)

    product_count = serializers.ReadOnlyField()
    reg_no = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ('name', 'color_code', 'product_count', 'reg_no') 

    def validate_name(self, name):
        
        # Check if the user already has a category (other than this one) with the same name
        category_exists = Category.objects.filter(
            profile=self.current_user_profile,
            name=name
        ).exclude(reg_no=self.category_reg_no).exists()
            
        if category_exists:
            msg = 'You already have a category with this name.'
            raise serializers.ValidationError(msg)

        return name