from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Departments, Postname, ITAsset, CertificateType
from apps.hr.models import Posts


@admin.register(Departments)
class DepartmentsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dep_short_name', 'email', 'city', 'net_id', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'parent')
    search_fields = ('name', 'code', 'description', 'dep_short_name', 'email', 'city', 'net_id')
    list_editable = ('is_active',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'dep_short_name', 'description', 'email')
        }),
        ('Адрес местонахождения', {
            'fields': ('zipcode', 'city', 'street', 'bldg'),
            'classes': ('collapse',)
        }),
        ('Сетевая информация', {
            'fields': ('net_id', 'ip', 'mask'),
            'classes': ('collapse',)
        }),
        ('Иерархия', {
            'fields': ('parent', 'sorting')
        }),
        ('Статус', {
            'fields': ('is_active', 'is_logical')
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
        
        # Сохраняем старый parent для проверки изменений
        old_parent = None
        if change and obj.pk:
            try:
                old_instance = Departments.objects.get(pk=obj.pk)
                old_parent = old_instance.parent
            except Departments.DoesNotExist:
                pass
        
        # Если sorting не заполнен, генерируем автоматически
        if not obj.sorting:
            obj.sorting = Departments.get_next_sorting_code(parent=obj.parent, exclude_pk=obj.pk)
        
        # Если parent изменился, обновляем sorting
        if old_parent != obj.parent:
            obj.sorting = Departments.get_next_sorting_code(parent=obj.parent, exclude_pk=obj.pk)
        
        super().save_model(request, obj, form, change)
        
        # Обновляем дочерние элементы после сохранения, если parent изменился
        if old_parent != obj.parent:
            obj.update_children_sorting()
    
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
    search_fields = ('name', 'name_accusative', 'code', 'description', 'category')
    list_editable = ('is_active',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('code', 'name', 'name_accusative', 'description')
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


@admin.register(ITAsset)
class ITAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description')
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


@admin.register(CertificateType)
class CertificateTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
