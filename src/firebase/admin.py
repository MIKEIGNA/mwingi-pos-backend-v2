from django.contrib import admin

from .models import FirebaseDevice


class FirebaseDeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_current_active') 

admin.site.register(FirebaseDevice, FirebaseDeviceAdmin) 

