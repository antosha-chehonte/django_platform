# План реализации функционала отчетов для приложения управления доступом

## 📋 Общая концепция

Реализация системы отчетов для анализа и контроля доступов к информационным системам и цифровых подписей сотрудников. Отчеты должны поддерживать группировку по подразделениям и экспорт в различные форматы.

---

## 🎯 Список отчетов

### 1. Отчеты для доступа к системам

#### 1.1. Список активных доступов к системе X (с группировкой по подразделениям)
**Назначение:** Получить список всех активных доступов к выбранной информационной системе, сгруппированных по подразделениям сотрудников.

**Параметры:**
- Система (обязательный, выбор из ITAsset)
- Статус доступа (по умолчанию: активные)
- Фильтр по подразделению (опционально)

**Выводимые данные:**
- Подразделение
- ФИО сотрудника
- Должность
- Логин
- Дата получения доступа
- Статус
- Дата блокировки (если есть)

**Группировка:** По подразделениям (через Posts -> Departments)

#### 1.2. Отчет о просроченных/истекающих доступах (требующих актуализации)
**Назначение:** Выявить доступы, требующие внимания и актуализации.

**Параметры:**
- Тип отчета:
  - Доступы со статусом "требует актуализации"
  - Доступы с датой блокировки в прошлом (просроченные)
  - Доступы с датой блокировки в ближайшие N дней (истекающие)
- Период для "истекающих" (по умолчанию: 40 дней)

**Выводимые данные:**
- Подразделение
- ФИО сотрудника
- Система
- Логин
- Статус
- Дата получения доступа
- Дата блокировки
- Дней до блокировки / дней просрочено

### 2. Отчеты для цифровых подписей

#### 2.1. Список сотрудников с активной цифровой подписью (с группировкой по подразделениям)
**Назначение:** Получить полный список сотрудников, имеющих активную цифровую подпись.

**Параметры:**
- Тип сертификата (опционально)
- Статус подписи (по умолчанию: активные)
- Фильтр по подразделению (опционально)

**Выводимые данные:**
- Подразделение
- ФИО сотрудника
- Должность
- Тип сертификата
- Серийный номер сертификата
- Отпечаток (alias)
- Дата окончания срока действия
- Статус (истек/активен)

**Группировка:** По подразделениям

#### 2.2. Список сотрудников без цифровой подписи (с группировкой по подразделениям)
**Назначение:** Выявить сотрудников, у которых отсутствует активная цифровая подпись.

**Параметры:**
- Фильтр по подразделению (опционально)
- Только активные сотрудники (по умолчанию: да)

**Выводимые данные:**
- Подразделение
- ФИО сотрудника
- Должность
- Email
- Телефон
- Дата последней проверки (опционально)

**Логика:** 
- Найти всех активных сотрудников (Employees.is_active=True)
- Исключить тех, у кого есть активная цифровая подпись (DigitalSignature.status='active')
- Сгруппировать по подразделениям через Posts

#### 2.3. Отчет об истекающих сертификатах
**Назначение:** Выявить сертификаты, срок действия которых истекает в ближайшее время.

**Параметры:**
- Период истечения (по умолчанию: 40 дней)
- Только активные сертификаты (по умолчанию: да)
- Фильтр по подразделению (опционально)

**Выводимые данные:**
- Подразделение
- ФИО сотрудника
- Должность
- Тип сертификата
- Серийный номер сертификата
- Дата окончания срока действия
- Дней до истечения
- Статус

**Логика:** Найти сертификаты, где expiry_date находится в диапазоне [сегодня, сегодня + N дней]

### 3. Экспорт отчетов

**Форматы экспорта:**
- CSV (для всех отчетов)
- Excel/XLSX (для всех отчетов)
- PDF (опционально, для выбранных отчетов)

---

## 📁 Структура реализации

### Этап 1: Создание модуля отчетов

