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
from .forms import SystemAccessForm, DigitalSignatureForm, BulkCertificateUploadForm, CertificateImportForm
from apps.hr.models import Employees
from apps.reference.models import CertificateType
from .utils.certificate_parser import (
    parse_certificate_from_django_file, 
    CertificateParseError,
    generate_certificate_filename
)
from .utils.html_certificate_parser import parse_certificate_html, HTMLParseError
from .utils.certificate_matcher import (
    get_certificate_type_by_text,
    match_employee_by_name,
    check_duplicate_certificate
)
from django.core.files.base import ContentFile
from django.db import transaction


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


def _find_employee_by_name(subject_name):
    """
    Ищет сотрудника по ФИО из сертификата
    
    Args:
        subject_name: ФИО из сертификата (может быть в формате "Фамилия Имя Отчество" или "Surname GivenName")
    
    Returns:
        Employees объект или None, если не найден
    """
    if not subject_name:
        return None
    
    # Нормализуем строку: убираем лишние пробелы
    subject_name = ' '.join(subject_name.split())
    
    # Разбиваем на части
    name_parts = subject_name.split()
    
    if len(name_parts) < 2:
        return None
    
    last_name = name_parts[0]
    first_name = name_parts[1]
    middle_name = name_parts[2] if len(name_parts) >= 3 else ''
    
    # Сначала ищем точное совпадение с отчеством (если оно есть)
    if middle_name:
        employee = Employees.objects.filter(
            last_name__iexact=last_name,
            first_name__iexact=first_name,
            middle_name__iexact=middle_name
        ).first()
        if employee:
            return employee
    
    # Если не нашли с отчеством или отчества нет, ищем по фамилии и имени
    # Если есть отчество в сертификате, предпочитаем сотрудника с совпадающим отчеством
    employees = Employees.objects.filter(
        last_name__iexact=last_name,
        first_name__iexact=first_name
    )
    
    if middle_name:
        # Если есть отчество в сертификате, ищем сотрудника с совпадающим отчеством
        for emp in employees:
            if emp.middle_name and emp.middle_name.lower() == middle_name.lower():
                return emp
        # Если не нашли с совпадающим отчеством, возвращаем первого найденного
        return employees.first()
    else:
        # Если отчества нет в сертификате, предпочитаем сотрудника без отчества
        for emp in employees:
            if not emp.middle_name or emp.middle_name.strip() == '':
                return emp
        # Если все сотрудники имеют отчество, возвращаем первого
        return employees.first()


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
            
            # Ищем сотрудника по ФИО из сертификата
            employee_id = None
            employee_name = None
            subject_name = cert_data.get('subject_name', '')
            
            if subject_name:
                employee = _find_employee_by_name(subject_name)
                if employee:
                    employee_id = employee.pk
                    employee_name = str(employee)
            
            response_data = {
                'certificate_serial': cert_data['certificate_serial'],
                'certificate_alias': cert_data['certificate_alias'],
                'expiry_date': cert_data['expiry_date'].strftime('%Y-%m-%d'),
                'status': status,
                'subject_name': subject_name,
                'issuer_name': cert_data.get('issuer_name', ''),
                'valid_from': cert_data.get('valid_from').strftime('%Y-%m-%d') if cert_data.get('valid_from') else '',
            }
            
            # Добавляем информацию о найденном сотруднике
            if employee_id:
                response_data['employee_id'] = employee_id
                response_data['employee_name'] = employee_name
            
            return JsonResponse({
                'success': True,
                'data': response_data
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


# ========== Bulk Certificate Upload Views ==========

class BulkCertificateUploadView(LoginRequiredMixin, View):
    """View для массовой загрузки сертификатов"""
    
    def get(self, request):
        """Отображение формы загрузки"""
        form = BulkCertificateUploadForm()
        return render(request, 'access_management/bulk_certificate_upload.html', {
            'form': form
        })
    
    def post(self, request):
        """Обработка загруженных файлов"""
        form = BulkCertificateUploadForm(request.POST, request.FILES)
        
        # Получаем файлы напрямую из request.FILES
        files = request.FILES.getlist('certificate_files')
        
        # Валидация файлов
        if not files:
            form.add_error('certificate_files', 'Необходимо выбрать хотя бы один файл')
            return render(request, 'access_management/bulk_certificate_upload.html', {
                'form': form
            })
        
        max_size = 1024 * 1024  # 1 МБ
        allowed_extensions = ['.cer', '.pfx']
        validation_errors = []
        
        for file in files:
            # Проверка размера
            if file.size > max_size:
                validation_errors.append(
                    f'Файл "{file.name}" превышает максимальный размер {max_size / (1024 * 1024):.1f} МБ'
                )
            
            # Проверка расширения
            file_ext = None
            if file.name:
                file_ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else None
            
            if file_ext not in allowed_extensions:
                validation_errors.append(
                    f'Файл "{file.name}" имеет недопустимое расширение. Разрешены только: {", ".join(allowed_extensions)}'
                )
        
        if validation_errors:
            for error in validation_errors:
                form.add_error('certificate_files', error)
            return render(request, 'access_management/bulk_certificate_upload.html', {
                'form': form
            })
        
        if not form.is_valid():
            return render(request, 'access_management/bulk_certificate_upload.html', {
                'form': form
            })
        
        certificate_type = form.cleaned_data.get('certificate_type')
        
        # Если тип не указан, берем первый активный
        if not certificate_type:
            certificate_type = CertificateType.objects.filter(is_active=True).first()
            if not certificate_type:
                messages.error(request, 'Не указан тип сертификата и нет активных типов в справочнике.')
                return render(request, 'access_management/bulk_certificate_upload.html', {
                    'form': form
                })
        
        # Результаты обработки
        results = {
            'success': [],  # Успешно загружено
            'skipped': [],  # Пропущено (сотрудник не найден)
            'errors': [],   # Ошибки парсинга
            'duplicates': []  # Дубликаты (уже существует)
        }
        
        today = timezone.now().date()
        
        # Обрабатываем каждый файл
        for file in files:
            original_filename = file.name
            try:
                # Парсим сертификат
                cert_data = parse_certificate_from_django_file(file)
                
                # Определяем статус
                expiry_date = cert_data['expiry_date']
                days_until_expiry = (expiry_date - today).days
                
                if expiry_date < today:
                    status = DigitalSignature.STATUS_NEEDS_UPDATE
                elif days_until_expiry <= 30:
                    status = DigitalSignature.STATUS_NEEDS_UPDATE
                else:
                    status = DigitalSignature.STATUS_ACTIVE
                
                # Ищем сотрудника по ФИО
                subject_name = cert_data.get('subject_name', '')
                employee = None
                if subject_name:
                    employee = _find_employee_by_name(subject_name)
                
                if not employee:
                    # Сотрудник не найден - пропускаем
                    results['skipped'].append({
                        'filename': original_filename,
                        'subject_name': subject_name,
                        'certificate_serial': cert_data.get('certificate_serial', 'N/A'),
                        'reason': 'Сотрудник не найден в базе данных'
                    })
                    continue
                
                # Проверяем на дубликаты по серийному номеру
                existing = DigitalSignature.objects.filter(
                    certificate_serial=cert_data['certificate_serial']
                ).first()
                
                if existing:
                    results['duplicates'].append({
                        'filename': original_filename,
                        'employee': str(employee),
                        'certificate_serial': cert_data['certificate_serial'],
                        'existing_id': existing.pk
                    })
                    continue
                
                # Генерируем имя файла
                new_filename = generate_certificate_filename(
                    employee, 
                    expiry_date, 
                    original_filename
                )
                
                # Создаем запись DigitalSignature
                signature = DigitalSignature(
                    employee=employee,
                    certificate_type=certificate_type,
                    certificate_serial=cert_data['certificate_serial'],
                    certificate_alias=cert_data['certificate_alias'],
                    expiry_date=expiry_date,
                    status=status,
                    notes=f"Сертификат выдан: {subject_name}"
                )
                
                # Сохраняем файл с новым именем
                file.seek(0)  # Возвращаемся в начало файла
                file_content = file.read()
                signature.certificate_file.save(
                    new_filename,
                    ContentFile(file_content),
                    save=False
                )
                
                signature.save()
                
                results['success'].append({
                    'filename': original_filename,
                    'employee': str(employee),
                    'certificate_serial': cert_data['certificate_serial'],
                    'signature_id': signature.pk,
                    'new_filename': new_filename
                })
                
            except CertificateParseError as e:
                results['errors'].append({
                    'filename': original_filename,
                    'error': str(e)
                })
            except Exception as e:
                results['errors'].append({
                    'filename': original_filename,
                    'error': f'Неожиданная ошибка: {str(e)}'
                })
        
        # Сохраняем результаты в сессии для отображения на странице результатов
        request.session['bulk_upload_results'] = results
        
        # Редирект на страницу результатов
        return redirect('access:bulk_certificate_upload_results')


class BulkCertificateUploadResultsView(LoginRequiredMixin, View):
    """View для отображения результатов массовой загрузки"""
    
    def get(self, request):
        """Отображение результатов обработки"""
        results = request.session.get('bulk_upload_results')
        
        if not results:
            messages.warning(request, 'Результаты обработки не найдены.')
            return redirect('access:digital_signature_list')
        
        # Удаляем результаты из сессии после отображения
        del request.session['bulk_upload_results']
        
        context = {
            'results': results,
            'total_files': (
                len(results['success']) + 
                len(results['skipped']) + 
                len(results['errors']) + 
                len(results['duplicates'])
            ),
            'success_count': len(results['success']),
            'skipped_count': len(results['skipped']),
            'errors_count': len(results['errors']),
            'duplicates_count': len(results['duplicates'])
        }
        
        return render(request, 'access_management/bulk_upload_results.html', context)


class CertificateImportView(LoginRequiredMixin, View):
    """View для импорта сертификатов из HTML-файла"""
    
    template_name = 'access_management/certificate_import.html'
    
    def get(self, request):
        """Отображение формы импорта"""
        form = CertificateImportForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """Обработка импорта"""
        form = CertificateImportForm(request.POST, request.FILES)
        
        if not form.is_valid():
            # Показываем ошибки валидации формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Ошибка в поле "{field}": {error}')
            return render(request, self.template_name, {'form': form})
        
        html_file = form.cleaned_data['html_file']
        override_certificate_type = form.cleaned_data.get('certificate_type')
        
        # Результаты импорта
        results = {
            'imported': [],  # Успешно импортировано
            'skipped_employee_not_found': [],  # Сотрудник не найден
            'skipped_duplicate': [],  # Дубликат
            'skipped_type_not_found': [],  # Тип сертификата не найден
            'skipped_parse_error': [],  # Ошибка парсинга
        }
        
        try:
            # Парсим HTML-файл
            certificates = parse_certificate_html(html_file)
        except HTMLParseError as e:
            import traceback
            error_details = traceback.format_exc()
            messages.error(request, f'Ошибка при парсинге HTML-файла: {str(e)}')
            # Логируем детали ошибки для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'HTML parse error: {error_details}')
            return render(request, self.template_name, {'form': CertificateImportForm()})
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messages.error(request, f'Неожиданная ошибка при обработке файла: {str(e)}')
            # Логируем детали ошибки для отладки
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Unexpected error during HTML import: {error_details}')
            return render(request, self.template_name, {'form': CertificateImportForm()})
        
        if not certificates:
            messages.warning(request, 'В HTML-файле не найдено сертификатов для импорта. Проверьте формат файла.')
            return render(request, self.template_name, {'form': CertificateImportForm()})
        
        # Список для массового создания
        signatures_to_create = []
        
        # Обрабатываем каждый сертификат
        for cert_data in certificates:
            try:
                # Определяем тип сертификата
                if override_certificate_type:
                    certificate_type = override_certificate_type
                else:
                    certificate_type = get_certificate_type_by_text(cert_data['certificate_type_text'])
                    if not certificate_type:
                        results['skipped_type_not_found'].append({
                            'certificate_number': cert_data['certificate_number'],
                            'owner_name': cert_data['owner_name'],
                            'type_text': cert_data['certificate_type_text'],
                        })
                        continue
                
                # Ищем сотрудника по ФИО
                employee = match_employee_by_name(cert_data['owner_name'])
                if not employee:
                    results['skipped_employee_not_found'].append({
                        'certificate_number': cert_data['certificate_number'],
                        'owner_name': cert_data['owner_name'],
                    })
                    continue
                
                # Проверяем дубликат
                if check_duplicate_certificate(cert_data['certificate_number']):
                    results['skipped_duplicate'].append({
                        'certificate_number': cert_data['certificate_number'],
                        'owner_name': cert_data['owner_name'],
                    })
                    continue
                
                # Определяем статус
                from django.utils import timezone
                today = timezone.now().date()
                if cert_data['expiry_date'] < today:
                    status = DigitalSignature.STATUS_NEEDS_UPDATE
                else:
                    status = DigitalSignature.STATUS_ACTIVE
                
                # Создаем объект для массового создания
                signature = DigitalSignature(
                    employee=employee,
                    certificate_type=certificate_type,
                    certificate_serial=cert_data['certificate_number'],
                    certificate_alias='',  # В HTML нет этих данных
                    expiry_date=cert_data['expiry_date'],
                    status=status,
                    notes=f'Импортировано из HTML-файла: {html_file.name}'
                )
                signatures_to_create.append(signature)
                
                results['imported'].append({
                    'certificate_number': cert_data['certificate_number'],
                    'owner_name': cert_data['owner_name'],
                    'employee': str(employee),
                    'expiry_date': cert_data['expiry_date'],
                })
            
            except Exception as e:
                # Ошибка при обработке отдельного сертификата
                results['skipped_parse_error'].append({
                    'certificate_number': cert_data.get('certificate_number', 'Неизвестно'),
                    'owner_name': cert_data.get('owner_name', 'Неизвестно'),
                    'error': str(e),
                })
                continue
        
        # Массовое создание записей в транзакции
        if signatures_to_create:
            try:
                with transaction.atomic():
                    DigitalSignature.objects.bulk_create(signatures_to_create)
                messages.success(
                    request,
                    f'Успешно импортировано {len(signatures_to_create)} сертификатов.'
                )
            except Exception as e:
                messages.error(
                    request,
                    f'Ошибка при сохранении в базу данных: {str(e)}'
                )
                return render(request, self.template_name, {'form': form})
        
        # Формируем контекст для отображения результатов
        context = {
            'form': CertificateImportForm(),  # Новая форма для повторного импорта
            'results': results,
            'total_found': len(certificates),
            'imported_count': len(results['imported']),
            'skipped_employee_count': len(results['skipped_employee_not_found']),
            'skipped_duplicate_count': len(results['skipped_duplicate']),
            'skipped_type_count': len(results['skipped_type_not_found']),
            'skipped_error_count': len(results['skipped_parse_error']),
        }
        
        return render(request, self.template_name, context)

