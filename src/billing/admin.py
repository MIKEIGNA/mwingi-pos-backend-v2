from django.contrib import admin
from .models import Subscription, Payment
from core.mixins.log_entry_mixin import AdminUserActivityLogMixin

class SubscriptionAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):

    readonly_fields = ('employee_profile', 'days_to_go')
    
    fieldsets = [
            (None, {'fields': (
                'employee_profile', 
                'days_to_go', 
                'expired', 
                'due_date', 
                'last_payment_date')})]
    
    list_display = (
        '__str__', 
        'get_employee_profile_reg_no', 
        'get_profile', 
        'expired', 
        'get_admin_due_date', 
        'get_admin_last_payment_date', 
        'days_to_go')
    
    def has_delete_permission(self, request, obj=None):
        """ Disable delete button/action from this admin """
        return True
    
    def has_add_permission(self, request):
        """ Disable add button/action from this admin """
        return True

    def get_queryset(self, request):
        return super().get_queryset(request
        ).prefetch_related('employee_profile__profile__user')
    

    
admin.site.register(Subscription, SubscriptionAdmin)

class PaymentAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    
    readonly_fields = ([f.name for f in Payment._meta.fields] + 
                       ['show_paymentlog_id_link', ])
    
    fieldsets = [
            (None, {'fields': (
                'show_paymentlog_id_link', 
                'amount', 
                'payed_date', 
                'parent_reg_no', 
                'duration', 
                'account_reg_no', 
                'account_type')})
    ]
    
    list_filter = ['amount', 'payed_date', 'account_reg_no']
    list_display = ('__str__', 'amount', 'get_payed_date', 'duration', 'account_reg_no' ,)
    
    
    def has_delete_permission(self, request, obj=None):
        """ Disable delete button/action from this admin """
        return False
    
    def has_add_permission(self, request):
        """ Disable add button/action from this admin """
        return True
    
admin.site.register(Payment, PaymentAdmin)

