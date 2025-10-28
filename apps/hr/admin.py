from django.contrib import admin
from django.utils.html import format_html

from .models import Employees, Posts, PositionHistory


@admin.register(Employees)
class EmployeesAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'middle_name', 'birth_date', 'gender', 'is_active')
    list_filter = ('is_active', 'gender')
    search_fields = ('last_name', 'first_name', 'middle_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


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


