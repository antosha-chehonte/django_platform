from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Departments, Postname
from apps.hr.models import Posts


@admin.register(Departments)
class DepartmentsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'parent')
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'description')
        }),
        ('Иерархия', {
            'fields': ('parent',)
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def has_delete_permission(self, request, obj=None):
        if obj and Posts.objects.filter(department=obj).exists():
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        if change and not form.cleaned_data.get('is_active', obj.is_active):
            if Posts.objects.filter(department=obj).exists():
                messages.error(request, _('Нельзя деактивировать подразделение: существуют связанные позиции.'))
                return
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Исключаем текущий объект из списка возможных родителей при редактировании
        if obj:
            form.base_fields['parent'].queryset = Departments.objects.exclude(pk=obj.pk)
        return form


@admin.register(Postname)
class PostnameAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'code', 'description', 'category')
    list_editable = ('is_active',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'description')
        }),
        ('Категория', {
            'fields': ('category',)
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def has_delete_permission(self, request, obj=None):
        if obj and Posts.objects.filter(postname=obj).exists():
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        if change and not form.cleaned_data.get('is_active', obj.is_active):
            if Posts.objects.filter(postname=obj).exists():
                messages.error(request, _('Нельзя деактивировать должность: существуют связанные позиции.'))
                return
        super().save_model(request, obj, form, change)
