from django.contrib import admin

from core.mixins.log_entry_mixin import AdminUserActivityLogMixin
from inventories.models.inventory_valuation_models import InventoryValuation, InventoryValuationLine

from .models import (
    InventoryCount,
    InventoryCountCount,
    InventoryCountLine,
    InventoryHistory,
    PurchaseOrder,
    PurchaseOrderCount,
    PurchaseOrderLine,
    StockAdjustment, 
    StockAdjustmentCount,
    StockAdjustmentLine, 
    StockLevel, 
    Supplier,
    TransferOrder,
    TransferOrderCount,
    TransferOrderLine,

    ProductTransform,
    ProductTransformCount,
    ProductTransformLine
)

class StockLevelAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    ordering = ('product__name',)

    list_filter = ('product__profile', 'product', 'store')
    list_display = ('units', 'store', 'product', 'inlude_in_price_calculations', 'get_product_profile')
    fieldsets = []

admin.site.register(StockLevel, StockLevelAdmin)


class SupplierAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('name', '__str__', 'profile')
    fieldsets = []

admin.site.register(Supplier, SupplierAdmin)




class StockAdjustmentLineAdminInline(admin.TabularInline):
    model = StockAdjustmentLine


class StockAdjustmentAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'get_admin_created_date', 'reg_no',)
    fieldsets = []

    inlines = [StockAdjustmentLineAdminInline,]

admin.site.register(StockAdjustment, StockAdjustmentAdmin)

class StockAdjustmentCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'increamental_id', 'reg_no',)
    fieldsets = []

admin.site.register(StockAdjustmentCount, StockAdjustmentCountAdmin)


class TransferOrderLineAdminInline(admin.TabularInline):
    model = TransferOrderLine


class TransferOrderAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'get_ordered_by', 'get_admin_created_date', 'reg_no',)
    fieldsets = []

    inlines = [TransferOrderLineAdminInline,]

admin.site.register(TransferOrder, TransferOrderAdmin)

class TransferOrderCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'increamental_id', 'reg_no',)
    fieldsets = []

admin.site.register(TransferOrderCount, TransferOrderCountAdmin)
    

class PurchaseOrderLineAdminInline(admin.TabularInline):
    model = PurchaseOrderLine

class PurchaseOrderAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'get_ordered_by', 'get_admin_created_date', 'reg_no',)
    fieldsets = []

    inlines = [PurchaseOrderLineAdminInline,]

admin.site.register(PurchaseOrder, PurchaseOrderAdmin) 


class PurchaseOrderCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'increamental_id', 'reg_no',)
    fieldsets = []

admin.site.register(PurchaseOrderCount, PurchaseOrderCountAdmin)

class InventoryCountLineAdminInline(admin.TabularInline):
    model = InventoryCountLine

class InventoryCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'get_admin_created_date', 'reg_no',)
    fieldsets = []

    inlines = [InventoryCountLineAdminInline,]

admin.site.register(InventoryCount, InventoryCountAdmin)

class InventoryCountCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'increamental_id', 'reg_no',)
    fieldsets = []

admin.site.register(InventoryCountCount, InventoryCountCountAdmin)

class InventoryHistoryAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):

    date_hierarchy = "created_date"  # DateField
    list_filter = ("product", "store", "user")
    search_fields = ('change_source_name', )

    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'product', 'reason', 'adjustment', 'stock_after', 'reg_no', 'get_admin_created_date', )
    fieldsets = []

    actions = [
        'call_model_delete_method',
        'start_recalculating_stock_afters',
        
    ]

    @admin.action(description="Recalculate inventory hisotry stock afters")
    def start_recalculating_stock_afters(self, request, queryset):
        for obj in queryset:
            obj.start_recalculating_stock_afters(should_recalculate=True)

    @admin.action(description="Call model delete method")
    def call_model_delete_method(self, request, queryset):
        for obj in queryset:
            obj.delete()

    def has_delete_permission(self, request, obj=None):
        return False 
    
admin.site.register(InventoryHistory, InventoryHistoryAdmin)



class ProductTransformLineAdminInline(admin.TabularInline):
    model = ProductTransformLine


class ProductTransformAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'get_created_by', 'get_admin_created_date', 'reg_no',)
    fieldsets = []

    inlines = [ProductTransformLineAdminInline,]

admin.site.register(ProductTransform, ProductTransformAdmin)

class ProductTransformCountAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    list_display = ('__str__',  'increamental_id', 'reg_no',)
    fieldsets = []

admin.site.register(ProductTransformCount, ProductTransformCountAdmin)




class InventoryValuationLineAdminInline(admin.TabularInline):
    ordering = ('product__name',)
    model = InventoryValuationLine

class InventoryValuationAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):

    ordering = ('store__name',)

    date_hierarchy = "created_date"  # DateField
    list_filter = ("created_date", "store", "user") 
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'get_created_date', 'reg_no',)
    fieldsets = []

    inlines = [InventoryValuationLineAdminInline,]

    actions = [
        "recalculate_inventory_valuation"
    ] 


    @admin.action(description="recalculate_inventory_valuation")
    def recalculate_inventory_valuation(self, request, queryset):
        for obj in queryset:
            lines = obj.inventoryvaluationline_set.all()

            for line in lines:
                line.recalculate_inventory_valuation_line()

admin.site.register(InventoryValuation, InventoryValuationAdmin)