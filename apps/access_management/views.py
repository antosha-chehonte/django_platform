from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from datetime import timedelta
from .models import SystemAccess, DigitalSignature
from .forms import SystemAccessForm, DigitalSignatureForm
from apps.hr.models import Employees
from apps.reference.models import CertificateType


def access_home(request):
    """Главная страница управления доступом"""
    return render(request, 'access_management/access_home.html')


# ========== SystemAccess Views ==========

class SystemAccessListView(LoginRequiredMixin, ListView):
    """Список доступов к системам"""
    model = SystemAccess
    template_name = 'access_management/system_access_list.html'
    context_object_name = 'accesses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SystemAccess.objects.select_related('employee', 'system').all()
        
        # Фильтр по сотруднику
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Фильтр по системе
        system_id = self.request.GET.get('system')
        if system_id:
            queryset = queryset.filter(system_id=system_id)
        
        # Фильтр по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(login__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__middle_name__icontains=search) |
                Q(system__name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['employee_filter'] = self.request.GET.get('employee', '')
        context['system_filter'] = self.request.GET.get('system', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['employees'] = Employees.objects.filter(is_active=True).order_by('last_name', 'first_name')
        from apps.reference.models import ITAsset
        context['systems'] = ITAsset.objects.filter(is_active=True).order_by('name')
        context['status_choices'] = SystemAccess.STATUS_CHOICES
        return context


class SystemAccessDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о доступе"""
    model = SystemAccess
    template_name = 'access_management/system_access_detail.html'
    context_object_name = 'access'


class SystemAccessCreateView(LoginRequiredMixin, CreateView):
    """Создание нового доступа"""
    model = SystemAccess
    form_class = SystemAccessForm
    template_name = 'access_management/system_access_form.html'
    success_url = reverse_lazy('access:system_access_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                from apps.hr.models import Employees
                employee = Employees.objects.get(pk=employee_id)
                kwargs['initial'] = kwargs.get('initial', {})
                kwargs['initial']['employee'] = employee.pk
            except Employees.DoesNotExist:
                pass
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Доступ успешно создан.')
        return super().form_valid(form)


class SystemAccessUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование доступа"""
    model = SystemAccess
    form_class = SystemAccessForm
    template_name = 'access_management/system_access_form.html'
    success_url = reverse_lazy('access:system_access_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Доступ успешно обновлен.')
        return super().form_valid(form)


class SystemAccessDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление доступа"""
    model = SystemAccess
    template_name = 'access_management/system_access_confirm_delete.html'
    success_url = reverse_lazy('access:system_access_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Доступ успешно удален.')
        return super().delete(request, *args, **kwargs)


# ========== DigitalSignature Views ==========

class DigitalSignatureListView(LoginRequiredMixin, ListView):
    """Список цифровых подписей"""
    model = DigitalSignature
    template_name = 'access_management/digital_signature_list.html'
    context_object_name = 'signatures'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = DigitalSignature.objects.select_related('employee', 'certificate_type').all()
        
        # Фильтр по сотруднику
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Фильтр по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Фильтр по типу сертификата
        cert_type_id = self.request.GET.get('cert_type')
        if cert_type_id:
            queryset = queryset.filter(certificate_type_id=cert_type_id)
        
        # Фильтр по истекающим срокам (в течение 40 дней)
        expiring = self.request.GET.get('expiring')
        if expiring == 'true':
            today = timezone.now().date()
            future_date = today + timedelta(days=40)
            queryset = queryset.filter(
                expiry_date__gte=today,
                expiry_date__lte=future_date
            )
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(certificate_serial__icontains=search) |
                Q(certificate_alias__icontains=search) |
                Q(carrier_serial__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__first_name__icontains=search) |
                Q(employee__middle_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['employee_filter'] = self.request.GET.get('employee', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['cert_type_filter'] = self.request.GET.get('cert_type', '')
        context['expiring_filter'] = self.request.GET.get('expiring', '')
        context['employees'] = Employees.objects.filter(is_active=True).order_by('last_name', 'first_name')
        context['cert_types'] = CertificateType.objects.filter(is_active=True).order_by('name')
        context['status_choices'] = DigitalSignature.STATUS_CHOICES
        return context


class DigitalSignatureDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о подписи"""
    model = DigitalSignature
    template_name = 'access_management/digital_signature_detail.html'
    context_object_name = 'signature'


class DigitalSignatureCreateView(LoginRequiredMixin, CreateView):
    """Создание новой подписи"""
    model = DigitalSignature
    form_class = DigitalSignatureForm
    template_name = 'access_management/digital_signature_form.html'
    success_url = reverse_lazy('access:digital_signature_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        employee_id = self.request.GET.get('employee')
        if employee_id:
            try:
                from apps.hr.models import Employees
                employee = Employees.objects.get(pk=employee_id)
                kwargs['initial'] = kwargs.get('initial', {})
                kwargs['initial']['employee'] = employee.pk
            except Employees.DoesNotExist:
                pass
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Цифровая подпись успешно создана.')
        return super().form_valid(form)


class DigitalSignatureUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование подписи"""
    model = DigitalSignature
    form_class = DigitalSignatureForm
    template_name = 'access_management/digital_signature_form.html'
    success_url = reverse_lazy('access:digital_signature_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Цифровая подпись успешно обновлена.')
        return super().form_valid(form)


class DigitalSignatureDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление подписи"""
    model = DigitalSignature
    template_name = 'access_management/digital_signature_confirm_delete.html'
    success_url = reverse_lazy('access:digital_signature_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Цифровая подпись успешно удалена.')
        return super().delete(request, *args, **kwargs)


class DigitalSignatureDownloadView(LoginRequiredMixin, View):
    """Скачивание файла сертификата"""
    def get(self, request, pk):
        signature = get_object_or_404(DigitalSignature, pk=pk)
        if signature.certificate_file:
            response = FileResponse(
                signature.certificate_file.open(),
                content_type='application/octet-stream'
            )
            filename = signature.certificate_file.name.split('/')[-1]
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            messages.error(request, 'Файл сертификата не найден.')
            return redirect('access:digital_signature_detail', pk=pk)



