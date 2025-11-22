from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import SystemAccess, DigitalSignature
from .forms import SystemAccessForm, DigitalSignatureForm
from apps.hr.models import Employees
from apps.reference.models import CertificateType
from .utils.certificate_parser import parse_certificate_from_django_file, CertificateParseError


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
        # Показываем только активных сотрудников (исключаем уволенных и временно отсутствующих)
        context['employees'] = Employees.objects.filter(status=Employees.STATUS_ACTIVE).order_by('last_name', 'first_name')
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
        
        # Фильтр по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Фильтр по типу сертификата
        cert_type_id = self.request.GET.get('cert_type')
        if cert_type_id:
            queryset = queryset.filter(certificate_type_id=cert_type_id)
        
        # Фильтр по диапазону даты окончания
        expiry_date_from = self.request.GET.get('expiry_date_from')
        if expiry_date_from:
            queryset = queryset.filter(expiry_date__gte=expiry_date_from)
        
        expiry_date_to = self.request.GET.get('expiry_date_to')
        if expiry_date_to:
            queryset = queryset.filter(expiry_date__lte=expiry_date_to)
        
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
        context['status_filter'] = self.request.GET.get('status', '')
        context['cert_type_filter'] = self.request.GET.get('cert_type', '')
        context['expiry_date_from'] = self.request.GET.get('expiry_date_from', '')
        context['expiry_date_to'] = self.request.GET.get('expiry_date_to', '')
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


@method_decorator(csrf_exempt, name='dispatch')
class CertificateParseAjaxView(LoginRequiredMixin, View):
    """AJAX endpoint для парсинга сертификата без сохранения"""
    
    def post(self, request):
        """Парсит загруженный файл сертификата и возвращает данные в JSON"""
        if 'certificate_file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Файл не предоставлен'
            }, status=400)
        
        try:
            certificate_file = request.FILES['certificate_file']
            cert_data = parse_certificate_from_django_file(certificate_file)
            
            # Определяем статус (логика совпадает с формой)
            today = timezone.now().date()
            expiry_date = cert_data['expiry_date']
            days_until_expiry = (expiry_date - today).days
            
            if expiry_date < today:
                # Сертификат уже истек
                status = DigitalSignature.STATUS_NEEDS_UPDATE
            elif days_until_expiry <= 30:
                # Сертификат истекает в течение месяца
                status = DigitalSignature.STATUS_NEEDS_UPDATE
            else:
                # Сертификат действителен
                status = DigitalSignature.STATUS_ACTIVE
            
            return JsonResponse({
                'success': True,
                'data': {
                    'certificate_serial': cert_data['certificate_serial'],
                    'certificate_alias': cert_data['certificate_alias'],
                    'expiry_date': cert_data['expiry_date'].strftime('%Y-%m-%d'),
                    'status': status,
                    'subject_name': cert_data.get('subject_name', ''),
                    'issuer_name': cert_data.get('issuer_name', ''),
                    'valid_from': cert_data.get('valid_from').strftime('%Y-%m-%d') if cert_data.get('valid_from') else '',
                }
            })
        
        except CertificateParseError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Ошибка при обработке файла: {str(e)}'
            }, status=500)



