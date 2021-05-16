from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Permission
from .models import *


class EortAdmin(admin.ModelAdmin):
    ordering = ['eort_id']
    search_fields = ['fm_eort_id']

class VehicleAdmin(admin.ModelAdmin):
    ordering = ['veh_id']
    search_fields = ['ikz']

class ZipAdmin(admin.ModelAdmin):
    ordering = ['zip_code']
    search_fields = ['zip_code', 'city']

class WorkshopAdmin(admin.ModelAdmin):
    ordering = ['w_id']
    search_fields = ['kuerzel', 'name', 'zip_code']


# Register your models here.
admin.site.register(WZO_User, UserAdmin)
admin.site.register(Permission)
admin.site.register(Eort, EortAdmin)
admin.site.register(Zip_Code, ZipAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Workshop, WorkshopAdmin)
admin.site.register(Allocation)
admin.site.register(RuleWT)
admin.site.register(Upload)

