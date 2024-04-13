from __future__ import unicode_literals

from django.contrib import admin

from core.admin_utils.extended_date_filter import ExtendedDateTimeFilter
from core.mixins.log_entry_mixin import AdminUserActivityLogMixin

from .models import UserActivityLog, PaymentLog, MpesaLog, RequestTimeSeries

class UserActivityLogAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    date_hierarchy = 'action_time'
    
    readonly_fields = ([f.name for f in UserActivityLog._meta.fields] + 
                       ['the_object', 
                        'find_owner', 
                        'editor_profile', 
                        'get_edited_object'])
    
    fieldsets = [
            (None, {'fields': (
                'action_time', 
                'editor_profile', 
                'is_hijacked',
                'action_type', 
                'the_object', 
                'change_message', 
                'get_edited_object', 
                'owner_email', 
                'find_owner', 
                'object_id', 
                'ip', 
                'object_repr', 
                'panel')})]
    
    list_filter = ['is_hijacked','user', 'ip', 'panel', 'action_type', 'content_type',]
    
    list_display = (
        'action_time', 
        'user', 
        'is_hijacked',
        'action_type',
        'ip', 
        'the_object', 
        'panel')
    
admin.site.register(UserActivityLog, UserActivityLogAdmin)

class PaymentLogAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    
    readonly_fields = ([f.name for f in PaymentLog._meta.fields])
    
    fieldsets = [
            (None, {'fields': (
                'amount', 
                'reg_no', 
                'payment_method', 
                'mpesa_id', 
                'email', 
                'payment_type', 
                'duration')})]
    
    list_filter = ['email', 'duration', 'reg_no']
    list_display = (
        'email', 
        'amount', 
        'duration', 
        'payment_type', 
        'get_admin_created_date')
    
admin.site.register(PaymentLog, PaymentLogAdmin)

class MpesaLogAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    
    readonly_fields = ([f.name for f in MpesaLog._meta.fields] + 
                       ['show_paymentlog_id_link', ])

    fieldsets = [
            (None, {'fields': (
                'show_paymentlog_id_link', 
                'transaction_type', 
                'trans_amount', 
                'trans_id', 
                'trans_time', 

                'business_shortcode', 
                'bill_ref_number', 
                'invoice_number', 
                'org_account_balance', 

                'third_party_trans_id', 
                'msisdn', 
                'first_name', 
                'middle_name', 
                'last_name')})]

    list_filter = ['trans_id', 'trans_amount', 'bill_ref_number']
    
    list_display = ('trans_id', 'trans_amount', 'bill_ref_number')
         
admin.site.register(MpesaLog, MpesaLogAdmin)

class RequestTimeSeriesAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    
    readonly_fields = ([f.name for f in RequestTimeSeries._meta.fields])
    
    fieldsets = []
    
    list_filter = (
        'email', 
        'is_logged_in_as', 
        'is_logged_in_as_email', 
        'os', 
        'device_type', 
        'browser', 
        'ip_address', 
        'view_name', 
        'request_method', 
        'status_code', 
        'is_api', 
        'map_loaded',
        'was_throttled',
        'reg_no', 
        'created_date', 
        ('created_date', ExtendedDateTimeFilter))

    list_display = (
        'view_name', 
        'email', 
        'is_logged_in_as_email',
        'response_time', 
        'is_api' ,
        'is_logged_in_as')
    
admin.site.register(RequestTimeSeries, RequestTimeSeriesAdmin)