#### 1.1. Структура файлов
```
apps/access_management/
├── reports/
│   ├── __init__.py
│   ├── views.py          # Views для генерации отчетов
│   ├── utils.py          # Утилиты для обработки данных
│   ├── forms.py          # Формы для параметров отчетов
│   └── exports.py        # Функции экспорта в различные форматы
└── templates/
    └── access_management/
        └── reports/
            ├── reports_home.html
            ├── system_access_active.html
            ├── system_access_expiring.html
            ├── digital_signature_active.html
            ├── digital_signature_missing.html
            └── digital_signature_expiring.html
```

#### 1.2. Зависимости для экспорта

**Для Excel:**
```python
# requirements.txt
openpyxl>=3.1.0  # Для Excel .xlsx
```

**Для PDF (опционально):**
```python
# requirements.txt
weasyprint>=59.0  # Или reportlab>=4.0
```

**Для CSV:**
- Встроенный модуль Python `csv` (не требует установки)

---

### Этап 2: Утилиты для работы с данными (reports/utils.py)

```python
from django.db.models import Q, OuterRef, Exists
from django.utils import timezone
from datetime import timedelta
from apps.access_management.models import SystemAccess, DigitalSignature
from apps.hr.models import Employees, Posts
from apps.reference.models import Departments


def get_employee_department(employee):
    """
    Получить текущее подразделение сотрудника через активную должность
    Возвращает Departments или None
    """
    current_post = Posts.objects.filter(
        employee=employee,
        status=Posts.STATUS_OCCUPIED,
        is_active=True
    ).select_related('department').first()
    
    return current_post.department if current_post else None


def get_system_accesses_by_department(system_id, status='active', department_id=None):
    """
    Получить доступы к системе, сгруппированные по подразделениям
    
    Returns:
        dict: {department: [accesses]}
    """
    accesses = SystemAccess.objects.filter(
        system_id=system_id,
        status=status
    ).select_related('employee', 'system')
    
    if department_id:
        # Фильтр по подразделению
        accesses = accesses.filter(
            employee__posts__department_id=department_id,
            employee__posts__status=Posts.STATUS_OCCUPIED
        )
    
    # Группировка по подразделениям
    result = {}
    for access in accesses:
        department = get_employee_department(access.employee)
        dept_name = department.name if department else "Не указано"
        
        if dept_name not in result:
            result[dept_name] = []
        
        result[dept_name].append({
            'access': access,
            'department': department,
            'employee': access.employee,
            'post': Posts.objects.filter(
                employee=access.employee,
                status=Posts.STATUS_OCCUPIED
            ).select_related('postname', 'department').first()
        })
    
    return result


def get_expiring_accesses(days=40, status_filter=None):
    """
    Получить доступы, требующие актуализации или истекающие
    
    Args:
        days: количество дней для определения "истекающих"
        status_filter: фильтр по статусу (None = все требующие внимания)
    
    Returns:
        list: список доступов с дополнительной информацией
    """
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    
    q_objects = Q()
    
    # Доступы со статусом "требует актуализации"
    if status_filter is None or 'needs_update' in status_filter:
        q_objects |= Q(status=SystemAccess.STATUS_NEEDS_UPDATE)
    
    # Доступы с датой блокировки в прошлом (просроченные)
    if status_filter is None or 'expired' in status_filter:
        q_objects |= Q(
            access_blocked_date__lt=today,
            status__in=[SystemAccess.STATUS_ACTIVE, SystemAccess.STATUS_SUSPENDED]
        )
    
    # Доступы с датой блокировки в ближайшие N дней (истекающие)
    if status_filter is None or 'expiring' in status_filter:
        q_objects |= Q(
            access_blocked_date__gte=today,
            access_blocked_date__lte=future_date,
            status__in=[SystemAccess.STATUS_ACTIVE, SystemAccess.STATUS_SUSPENDED]
        )
    
    accesses = SystemAccess.objects.filter(q_objects).select_related(
        'employee', 'system'
    )
    
    result = []
    for access in accesses:
        department = get_employee_department(access.employee)
        post = Posts.objects.filter(
            employee=access.employee,
            status=Posts.STATUS_OCCUPIED
        ).select_related('postname', 'department').first()
        
        # Расчет дней до/после блокировки
        days_diff = None
        if access.access_blocked_date:
            days_diff = (access.access_blocked_date - today).days
        
        result.append({
            'access': access,
            'department': department,
            'employee': access.employee,
            'post': post,
            'days_diff': days_diff,
            'is_expired': days_diff < 0 if days_diff is not None else False
        })
    
    return result


def get_employees_with_signature(status='active', cert_type_id=None, department_id=None):
    """
    Получить сотрудников с активной цифровой подписью, сгруппированных по подразделениям
    
    Returns:
        dict: {department: [signatures]}
    """
    signatures = DigitalSignature.objects.filter(status=status).select_related(
        'employee', 'certificate_type'
    )
    
    if cert_type_id:
        signatures = signatures.filter(certificate_type_id=cert_type_id)
    
    if department_id:
        signatures = signatures.filter(
            employee__posts__department_id=department_id,
            employee__posts__status=Posts.STATUS_OCCUPIED
        )
    
    result = {}
    for signature in signatures:
        department = get_employee_department(signature.employee)
        dept_name = department.name if department else "Не указано"
        
        if dept_name not in result:
            result[dept_name] = []
        
        post = Posts.objects.filter(
            employee=signature.employee,
            status=Posts.STATUS_OCCUPIED
        ).select_related('postname', 'department').first()
        
        result[dept_name].append({
            'signature': signature,
            'department': department,
            'employee': signature.employee,
            'post': post
        })
    
    return result


def get_employees_without_signature(department_id=None, active_only=True):
    """
    Получить сотрудников без активной цифровой подписи
    
    Returns:
        dict: {department: [employees]}
    """
    # Найти всех активных сотрудников
    employees = Employees.objects.filter(is_active=active_only)
    
    if department_id:
        employees = employees.filter(
            posts__department_id=department_id,
            posts__status=Posts.STATUS_OCCUPIED
        )
    
    # Исключить тех, у кого есть активная подпись
    employees_with_signature = DigitalSignature.objects.filter(
        status=DigitalSignature.STATUS_ACTIVE
    ).values_list('employee_id', flat=True)
    
    employees = employees.exclude(id__in=employees_with_signature)
    
    # Группировка по подразделениям
    result = {}
    for employee in employees:
        department = get_employee_department(employee)
        dept_name = department.name if department else "Не указано"
        
        if dept_name not in result:
            result[dept_name] = []
        
        post = Posts.objects.filter(
            employee=employee,
            status=Posts.STATUS_OCCUPIED
        ).select_related('postname', 'department').first()
        
        result[dept_name].append({
            'employee': employee,
            'department': department,
            'post': post
        })
    
    return result


def get_expiring_signatures(days=40, active_only=True, department_id=None):
    """
    Получить сертификаты, срок действия которых истекает в ближайшие N дней
    
    Returns:
        list: список подписей с дополнительной информацией
    """
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    
    signatures = DigitalSignature.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=future_date
    )
    
    if active_only:
        signatures = signatures.filter(status=DigitalSignature.STATUS_ACTIVE)
    
    if department_id:
        signatures = signatures.filter(
            employee__posts__department_id=department_id,
            employee__posts__status=Posts.STATUS_OCCUPIED
        )
    
    signatures = signatures.select_related('employee', 'certificate_type')
    
    result = []
    for signature in signatures:
        department = get_employee_department(signature.employee)
        post = Posts.objects.filter(
            employee=signature.employee,
            status=Posts.STATUS_OCCUPIED
        ).select_related('postname', 'department').first()
        
        days_diff = (signature.expiry_date - today).days
        
        result.append({
            'signature': signature,
            'department': department,
            'employee': signature.employee,
            'post': post,
            'days_diff': days_diff
        })
    
    return result
```

