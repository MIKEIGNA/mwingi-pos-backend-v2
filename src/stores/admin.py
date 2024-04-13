from django.contrib import admin
from accounts.tasks.local_midnight_task import local_midnight_tasks

from core.mixins.log_entry_mixin import AdminUserActivityLogMixin
from profiles.models import ReceiptSetting

from stores.models import Store, Category, Discount, StorePaymentMethod, Tax


class ReceiptSettingAdminInline(admin.StackedInline):
    max_num = 1
    readonly_fields = ('reg_no',)
    model = ReceiptSetting

class StoreAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    ordering = ('name',)
    list_filter = ("profile",)
    readonly_fields = ('reg_no',)
    list_display = ('name', 'is_shop', 'is_truck', 'profile', 'till_number', 'reg_no', 'loyverse_store_id')
    fieldsets = []

    inlines = [ReceiptSettingAdminInline]

    actions = [
        "call_create_stock_levels_method",
        "call_save_method" ,
        "create_inventory_valuations",
        "soft_delete_selected"
    ] 

    @admin.action(description="Call stock_levels method")
    def call_create_stock_levels_method(self, request, queryset):
        for q in queryset:
            q.create_stock_levels_for_all_products()

    @admin.action(description="Call save method")
    def call_save_method(self, request, queryset):
        for q in queryset:
            q.save()

    @admin.action(description="create inventory valuations")
    def create_inventory_valuations(self, request, queryset):
        local_midnight_tasks.delay()

    @admin.action(description="Soft delete selected")
    def soft_delete_selected(self, request, queryset):
        for q in queryset:
            q.soft_delete()

admin.site.register(Store, StoreAdmin)

class StorePaymentMethodAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'profile', 'payment_type', 'reg_no')
    fieldsets = []

admin.site.register(StorePaymentMethod, StorePaymentMethodAdmin)


class CategoryAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'reg_no', 'color_code')
    fieldsets = []

admin.site.register(Category, CategoryAdmin)


class DiscountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'value')
    fieldsets = []

admin.site.register(Discount, DiscountAdmin)

class TaxAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'rate')
    fieldsets = []

admin.site.register(Tax, TaxAdmin)


