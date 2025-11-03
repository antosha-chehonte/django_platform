from django.contrib import admin
from django.utils.html import format_html
from .models import SystemAccess, DigitalSignature


@admin.register(SystemAccess)
class SystemAccessAdmin(admin.ModelAdmin):
    list_display = ('employee', 'system', 'login', 'status', 'access_granted_date', 'access_blocked_date', 'created_at')
    list_filter = ('status', 'system', 'access_granted_date')
    search_fields = ('employee__last_name', 'employee__first_name', 'employee__middle_name', 'login', 'system__name', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'system')


@admin.register(DigitalSignature)
class DigitalSignatureAdmin(admin.ModelAdmin):
    list_display = ('employee', 'certificate_type', 'certificate_serial', 'expiry_date', 'status', 'has_file', 'created_at')
    list_filter = ('status', 'certificate_type', 'expiry_date')
    search_fields = (
        'employee__last_name', 'employee__first_name', 'employee__middle_name',
        'certificate_serial', 'certificate_alias', 'carrier_serial', 'notes'
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'certificate_type')
    
    def has_file(self, obj):
        """Проверка наличия файла"""
        return bool(obj.certificate_file)
    has_file.boolean = True
    has_file.short_description = 'Файл загружен'