---

### Этап 3: Формы для параметров отчетов (reports/forms.py)

```python
from django import forms
from apps.reference.models import ITAsset, Departments
from apps.access_management.models import CertificateType


class SystemAccessActiveReportForm(forms.Form):
    """Форма для отчета по активным доступам к системе"""
    system = forms.ModelChoiceField(
        queryset=ITAsset.objects.filter(is_active=True),
        label='Информационная система',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[
            ('active', 'Активные'),
            ('suspended', 'Приостановленные'),
            ('blocked', 'Заблокированные'),
        ],
        initial='active',
        label='Статус доступа',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )


class SystemAccessExpiringReportForm(forms.Form):
    """Форма для отчета по истекающим доступам"""
    report_type = forms.MultipleChoiceField(
        choices=[
            ('needs_update', 'Требуют актуализации'),
            ('expired', 'Просроченные'),
            ('expiring', 'Истекающие'),
        ],
        label='Тип отчета',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        initial=['needs_update', 'expired', 'expiring']
    )
    days = forms.IntegerField(
        label='Период для "истекающих" (дней)',
        initial=40,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class DigitalSignatureActiveReportForm(forms.Form):
    """Форма для отчета по сотрудникам с активной подписью"""
    cert_type = forms.ModelChoiceField(
        queryset=CertificateType.objects.filter(is_active=True),
        label='Тип сертификата',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все типы'
    )
    status = forms.ChoiceField(
        choices=[
            ('active', 'Активные'),
            ('revoked', 'Аннулированные'),
        ],
        initial='active',
        label='Статус подписи',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )


class DigitalSignatureMissingReportForm(forms.Form):
    """Форма для отчета по сотрудникам без подписи"""
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )
    active_only = forms.BooleanField(
        label='Только активные сотрудники',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class DigitalSignatureExpiringReportForm(forms.Form):
    """Форма для отчета по истекающим сертификатам"""
    days = forms.IntegerField(
        label='Период истечения (дней)',
        initial=40,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    active_only = forms.BooleanField(
        label='Только активные сертификаты',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )
```

