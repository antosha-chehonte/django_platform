from django.contrib import admin
from django.utils.html import format_html

from .models import Employees, Posts, PositionHistory


@admin.register(Employees)
class EmployeesAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'birth_date', 'gender', 'work_phone', 'mobile_phone', 'ip_phone', 'status_badge', 'is_active')
    list_filter = ('status', 'is_active', 'gender')
    search_fields = ('last_name', 'first_name', 'middle_name', 'email', 'work_phone', 'mobile_phone', 'ip_phone', 'full_name_accusative')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('last_name', 'first_name', 'middle_name', 'full_name_accusative', 'birth_date', 'gender')
        }),
        ('Контакты', {
            'fields': ('work_phone', 'mobile_phone', 'ip_phone', 'email')
        }),
        ('Назначение', {
            'fields': ('appointment_date', 'appointment_order_date', 'appointment_order_number')
        }),
        ('Статус', {
            'fields': ('status', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj: Employees):
        if obj.status == Employees.STATUS_ACTIVE:
            color = '#198754'  # bootstrap success
        elif obj.status == Employees.STATUS_DISMISSED:
            color = '#dc3545'  # bootstrap danger
        elif obj.status == Employees.STATUS_TEMPORARY_ABSENCE:
            color = '#ffc107'  # bootstrap warning
        else:
            color = '#6c757d'  # bootstrap secondary
        label = obj.get_status_display()
        return format_html('<span style="padding:2px 8px;border-radius:12px;background:{};color:#fff;">{}</span>', color, label)

    status_badge.short_description = 'Статус'


@admin.register(Posts)
class PostsAdmin(admin.ModelAdmin):
    list_display = ('department', 'postname', 'status_badge', 'employee', 'is_active', 'updated_at')
    list_filter = ('status', 'is_active', 'department', 'postname')
    search_fields = ('department__name', 'postname__name', 'employee__last_name', 'employee__first_name')
    readonly_fields = ('created_at', 'updated_at')

    def status_badge(self, obj: Posts):
        if obj.status == Posts.STATUS_OCCUPIED:
            color = '#198754'  # bootstrap success
            label = 'Занята'
        else:
            color = '#dc3545'  # bootstrap danger
            label = 'Вакантна'
        return format_html('<span style="padding:2px 8px;border-radius:12px;background:{};color:#fff;">{}</span>', color, label)

    status_badge.short_description = 'Статус'


@admin.register(PositionHistory)
class PositionHistoryAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'employee', 'post', 'action', 'start_date', 'end_date')
    list_filter = ('action', 'start_date', 'end_date', 'post__department', 'post__postname')
    search_fields = ('employee__last_name', 'employee__first_name', 'post__department__name', 'post__postname__name')
    readonly_fields = ('created_at',)


