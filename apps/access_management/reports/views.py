from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
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
        
        if format_type == 'csv' and data:
            return self._export_csv(data, form.cleaned_data.get('system'))
        elif format_type == 'excel' and data:
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
                post_name = item['post'].postname.name if item['post'] and item['post'].postname else "—"
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
        
        filename = f"active_accesses_{system.name.replace(' ', '_') if system else 'all'}"
        return export_to_csv(rows, filename, headers, row_gen)
    
    def _export_excel(self, data, system):
        headers = ['Подразделение', 'ФИО', 'Должность', 'Логин', 'Дата получения', 'Статус', 'Дата блокировки']
        
        rows = []
        for dept_name, items in sorted(data.items()):
            for item in items:
                post_name = item['post'].postname.name if item['post'] and item['post'].postname else "—"
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
        
        filename = f"active_accesses_{system.name.replace(' ', '_') if system else 'all'}"
        return export_to_excel(rows, filename, headers, row_gen, sheet_name='Активные доступы')


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
        
        if format_type in ['csv', 'excel'] and data:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/system_access_expiring.html', context)
    
    def _export(self, data, format_type):
        headers = ['Подразделение', 'ФИО', 'Должность', 'Система', 'Логин', 'Статус', 'Дата получения', 'Дата блокировки', 'Дней до/после']
        
        rows = []
        for item in data:
            dept_name = item['department'].name if item['department'] else "Не указано"
            post_name = item['post'].postname.name if item['post'] and item['post'].postname else "—"
            
            days_str = "—"
            if item['days_diff'] is not None:
                if item['is_expired']:
                    days_str = f"Просрочено: {abs(item['days_diff'])}"
                else:
                    days_str = f"Дней до: {item['days_diff']}"
            
            rows.append({
                'department': dept_name,
                'employee': str(item['employee']),
                'post': post_name,
                'system': item['access'].system.name,
                'login': item['access'].login,
                'status': item['access'].get_status_display(),
                'granted_date': item['access'].access_granted_date.strftime('%d.%m.%Y'),
                'blocked_date': item['access'].access_blocked_date.strftime('%d.%m.%Y') if item['access'].access_blocked_date else "—",
                'days': days_str
            })
        
        def row_gen(item):
            return [
                item['department'],
                item['employee'],
                item['post'],
                item['system'],
                item['login'],
                item['status'],
                item['granted_date'],
                item['blocked_date'],
                item['days']
            ]
        
        filename = "expiring_accesses"
        
        if format_type == 'csv':
            return export_to_csv(rows, filename, headers, row_gen)
        else:
            return export_to_excel(rows, filename, headers, row_gen, sheet_name='Истекающие доступы')


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
        
        if format_type in ['csv', 'excel'] and data:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/digital_signature_active.html', context)
    
    def _export(self, data, format_type):
        headers = ['Подразделение', 'ФИО', 'Должность', 'Тип сертификата', 'Серийный номер', 'Отпечаток', 'Дата окончания', 'Статус']
        
        rows = []
        for dept_name, items in sorted(data.items()):
            for item in items:
                post_name = item['post'].postname.name if item['post'] and item['post'].postname else "—"
                is_expired = item['signature'].is_expired
                status_str = item['signature'].get_status_display()
                if is_expired:
                    status_str += " (истек)"
                
                rows.append({
                    'department': dept_name,
                    'employee': str(item['employee']),
                    'post': post_name,
                    'cert_type': item['signature'].certificate_type.name,
                    'serial': item['signature'].certificate_serial,
                    'alias': item['signature'].certificate_alias,
                    'expiry': item['signature'].expiry_date.strftime('%d.%m.%Y'),
                    'status': status_str
                })
        
        def row_gen(item):
            return [
                item['department'],
                item['employee'],
                item['post'],
                item['cert_type'],
                item['serial'],
                item['alias'],
                item['expiry'],
                item['status']
            ]
        
        filename = "signatures_active"
        
        if format_type == 'csv':
            return export_to_csv(rows, filename, headers, row_gen)
        else:
            return export_to_excel(rows, filename, headers, row_gen, sheet_name='Подписи активные')


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
        
        if format_type in ['csv', 'excel'] and data:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/digital_signature_missing.html', context)
    
    def _export(self, data, format_type):
        headers = ['Подразделение', 'ФИО', 'Должность', 'Email', 'Телефон']
        
        rows = []
        for dept_name, items in sorted(data.items()):
            for item in items:
                post_name = item['post'].postname.name if item['post'] and item['post'].postname else "—"
                
                rows.append({
                    'department': dept_name,
                    'employee': str(item['employee']),
                    'post': post_name,
                    'email': item['employee'].email or "—",
                    'phone': item['employee'].phone or "—"
                })
        
        def row_gen(item):
            return [
                item['department'],
                item['employee'],
                item['post'],
                item['email'],
                item['phone']
            ]
        
        filename = "employees_without_signature"
        
        if format_type == 'csv':
            return export_to_csv(rows, filename, headers, row_gen)
        else:
            return export_to_excel(rows, filename, headers, row_gen, sheet_name='Сотрудники без подписи')


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
        
        if format_type in ['csv', 'excel'] and data:
            return self._export(data, format_type)
        
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'access_management/reports/digital_signature_expiring.html', context)
    
    def _export(self, data, format_type):
        headers = ['Подразделение', 'ФИО', 'Должность', 'Тип сертификата', 'Серийный номер', 'Дата окончания', 'Дней до истечения', 'Статус']
        
        rows = []
        for item in data:
            dept_name = item['department'].name if item['department'] else "Не указано"
            post_name = item['post'].postname.name if item['post'] and item['post'].postname else "—"
            
            rows.append({
                'department': dept_name,
                'employee': str(item['employee']),
                'post': post_name,
                'cert_type': item['signature'].certificate_type.name,
                'serial': item['signature'].certificate_serial,
                'expiry': item['signature'].expiry_date.strftime('%d.%m.%Y'),
                'days': item['days_diff'],
                'status': item['signature'].get_status_display()
            })
        
        def row_gen(item):
            return [
                item['department'],
                item['employee'],
                item['post'],
                item['cert_type'],
                item['serial'],
                item['expiry'],
                item['days'],
                item['status']
            ]
        
        filename = "signatures_expiring"
        
        if format_type == 'csv':
            return export_to_csv(rows, filename, headers, row_gen)
        else:
            return export_to_excel(rows, filename, headers, row_gen, sheet_name='Истекающие сертификаты')