---

### Этап 4: Функции экспорта (reports/exports.py)

```python
import csv
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from io import BytesIO


def export_to_csv(data, filename, headers, row_generator):
    """
    Экспорт данных в CSV
    
    Args:
        data: данные для экспорта
        filename: имя файла
        headers: список заголовков колонок
        row_generator: функция-генератор строк (принимает элемент данных, возвращает список значений)
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(headers)
    
    for item in data:
        row = row_generator(item)
        writer.writerow(row)
    
    return response


def export_to_excel(data, filename, headers, row_generator, sheet_name='Отчет'):
    """
    Экспорт данных в Excel
    
    Args:
        data: данные для экспорта
        filename: имя файла
        headers: список заголовков колонок
        row_generator: функция-генератор строк
        sheet_name: название листа
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # Стили для заголовков
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    # Заголовки
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Данные
    for row_num, item in enumerate(data, 2):
        row_data = row_generator(item)
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.alignment = Alignment(vertical='top')
    
    # Автоматическая ширина колонок
    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        max_length = 0
        for row in ws[column_letter]:
            try:
                if len(str(row.value)) > max_length:
                    max_length = len(str(row.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    
    wb.save(response)
    return response


def export_to_pdf(html_template, context, filename):
    """
    Экспорт в PDF (опционально, используя weasyprint или reportlab)
    
    Требует установки: pip install weasyprint
    """
    from django.template.loader import render_to_string
    from weasyprint import HTML, CSS
    from django.conf import settings
    
    html_string = render_to_string(html_template, context)
    
    css = CSS(settings.BASE_DIR / 'static/css/pdf_styles.css')
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    
    return response
```

---

### Этап 5: Views для отчетов (reports/views.py)

