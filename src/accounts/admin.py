from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from accounts.create_permissions import CreatePermission

from core.mixins.log_entry_mixin import AdminUserActivityLogMixin
from profiles.models import Profile

from .models import UserChannelRecord, UserGroup, WebSocketTicket, ResetPasswordToken

from .utils.user_type import TOP_USER, USER_TYPE_CHOICES

from .forms import UserCreationAdminForm

User = get_user_model()


class UserAdmin(AdminUserActivityLogMixin, BaseUserAdmin):
    # The forms to add and change user instances
    add_form = UserCreationAdminForm

    readonly_fields = ('get_user_type',)
        
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        'full_name', 
        'email', 
        'phone', 
        'user_type', 
        'gender',
        'reg_no', 
        'loyverse_employee_id',
        'loyverse_store_id', 
        'is_superuser',
        'is_staff', 
        'is_active')
    list_filter = ('is_staff','user_type')
    fieldsets = (
            ('Personal info', {'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'get_user_type',
                'loyverse_employee_id',)}),
            ('Permissions', {'fields': ('is_active', 'is_staff', 'groups',)}),
            )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
            (None, {
                    'classes': ('wide',),
                    'fields': (
                        'first_name', 
                        'last_name', 
                        'email', 
                        'phone', 
                        'user_type', 
                        
                        'password1', 
                        'password2')}
    ),
    )
    search_fields = ('email','loyverse_employee_id')
    ordering = ('email',)
    filter_horizontal = ()

    actions = [
        "clear_user_perms_method",
        'create_api_user_for_profile'
    ] 

    def get_user_type(self, obj):
        return USER_TYPE_CHOICES[obj.user_type][1].title()
    get_user_type.short_description = "User type"

    @admin.action(description='Clear user perms')
    def clear_user_perms_method(self, request, queryset):
        for q in queryset:
            q.clear_user_perms()


    @admin.action(description="Call save method")
    def call_save_method(self, request, queryset):
        for q in queryset:
            q.save()

            # Create Profile
            if q.user_type == TOP_USER:
                
                Profile.objects.get_or_create(
                    user=q,
                    # phone=q.phone,
                    reg_no=q.reg_no
                ) # Create Profile

    @admin.action(description="Create API user for profile")
    def create_api_user_for_profile(self, request, queryset):
        queryset = queryset.filter(user_type=TOP_USER)
        for q in queryset:
            q.create_api_user()


admin.site.register(User, UserAdmin)
    
         
class UserChannelRecordAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    list_display = ('user', 'is_api', 'channel_name',)

admin.site.register(UserChannelRecord, UserChannelRecordAdmin)

class WebSocketTicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'reg_no')

admin.site.register(WebSocketTicket, WebSocketTicketAdmin)


class ResetPasswordTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key')

admin.site.register(ResetPasswordToken, ResetPasswordTokenAdmin)


class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('master_user', 'ident_name', 'reg_no', 'get_all_perms')


    search_fields = ('name',)
    ordering = ('name',)
    filter_horizontal = ('permissions',)

    actions = [
        'update_perms'
    ]

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'permissions':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            # Avoid a major performance hit resolving permission names which
            # triggers a content_type load:
            kwargs['queryset'] = qs.select_related('content_type')
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)
    
    @admin.action(description='Update perms')
    def update_perms(self, request, queryset):
        CreatePermission.create_permissions()
        for q in queryset:
            q.update_perms()

admin.site.register(UserGroup, UserGroupAdmin)




