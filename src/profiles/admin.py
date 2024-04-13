from django.contrib import admin
from django.urls import reverse_lazy
from django.utils.html import format_html

from accounts.utils.user_type import TOP_USER
from core.mixins.log_entry_mixin import AdminUserActivityLogMixin

from .forms import ProfileAdminForm 
from .admin_helpers import ProfileAdminPaymentActionMixin

from .models import (
    LoyaltySetting,
    ReceiptSetting,
    Profile, 
    ProfileCount,
    EmployeeProfile,
    EmployeeProfileCount,
    Customer,
    CustomerCount,
    UserGeneralSetting
)

class ProfileAdmin(
    AdminUserActivityLogMixin, 
    #HijackUserAdminMixin, 
    ProfileAdminPaymentActionMixin, 
    admin.ModelAdmin):

    form = ProfileAdminForm

    date_hierarchy = 'join_date'
    empty_value_display = '-empty-'
    # readonly_fields = ('user', 'join_date', 'reg_no',)

    fieldsets = [
            (None, {'fields': (
                'user',
                'image',  
                'join_date', 
                'phone',  
                'business_name',
                'location', 
                'currency',  
                'approved')})]

    list_display = ('get_full_name', 'user', 'reg_no', 'get_admin_join_date', 'approved')
    list_filter = ['join_date']


    def get_actions(self, request):
        """ Disable delete_selected action from this admin """
        actions = super().get_actions(request)

        # Show make payment actions
        self.show_make_payment_actions(request)
     
        return actions

    def show_make_payment_actions(self, request):
        """ Only show make payment options to superuser """

        if request.user.is_superuser:

            # This actions have been provided by ProfileAdminPaymentActionMixin
            payment_actions = [
                'make_payment_for_1_month', 
                'make_payment_for_6_months', 
                'make_payment_for_1_year']

            self.actions = self.actions + payment_actions

        else:
            # To avoid the django admin cache, we empty actions when we are not
            # supposed to show any
            self.actions = []

        return False

    def has_delete_permission(self, request, obj=None):
        """ Disable delete button/action from this admin """
        return True

    def has_add_permission(self, request):
        """ Disable add button/action from this admin """
        return False

admin.site.register(Profile, ProfileAdmin)

class ProfileCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['profile', 'created_date']})]
    list_display = ('profile', 'get_admin_created_date',)

    def get_queryset(self, request):
        return super().get_queryset(request
        ).prefetch_related('profile__user',)

admin.site.register(ProfileCount, ProfileCountAdmin)





class EmployeeProfileAdmin(
    AdminUserActivityLogMixin, 
    #HijackUserAdminMixin, 
    #EmployeeProfileAdminPaymentActionMixin,
    admin.ModelAdmin):
    
    form = ProfileAdminForm

    ordering = ('user__first_name',) 
    
    readonly_fields = ('user', 'profile', 'image', 'reg_no',)

    fieldsets = [] 

    list_display = (
        'get_full_name', 
        'user', 
        'profile', 
        'reg_no', 
        'loyverse_store_id',
        'get_admin_join_date') 
    
    list_filter = ['join_date']

    actions = [
        "create_api_user_for_profile",
    ]

    def get_actions(self, request):
        """ Disable delete_selected action from this admin """
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']

        # Only show make payment options to superuser
        if request.user.is_superuser:

            # This actions have been provided by ProfileAdminPaymentActionMixin
            payment_actions = [
                'make_payment_for_1_month', 
                'make_payment_for_6_months', 
                'make_payment_for_1_year']

            self.actions = self.actions + payment_actions

        else:
            # To avoid the django admin cache, we empty actions when we are not
            # supposed to show any
            self.actions = []

        return actions

    def has_add_permission(self, request):
        """ Disable add button/action from this admin """
        return False

    def get_queryset(self, request):
        return super().get_queryset(request
        ).prefetch_related(
            'profile__user',
            'user',
        )
    
    @admin.action(description="Create API user for profile")
    def create_api_user_for_profile(self, request, queryset):
        queryset = queryset.filter(user_type=TOP_USER)
        for q in queryset:
            q.create_api_user()
           
admin.site.register(EmployeeProfile, EmployeeProfileAdmin)

class EmployeeProfileCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['team_profile', 'created_date']})]
    list_display = (
        'profile', 
        'employee_profile', 
        'get_admin_created_date',
    )

    def get_queryset(self, request):
        return super().get_queryset(request
        ).prefetch_related(
            'profile__user', 
            'user',)

admin.site.register(EmployeeProfileCount, EmployeeProfileCountAdmin)



class CustomerAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    search_fields = ('name',)
    readonly_fields = ('reg_no',)
    list_display = ('name', '__str__', 'profile')
    fieldsets = []

    actions = [
        "call_save_method",
    ]

    @admin.action(description="Call save method")
    def call_save_method(self, request, queryset):
        for q in queryset:
            q.save()

admin.site.register(Customer, CustomerAdmin)


class LoyaltySettingAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    list_display = ('profile', 'value')
    fieldsets = []

admin.site.register(LoyaltySetting, LoyaltySettingAdmin)

class ReceiptSettingAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    list_display = ('profile', 'store', 'header1', 'footer1')
    fieldsets = []

admin.site.register(ReceiptSetting, ReceiptSettingAdmin)



class UserGeneralSettingAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'profile')
    fieldsets = []

admin.site.register(UserGeneralSetting, UserGeneralSettingAdmin)