```python
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http import HttpResponse
from .forms import (
    SystemAccessActiveReportForm,
    SystemAccessExpiringReportForm,
    DigitalSignatureActiveReportForm,
    DigitalSignatureMissingReportForm,
    DigitalSignatureExpiringReportForm
)
from .utils import (
    get_system_accesses_by_department,
    get_expiring_accesses,
    get_employees_with_signature,
    get_employees_without_signature,
    get_expiring_signatures
)
from .exports import export_to_csv, export_to_excel
from apps.reference.models import ITAsset, Departments


class ReportsHomeView(LoginRequiredMixin, View):
    """Главная страница отчетов"""
    def get(self, request):
        return render(request, 'access_management/reports/reports_home.html')


class SystemAccessActiveReportView(LoginRequiredMixin, View):
    """Отчет: Активные доступы к системе"""
    def get(self, request):
        form = SystemAccessActiveReportForm(request.GET)
        data = None
        
        if form.is_valid():
            system_id = form.cleaned_data['system'].id
            status = form.cleaned_data['status']
            department_id = form.cleaned_data['department'].id if form.cleaned_data['department'] else None
            
            data = get_system_accesses_by_department(system_id, status, department_id)
        
        format_type = request.GET.get('format', 'html')
        
        if format_type == 'csv':
            return self._export_csv(data, form.cleaned_data.get('system'))
        elif format_type == 'excel':
            return self._export_excel(data, form.cleaned_data.get('system'))
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/system_access_active.html', context)
    
    def _export_csv(self, data, system):
        headers = ['Подразделение', 'ФИО', 'Должность', 'Логин', 'Дата получения', 'Статус', 'Дата блокировки']
        
        rows = []
        for dept_name, items in sorted(data.items()):
            for item in items:
                post_name = item['post'].postname.name if item['post'] else "—"
                rows.append({
                    'department': dept_name,
                    'employee': str(item['employee']),
                    'post': post_name,
                    'login': item['access'].login,
                    'granted_date': item['access'].access_granted_date.strftime('%d.%m.%Y'),
                    'status': item['access'].get_status_display(),
                    'blocked_date': item['access'].access_blocked_date.strftime('%d.%m.%Y') if item['access'].access_blocked_date else "—"
                })
        
        def row_gen(item):
            return [
                item['department'],
                item['employee'],
                item['post'],
                item['login'],
                item['granted_date'],
                item['status'],
                item['blocked_date']
            ]
        
        filename = f"active_accesses_{system.name if system else 'all'}"
        return export_to_csv(rows, filename, headers, row_gen)
    
    def _export_excel(self, data, system):
        # Аналогично CSV, но используя export_to_excel
        # (реализация похожа)
        pass


class SystemAccessExpiringReportView(LoginRequiredMixin, View):
    """Отчет: Истекающие/просроченные доступы"""
    def get(self, request):
        form = SystemAccessExpiringReportForm(request.GET)
        data = None
        
        if form.is_valid():
            report_types = form.cleaned_data['report_type']
            days = form.cleaned_data['days']
            
            data = get_expiring_accesses(days, report_types)
        
        format_type = request.GET.get('format', 'html')
        
        if format_type in ['csv', 'excel']:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/system_access_expiring.html', context)
    
    def _export(self, data, format_type):
        # Реализация экспорта
        pass


class DigitalSignatureActiveReportView(LoginRequiredMixin, View):
    """Отчет: Сотрудники с активной подписью"""
    def get(self, request):
        form = DigitalSignatureActiveReportForm(request.GET)
        data = None
        
        if form.is_valid():
            status = form.cleaned_data['status']
            cert_type_id = form.cleaned_data['cert_type'].id if form.cleaned_data['cert_type'] else None
            department_id = form.cleaned_data['department'].id if form.cleaned_data['department'] else None
            
            data = get_employees_with_signature(status, cert_type_id, department_id)
        
        format_type = request.GET.get('format', 'html')
        
        if format_type in ['csv', 'excel']:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/digital_signature_active.html', context)
    
    def _export(self, data, format_type):
        # Реализация экспорта
        pass


class DigitalSignatureMissingReportView(LoginRequiredMixin, View):
    """Отчет: Сотрудники без подписи"""
    def get(self, request):
        form = DigitalSignatureMissingReportForm(request.GET)
        data = None
        
        if form.is_valid():
            department_id = form.cleaned_data['department'].id if form.cleaned_data['department'] else None
            active_only = form.cleaned_data['active_only']
            
            data = get_employees_without_signature(department_id, active_only)
        
        format_type = request.GET.get('format', 'html')
        
        if format_type in ['csv', 'excel']:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/digital_signature_missing.html', context)
    
    def _export(self, data, format_type):
        # Реализация экспорта
        pass


class DigitalSignatureExpiringReportView(LoginRequiredMixin, View):
    """Отчет: Истекающие сертификаты"""
    def get(self, request):
        form = DigitalSignatureExpiringReportForm(request.GET)
        data = None
        
        if form.is_valid():
            days = form.cleaned_data['days']
            active_only = form.cleaned_data['active_only']
            department_id = form.cleaned_data['department'].id if form.cleaned_data['department'] else None
            
            data = get_expiring_signatures(days, active_only, department_id)
        
        format_type = request.GET.get('format', 'html')
        
        if format_type in ['csv', 'excel']:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/digital_signature_expiring.html', context)
    
    def _export(self, data, format_type):
        # Реализация экспорта
        pass
```

