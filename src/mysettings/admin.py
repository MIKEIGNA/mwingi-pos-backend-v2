from django.contrib import admin

from core.mixins.log_entry_mixin import AdminUserActivityLogMixin

from .models import MySetting

class MySettingAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):

    readonly_fields = ('name',)
    fieldsets = [
            (None, {'fields': (
                'name', 
                'reset_tokens', 
                'signups', 
                'maintenance', 
                'allow_contact', 
                'delete_sessions', 
                'accept_payments', 
                'accept_mpesa', 
                'new_employee',
                'new_product',
                'new_customer',
                'new_sale',
                'receipt_change_stock_task_running')})]
    
    list_display = (
        '__str__', 
        'signups', 
        'maintenance', 
        'accept_payments', 
        'accept_mpesa', 
        'new_employee',
        'receipt_change_stock_task_running'
    )
    
    def has_delete_permission(self, request, obj=None):
        """ Disable delete button/action from this admin """
        return False
    
    def has_add_permission(self, request):
        """ Disable add button/action from this admin """
        return False
    
    
admin.site.register(MySetting, MySettingAdmin)

