from django.contrib import admin
from accounts.tasks import receipt_change_stock_tasks
from core.mixins.log_entry_mixin import AdminUserActivityLogMixin
from products.models import ModifierOption

from sales.models import Receipt, ReceiptLine, ReceiptPayment

class ReceiptPaymentAdminInline(admin.TabularInline):
    model = ReceiptPayment

class ReceiptLineAdminInline(admin.TabularInline):
    model = ReceiptLine

class ReceiptAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    search_fields = [
        "receipt_number",
    ]
    date_hierarchy = "created_date"  # DateField
    list_filter = ("created_date", "is_refund", "tims_success", "store", "user") 
    readonly_fields = ('reg_no', 'customer_info')
    list_display = (
        'receipt_number', 
        'changed_stock', 
        "tims_success",
        'is_refund',
        'user', 
        'get_created_date',
        'store', 
        'item_count',
        'customer', 
        'total_amount',
        'subtotal_amount', 
        'total_cost',
        "tims_cu_invoice_number",
        "tims_rel_doc_number",
        'reg_no',
        'local_reg_no',
        'loyverse_store_id'

    ) 
    fieldsets = []

    inlines = [ReceiptLineAdminInline, ReceiptPaymentAdminInline,]

    actions = [
        "call_save_method",
        "call_receipt_change_stock_tasks",
        "resave_customer_info"
    ]

    @admin.action(description="Call save method")
    def call_save_method(self, request, queryset):
        for q in queryset:
            q.save()

    @admin.action(description="Call receipt change stock tasks")
    def call_receipt_change_stock_tasks(self, request, queryset):
        receipt_change_stock_tasks.delay()

    @admin.action(description="Resave customer info")
    def resave_customer_info(self, request, queryset):
        for q in queryset:
            q.resave_customer_info()

admin.site.register(Receipt, ReceiptAdmin)


class ModifierOptionAdminInline(admin.TabularInline):
    readonly_fields = ('reg_no',)
    model = ModifierOption

class ReceiptLineAdmin(AdminUserActivityLogMixin, admin.ModelAdmin):
    date_hierarchy = "created_date"  # DateField
    list_filter = ("product", "store") 
    readonly_fields = ('reg_no',)
    list_display = ('__str__', 'user', 'store', 'tax', 'units', 'created_date')
    fieldsets = []

admin.site.register(ReceiptLine, ReceiptLineAdmin)