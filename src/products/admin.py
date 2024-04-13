from django.contrib import admin

from core.mixins.log_entry_mixin import AdminUserActivityLogMixin
from inventories.models import StockLevel

from .models import (
    Product, 
    ProductVariant, 
    ProductBundle ,
    Modifier, 
    ModifierOption,
    ProductProductionMap
)

class StockLevelLineAdminInline(admin.TabularInline):
    model = StockLevel

class ProductBundleAdminInline(admin.TabularInline):
    model = ProductBundle

class ProductProductionMapAdminInline(admin.TabularInline):
    model = ProductProductionMap

class ProductAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    list_filter = ("profile",)
    ordering = ('name',)
    readonly_fields = ('reg_no',)
    list_display = (
        '__str__', 
        'profile', 
        'price', 
        'cost', 
        'loyverse_variant_id', 
        'reg_no',
        'is_transformable',
        'is_deleted'

    )
    fieldsets = []

    inlines = [
        ProductBundleAdminInline, 
        StockLevelLineAdminInline, 
        ProductProductionMapAdminInline
    ]

    actions = [
        "call_save_method",
        'mark_as_transformable_method',
        'unmark_as_transformable_method',
        'recalculate_production',
        "soft_delete_selected"
    ] 

    @admin.action(description="Call save method")
    def call_save_method(self, request, queryset):
        for q in queryset:
            q.save()

    @admin.action(description="Mark as transformable")
    def mark_as_transformable_method(self, request, queryset):
        for q in queryset:
            q.is_transformable=True
            q.save()

    @admin.action(description="Unmark as transformable")
    def unmark_as_transformable_method(self, request, queryset):
        for q in queryset:
            q.is_transformable=False
            q.save()

    @admin.action(description="Recalulate productions")
    def recalculate_production(self, request, queryset):
        for q in queryset:
            q.production_count=q.productions.all().count()
            q.save()

    @admin.action(description="Soft delete selected")
    def soft_delete_selected(self, request, queryset):
        for q in queryset:
            q.soft_delete()

    

admin.site.register(Product, ProductAdmin)


class ProductBundleAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    list_filter = ("product_bundle__profile",)
    list_display = ('__str__', 'quantity')
    fieldsets = []

admin.site.register(ProductBundle, ProductBundleAdmin)


class ProductVariantAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    list_display = ('__str__',)
    fieldsets = []

admin.site.register(ProductVariant, ProductVariantAdmin)


class ModifierOptionAdminInline(admin.TabularInline):
    readonly_fields = ('reg_no',)

    model = ModifierOption
    max_num = 10

class ModifierAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'reg_no', 'get_store_count')
    fieldsets = []

    inlines = [ModifierOptionAdminInline,]

admin.site.register(Modifier, ModifierAdmin)