---

### Этап 6: URLs для отчетов

```python
# apps/access_management/urls.py (дополнение)

urlpatterns += [
    # Отчеты
    path('reports/', views.ReportsHomeView.as_view(), name='reports_home'),
    path('reports/system-access/active/', reports.SystemAccessActiveReportView.as_view(), name='report_system_access_active'),
    path('reports/system-access/expiring/', reports.SystemAccessExpiringReportView.as_view(), name='report_system_access_expiring'),
    path('reports/digital-signature/active/', reports.DigitalSignatureActiveReportView.as_view(), name='report_signature_active'),
    path('reports/digital-signature/missing/', reports.DigitalSignatureMissingReportView.as_view(), name='report_signature_missing'),
    path('reports/digital-signature/expiring/', reports.DigitalSignatureExpiringReportView.as_view(), name='report_signature_expiring'),
]
```

---

### Этап 7: Шаблоны отчетов

#### 7.1. Главная страница отчетов (reports_home.html)

```django
{% extends "base.html" %}

{% block content %}
<h2>Отчеты по управлению доступом</h2>

<div class="row mt-4">
    <div class="col-md-6 mb-4">
        <div class="card">
            <div class="card-header">
                <h5>Отчеты по доступам к системам</h5>
            </div>
            <div class="card-body">
                <ul class="list-unstyled">
                    <li class="mb-2">
                        <a href="{% url 'access:report_system_access_active' %}" class="btn btn-outline-primary w-100">
                            Активные доступы к системе
                        </a>
                    </li>
                    <li>
                        <a href="{% url 'access:report_system_access_expiring' %}" class="btn btn-outline-primary w-100">
                            Истекающие/просроченные доступы
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 mb-4">
        <div class="card">
            <div class="card-header">
                <h5>Отчеты по цифровым подписям</h5>
            </div>
            <div class="card-body">
                <ul class="list-unstyled">
                    <li class="mb-2">
                        <a href="{% url 'access:report_signature_active' %}" class="btn btn-outline-primary w-100">
                            Сотрудники с активной подписью
                        </a>
                    </li>
                    <li class="mb-2">
                        <a href="{% url 'access:report_signature_missing' %}" class="btn btn-outline-primary w-100">
                            Сотрудники без подписи
                        </a>
                    </li>
                    <li>
                        <a href="{% url 'access:report_signature_expiring' %}" class="btn btn-outline-primary w-100">
                            Истекающие сертификаты
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</div>

<div class="mt-3">
    <a href="{% url 'access:home' %}" class="btn btn-secondary">Назад</a>
</div>
{% endblock %}
```

#### 7.2. Пример шаблона отчета (system_access_active.html)

