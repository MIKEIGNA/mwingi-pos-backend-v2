from django.contrib import admin

from loyverse.models import LoyverseAppData

# Register your models here.
class LoyverseAppDataAdmin(admin.ModelAdmin):
    list_display = (
        "access_token",
        "refresh_token",
        "receipt_anlayze_date",
        "get_updated_date",
    )
    fieldsets = []

admin.site.register(LoyverseAppData, LoyverseAppDataAdmin)