from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import DeviceDataLog, DeviceRawData, ModuleDataLog


@admin.register(DeviceDataLog)
class DeviceDataLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_token', 'device', 'created_date', 'ip')
    list_filter = ('device',)
    readonly_fields = ('id', 'created_date', 'ip')
    fieldsets = (
        (_('Main'), {'fields': [('id', 'created_date',),
                                ('device', 'ip')]}),
        (_('Data'), {'classes': ('collapse',),
                     'fields': [('beer_temp', 'fridge_temp', 'room_temp'),
                                ('aux_temp', 'gravity', 'pressure'),
                                ('tilt', 'voltage', 'rssi')]}),
    )

    def device_token(self, obj):
         return obj.device.token


@admin.register(DeviceRawData)
class DeviceRawDataAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'date', 'ip', 'url')
    list_filter = ('token',)
    readonly_fields = ('id', 'date', 'ip')
    fieldsets = (
        (_('Main'), {'fields': [('id', 'date',),
                                ('token', 'ip')]}),
        (_('Data'), {'fields': [('hostname', 'url', 'user_agent'),
                                ('body',),
                                ('referer',)]}),
    )


@admin.register(ModuleDataLog)
class ModuleDataLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'module_token', 'module', 'timestamp', 'date')
    list_filter = ('module',)
    readonly_fields = ('id', 'timestamp', 'date', 'sensor_id', 'chip_id', 'version', 'temperature', 'relay_state')
    fieldsets = (
        (_('Main'), {'fields': [('id', 'timestamp', 'module', 'date')]}),
        (_('Data'), {'fields': [('temperature', 'relay_state'),
                                ('sensor_id', 'chip_id', 'version')]}),
    )

    def module_token(self, obj):
         return obj.module.token