```django
{% extends "base.html" %}

{% block content %}
<h2>Отчет: Активные доступы к системе</h2>

<form method="get" class="card mb-4">
    <div class="card-body">
        <div class="row g-3">
            <div class="col-md-4">
                {{ form.system.label_tag }}
                {{ form.system }}
            </div>
            <div class="col-md-3">
                {{ form.status.label_tag }}
                {{ form.status }}
            </div>
            <div class="col-md-3">
                {{ form.department.label_tag }}
                {{ form.department }}
            </div>
            <div class="col-md-2 d-flex align-items-end">
                <button type="submit" class="btn btn-primary w-100">Применить</button>
            </div>
        </div>
    </div>
</form>

{% if data %}
    <div class="d-flex justify-content-end mb-3">
        <a href="?{{ request.GET.urlencode }}&format=csv" class="btn btn-sm btn-success me-2">Экспорт CSV</a>
        <a href="?{{ request.GET.urlencode }}&format=excel" class="btn btn-sm btn-success">Экспорт Excel</a>
    </div>
    
    {% for dept_name, items in data.items|dictsort:0 %}
        <div class="card mb-3">
            <div class="card-header">
                <h5>{{ dept_name }} ({{ items|length }})</h5>
            </div>
            <div class="card-body">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>ФИО</th>
                            <th>Должность</th>
                            <th>Логин</th>
                            <th>Дата получения</th>
                            <th>Статус</th>
                            <th>Дата блокировки</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in items %}
                        <tr>
                            <td><a href="{% url 'hr:employee_detail' item.employee.pk %}">{{ item.employee }}</a></td>
                            <td>{{ item.post.postname.name|default:"—" }}</td>
                            <td><strong>{{ item.access.login }}</strong></td>
                            <td>{{ item.access.access_granted_date|date:"d.m.Y" }}</td>
                            <td><span class="badge bg-success">{{ item.access.get_status_display }}</span></td>
                            <td>{{ item.access.access_blocked_date|date:"d.m.Y"|default:"—" }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    {% endfor %}
{% else %}
    <div class="alert alert-info">
        Выберите параметры для генерации отчета
    </div>
{% endif %}

<div class="mt-3">
    <a href="{% url 'access:reports_home' %}" class="btn btn-secondary">Назад к отчетам</a>
</div>
{% endblock %}
```

---

## 📦 Установка зависимостей

```bash
pip install openpyxl>=3.1.0
# Для PDF (опционально):
pip install weasyprint>=59.0
```

---

## ✅ Порядок реализации

1. **Этап 1**: Создать модуль `reports/` и базовую структуру
2. **Этап 2**: Реализовать утилиты (`utils.py`)
3. **Этап 3**: Создать формы для параметров отчетов (`forms.py`)
4. **Этап 4**: Реализовать функции экспорта (`exports.py`)
5. **Этап 5**: Создать Views для каждого отчета (`views.py`)
6. **Этап 6**: Добавить URLs
7. **Этап 7**: Создать шаблоны для всех отчетов
8. **Этап 8**: Тестирование и оптимизация запросов

---

## 🔍 Особенности реализации

### Группировка по подразделениям

**Важно:** У сотрудника может быть:
- Одна активная должность (Posts со статусом 'occupied')
- Несколько должностей (при работе на ставках)
- Нет активной должности (новый сотрудник, уволенный)

**Подход:**
- Использовать `Posts.objects.filter(employee=employee, status=Posts.STATUS_OCCUPIED).first()` для получения текущей должности
- Если должности нет, группировать в "Не указано"

### Оптимизация запросов

- Использовать `select_related()` для ForeignKey
- Использовать `prefetch_related()` для ManyToMany (если будет)
- Избегать N+1 запросов при группировке

### Производительность

- Для больших объемов данных можно добавить пагинацию
- Кэширование часто запрашиваемых отчетов (опционально)
- Асинхронная генерация больших отчетов (опционально, для будущего)

---

## 📝 Дополнительные возможности (будущее)

1. **Расписание отчетов**: Автоматическая генерация и отправка по email
2. **Сохранение отчетов**: История сгенерированных отчетов
3. **Пользовательские фильтры**: Сохранение часто используемых параметров
4. **Графики и диаграммы**: Визуализация данных в отчетах

