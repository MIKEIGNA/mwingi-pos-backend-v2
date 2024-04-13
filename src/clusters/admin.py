from django.contrib import admin

from .models import StoreCluster

                                     
class StoreClusterAdmin(admin.ModelAdmin):
    readonly_fields = ('reg_no',)
    # list_display = ('name', '__str__', 'profile')
    fieldsets = []

admin.site.register(StoreCluster, StoreClusterAdmin)

