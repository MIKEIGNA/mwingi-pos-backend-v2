from rest_framework import serializers

from accounts.models import UserGroup


class LeanRoleListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = (
            'ident_name',
            'reg_no', 
        )
        

class RoleListCreateSerializer(serializers.ModelSerializer):

    can_view_shift_reports = serializers.BooleanField(required=True, write_only=True)
    can_manage_open_tickets = serializers.BooleanField(required=True, write_only=True)
    can_void_open_ticket_items = serializers.BooleanField(required=True, write_only=True)
    can_manage_items = serializers.BooleanField(required=True, write_only=True)
    can_refund_sale = serializers.BooleanField(required=True, write_only=True)
    can_open_drawer = serializers.BooleanField(required=True, write_only=True)
    can_reprint_receipt = serializers.BooleanField(required=True, write_only=True)
    can_change_settings = serializers.BooleanField(required=True, write_only=True)
    can_apply_discount = serializers.BooleanField(required=True, write_only=True)
    can_change_taxes = serializers.BooleanField(required=True, write_only=True)
    can_accept_debt = serializers.BooleanField(required=True, write_only=True)
    can_manage_customers = serializers.BooleanField(required=True, write_only=True)
    can_manage_employees = serializers.BooleanField(required=True, write_only=True)
    can_change_general_settings = serializers.BooleanField(required=True, write_only=True)

    reg_no = serializers.ReadOnlyField()
    employee_count = serializers.ReadOnlyField(source='get_employee_count')

    def __init__(self, *args, **kwargs):
        
        self.current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)

    class Meta:
        model = UserGroup
        fields = (
            'ident_name',
            'can_view_shift_reports',
            'can_manage_open_tickets',
            'can_void_open_ticket_items',
            'can_manage_items',
            'can_refund_sale',
            'can_open_drawer',
            'can_reprint_receipt',
            'can_change_settings',
            'can_apply_discount',
            'can_change_taxes',
            'can_accept_debt',
            'can_manage_customers',
            'can_manage_employees',
            'can_change_general_settings', 
            'reg_no', 
            'employee_count'
        )
        
    
    def validate_ident_name(self, ident_name):
        
        # Check if the user already has a group with the same name
        role_exists = UserGroup.objects.filter(
            master_user=self.current_user,
            ident_name=ident_name
        ).exists()
 
        if role_exists:
            
            msg = 'You already have a role with this name.'
            raise serializers.ValidationError(msg)

        return ident_name


class RoleEditViewSerializer(serializers.ModelSerializer):

    can_view_shift_reports = serializers.BooleanField(required=True, write_only=True)
    can_manage_open_tickets = serializers.BooleanField(required=True, write_only=True)
    can_void_open_ticket_items = serializers.BooleanField(required=True, write_only=True)
    can_manage_items = serializers.BooleanField(required=True, write_only=True)
    can_refund_sale = serializers.BooleanField(required=True, write_only=True)
    can_open_drawer = serializers.BooleanField(required=True, write_only=True)
    can_reprint_receipt = serializers.BooleanField(required=True, write_only=True)
    can_change_settings = serializers.BooleanField(required=True, write_only=True)
    can_apply_discount = serializers.BooleanField(required=True, write_only=True)
    can_change_taxes = serializers.BooleanField(required=True, write_only=True)
    can_accept_debt = serializers.BooleanField(required=True, write_only=True)
    can_manage_customers = serializers.BooleanField(required=True, write_only=True)
    can_manage_employees = serializers.BooleanField(required=True, write_only=True)
    can_change_general_settings = serializers.BooleanField(required=True, write_only=True)

    reg_no = serializers.ReadOnlyField()
    perms_state = serializers.ReadOnlyField(source='get_user_permissions_state')

    def __init__(self, *args, **kwargs):
        
        self.current_user = kwargs.pop('current_user')
        self.group_reg_no = kwargs.pop('group_reg_no')

        super().__init__(*args, **kwargs)


    class Meta:
        model = UserGroup
        fields = (
            'ident_name',
            'can_view_shift_reports',
            'can_manage_open_tickets',
            'can_void_open_ticket_items',
            'can_manage_items',
            'can_refund_sale',
            'can_open_drawer',
            'can_reprint_receipt',
            'can_change_settings',
            'can_apply_discount',
            'can_change_taxes',
            'can_accept_debt',
            'can_manage_customers',
            'can_manage_employees',
            'can_change_general_settings', 
            'reg_no', 
            'perms_state'
        )

    def validate_ident_name(self, ident_name):
        
        # Check if the user already has a group with the same name
        role_exists = UserGroup.objects.filter(
            master_user=self.current_user,
            ident_name=ident_name
        ).exclude(reg_no=self.group_reg_no).exists()
 
        if role_exists:
            
            msg = 'You already have a role with this name.'
            raise serializers.ValidationError(msg)

        return ident_name