from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponse
from .models import Departments, Postname, ITAsset, CertificateType
from .forms import DepartmentForm, PostnameForm, CSVImportPostnameForm, CSVImportDepartmentForm, ITAssetForm, CertificateTypeForm
import csv


class DepartmentListView(LoginRequiredMixin, ListView):
    """Список подразделений"""
    model = Departments
    template_name = 'reference/departments_list.html'
    context_object_name = 'departments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Departments.objects.filter(is_active=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о подразделении"""
    model = Departments
    template_name = 'reference/departments_detail.html'
    context_object_name = 'department'


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Создание нового подразделения"""
    model = Departments
    form_class = DepartmentForm
    template_name = 'reference/departments_form.html'
    success_url = reverse_lazy('reference:departments_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Подразделение успешно создано.')
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование подразделения"""
    model = Departments
    form_class = DepartmentForm
    template_name = 'reference/departments_form.html'
    success_url = reverse_lazy('reference:departments_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Подразделение успешно обновлено.')
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление подразделения"""
    model = Departments
    template_name = 'reference/departments_confirm_delete.html'
    success_url = reverse_lazy('reference:departments_list')
    login_url = '/testing/moderator/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Подразделение успешно удалено.')
        return super().delete(request, *args, **kwargs)


class DepartmentCSVImportView(LoginRequiredMixin, View):
    """Импорт подразделений из CSV файла"""
    
    def get(self, request):
        form = CSVImportDepartmentForm()
        return render(request, 'reference/departments_csv_import.html', {'form': form})
    
    def post(self, request):
        form = CSVImportDepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                decoded_file = csv_file.read().decode('utf-8-sig')
                lines = decoded_file.strip().splitlines()
                
                if not lines:
                    messages.error(request, 'Файл пуст.')
                    return render(request, 'reference/departments_csv_import.html', {'form': form})
                
                imported = 0
                errors = []
                
                # Определяем, есть ли заголовок
                first_line_lower = lines[0].lower()
                has_header = 'название' in first_line_lower or 'name' in first_line_lower or 'подразделение' in first_line_lower
                
                if has_header:
                    csv_reader = csv.DictReader(lines, delimiter=';')
                    start_row = 2
                else:
                    csv_reader = csv.reader(lines, delimiter=';')
                    start_row = 1
                
                for row_num, row_data in enumerate(csv_reader, start=start_row):
                    try:
                        if has_header:
                            row = row_data
                            name = row.get('Название', '').strip()
                            code = row.get('Код', '').strip()
                            sorting = row.get('Код сортировки', '').strip()
                            description = row.get('Описание', '').strip()
                            parent_str = row.get('Родительское подразделение', '').strip()
                            is_logical_str = row.get('Логическое', '').strip()
                            is_active_str = row.get('Активно', '').strip()
                        else:
                            if len(row_data) < 2:
                                errors.append(f"Строка {row_num}: недостаточно данных (нужно минимум 2 поля: Название, Код)")
                                continue
                            name = row_data[0].strip() if len(row_data) > 0 else ''
                            code = row_data[1].strip() if len(row_data) > 1 else ''
                            sorting = row_data[2].strip() if len(row_data) > 2 else ''
                            description = row_data[3].strip() if len(row_data) > 3 else ''
                            parent_str = row_data[4].strip() if len(row_data) > 4 else ''
                            is_logical_str = row_data[5].strip() if len(row_data) > 5 else ''
                            is_active_str = row_data[6].strip() if len(row_data) > 6 else ''
                        
                        # Валидация обязательных полей
                        if not name or not code:
                            errors.append(f"Строка {row_num}: отсутствует название или код")
                            continue
                        
                        # Проверка уникальности кода
                        if Departments.objects.filter(code=code).exists():
                            errors.append(f"Строка {row_num}: подразделение с кодом '{code}' уже существует")
                            continue
                        
                        # Поиск родительского подразделения (опционально)
                        parent = None
                        if parent_str:
                            try:
                                parent = Departments.objects.get(name=parent_str, is_active=True)
                            except Departments.DoesNotExist:
                                try:
                                    parent = Departments.objects.get(code=parent_str, is_active=True)
                                except Departments.DoesNotExist:
                                    errors.append(f"Строка {row_num}: родительское подразделение не найдено: {parent_str}")
                                    continue
                        
                        # Определяем is_logical
                        is_logical = False
                        if is_logical_str:
                            is_logical_str_lower = is_logical_str.lower()
                            if is_logical_str_lower in ['true', '1', 'да', 'yes', 'да']:
                                is_logical = True
                            elif is_logical_str_lower in ['false', '0', 'нет', 'no']:
                                is_logical = False
                        
                        # Определяем is_active
                        is_active = True
                        if is_active_str:
                            is_active_str_lower = is_active_str.lower()
                            if is_active_str_lower in ['false', '0', 'нет', 'no']:
                                is_active = False
                            elif is_active_str_lower in ['true', '1', 'да', 'yes']:
                                is_active = True
                        
                        # Создаем подразделение
                        Departments.objects.create(
                            name=name,
                            code=code,
                            sorting=sorting,
                            description=description,
                            parent=parent,
                            is_logical=is_logical,
                            is_active=is_active
                        )
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Строка {row_num}: ошибка при обработке - {str(e)}")
                
                if imported > 0:
                    messages.success(request, f'Успешно импортировано подразделений: {imported}')
                if errors:
                    for error in errors[:20]:
                        messages.warning(request, error)
                    if len(errors) > 20:
                        messages.warning(request, f'... и еще {len(errors) - 20} ошибок')
                
                if imported == 0 and not errors:
                    messages.info(request, 'Нет данных для импорта. Проверьте формат файла.')
                
                return redirect('reference:departments_list')
                
            except UnicodeDecodeError:
                messages.error(request, 'Ошибка кодировки файла. Убедитесь, что файл в кодировке UTF-8.')
                return render(request, 'reference/departments_csv_import.html', {'form': form})
            except Exception as e:
                messages.error(request, f'Ошибка при чтении файла: {str(e)}')
                return render(request, 'reference/departments_csv_import.html', {'form': form})
        
        for field, field_errors in form.errors.items():
            for error in field_errors:
                messages.error(request, f'{field}: {error}')
        
        return render(request, 'reference/departments_csv_import.html', {'form': form})


class DepartmentCSVTemplateView(LoginRequiredMixin, View):
    """Генерация шаблона CSV файла для импорта подразделений"""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="departments_template.csv"'
        
        writer = csv.writer(response, delimiter=';')
        
        writer.writerow(['Название', 'Код', 'Код сортировки', 'Описание', 'Родительское подразделение', 'Логическое', 'Активно'])
        
        writer.writerow(['Администрация', 'ADM001', 'ADM', 'Административное подразделение', '', 'False', 'True'])
        writer.writerow(['Отдел продаж', 'SALES001', 'SALES', 'Отдел по работе с клиентами', 'Администрация', 'False', 'True'])
        writer.writerow(['Отдел кадров', 'HR001', 'HR', 'Отдел управления персоналом', 'Администрация', 'False', 'True'])
        
        return response


class PostnameListView(LoginRequiredMixin, ListView):
    """Список должностей"""
    model = Postname
    template_name = 'reference/postname_list.html'
    context_object_name = 'postnames'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Postname.objects.filter(is_active=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class PostnameDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о должности"""
    model = Postname
    template_name = 'reference/postname_detail.html'
    context_object_name = 'postname'


class PostnameCreateView(LoginRequiredMixin, CreateView):
    """Создание новой должности"""
    model = Postname
    form_class = PostnameForm
    template_name = 'reference/postname_form.html'
    success_url = reverse_lazy('reference:postname_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Должность успешно создана.')
        return super().form_valid(form)


class PostnameUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование должности"""
    model = Postname
    form_class = PostnameForm
    template_name = 'reference/postname_form.html'
    success_url = reverse_lazy('reference:postname_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Должность успешно обновлена.')
        return super().form_valid(form)


class PostnameDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление должности"""
    model = Postname
    template_name = 'reference/postname_confirm_delete.html'
    success_url = reverse_lazy('reference:postname_list')
    login_url = '/testing/moderator/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Должность успешно удалена.')
        return super().delete(request, *args, **kwargs)


@login_required(login_url='/testing/moderator/login/')
def reference_home(request):
    """Главная страница справочников"""
    departments_count = Departments.objects.filter(is_active=True).count()
    postnames_count = Postname.objects.filter(is_active=True).count()
    itassets_count = ITAsset.objects.filter(is_active=True).count()
    cert_types_count = CertificateType.objects.filter(is_active=True).count()
    context = {
        'departments_count': departments_count,
        'postnames_count': postnames_count,
        'itassets_count': itassets_count,
        'cert_types_count': cert_types_count,
    }
    return render(request, 'reference/reference_home.html', context)


class PostnameCSVImportView(LoginRequiredMixin, View):
    """Импорт должностей из CSV файла"""
    
    def get(self, request):
        form = CSVImportPostnameForm()
        return render(request, 'reference/postname_csv_import.html', {'form': form})
    
    def post(self, request):
        form = CSVImportPostnameForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                decoded_file = csv_file.read().decode('utf-8-sig')
                lines = decoded_file.strip().splitlines()
                
                if not lines:
                    messages.error(request, 'Файл пуст.')
                    return render(request, 'reference/postname_csv_import.html', {'form': form})
                
                imported = 0
                errors = []
                
                # Определяем, есть ли заголовок
                first_line_lower = lines[0].lower()
                has_header = 'название' in first_line_lower or 'name' in first_line_lower
                
                if has_header:
                    csv_reader = csv.DictReader(lines, delimiter=';')
                    start_row = 2
                else:
                    csv_reader = csv.reader(lines, delimiter=';')
                    start_row = 1
                
                for row_num, row_data in enumerate(csv_reader, start=start_row):
                    try:
                        if has_header:
                            row = row_data
                            name = row.get('Название', '').strip()
                            code = row.get('Код', '').strip()
                            sorting = row.get('Код сортировки', '').strip()
                            description = row.get('Описание', '').strip()
                            category = row.get('Категория', '').strip()
                        else:
                            if len(row_data) < 2:
                                errors.append(f"Строка {row_num}: недостаточно данных (нужно минимум 2 поля)")
                                continue
                            name = row_data[0].strip() if len(row_data) > 0 else ''
                            code = row_data[1].strip() if len(row_data) > 1 else ''
                            sorting = row_data[2].strip() if len(row_data) > 2 else ''
                            description = row_data[3].strip() if len(row_data) > 3 else ''
                            category = row_data[4].strip() if len(row_data) > 4 else ''
                        
                        # Валидация обязательных полей
                        if not name or not code:
                            errors.append(f"Строка {row_num}: отсутствует название или код")
                            continue
                        
                        # Проверка уникальности кода
                        if Postname.objects.filter(code=code).exists():
                            errors.append(f"Строка {row_num}: должность с кодом '{code}' уже существует")
                            continue
                        
                        # Создаем должность
                        Postname.objects.create(
                            name=name,
                            code=code,
                            sorting=sorting,
                            description=description,
                            category=category,
                            is_active=True
                        )
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Строка {row_num}: ошибка при обработке - {str(e)}")
                
                if imported > 0:
                    messages.success(request, f'Успешно импортировано должностей: {imported}')
                if errors:
                    for error in errors[:20]:
                        messages.warning(request, error)
                    if len(errors) > 20:
                        messages.warning(request, f'... и еще {len(errors) - 20} ошибок')
                
                if imported == 0 and not errors:
                    messages.info(request, 'Нет данных для импорта. Проверьте формат файла.')
                
                return redirect('reference:postname_list')
                
            except UnicodeDecodeError:
                messages.error(request, 'Ошибка кодировки файла. Убедитесь, что файл в кодировке UTF-8.')
                return render(request, 'reference/postname_csv_import.html', {'form': form})
            except Exception as e:
                messages.error(request, f'Ошибка при чтении файла: {str(e)}')
                return render(request, 'reference/postname_csv_import.html', {'form': form})
        
        for field, field_errors in form.errors.items():
            for error in field_errors:
                messages.error(request, f'{field}: {error}')
        
        return render(request, 'reference/postname_csv_import.html', {'form': form})


class PostnameCSVTemplateView(LoginRequiredMixin, View):
    """Генерация шаблона CSV файла для импорта должностей"""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="postnames_template.csv"'
        
        writer = csv.writer(response, delimiter=';')
        
        writer.writerow(['Название', 'Код', 'Код сортировки', 'Описание', 'Категория'])
        
        writer.writerow(['Директор', 'DIR001', 'DIR', 'Руководитель организации', 'Руководящий состав'])
        writer.writerow(['Бухгалтер', 'ACC001', 'ACC', 'Специалист по ведению учета', 'Финансовый отдел'])
        
        return response


class ITAssetListView(LoginRequiredMixin, ListView):
    """Список информационных активов"""
    model = ITAsset
    template_name = 'reference/itasset_list.html'
    context_object_name = 'assets'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ITAsset.objects.filter(is_active=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class ITAssetDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация об информационном активе"""
    model = ITAsset
    template_name = 'reference/itasset_detail.html'
    context_object_name = 'asset'


class ITAssetCreateView(LoginRequiredMixin, CreateView):
    """Создание нового информационного актива"""
    model = ITAsset
    form_class = ITAssetForm
    template_name = 'reference/itasset_form.html'
    success_url = reverse_lazy('reference:itasset_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Информационный актив успешно создан.')
        return super().form_valid(form)


class ITAssetUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование информационного актива"""
    model = ITAsset
    form_class = ITAssetForm
    template_name = 'reference/itasset_form.html'
    success_url = reverse_lazy('reference:itasset_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Информационный актив успешно обновлен.')
        return super().form_valid(form)


class ITAssetDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление информационного актива"""
    model = ITAsset
    template_name = 'reference/itasset_confirm_delete.html'
    success_url = reverse_lazy('reference:itasset_list')
    login_url = '/testing/moderator/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Информационный актив успешно удален.')
        return super().delete(request, *args, **kwargs)


# ========== CertificateType Views ==========

class CertificateTypeListView(LoginRequiredMixin, ListView):
    """Список типов сертификатов"""
    model = CertificateType
    template_name = 'reference/certificate_type_list.html'
    context_object_name = 'cert_types'
    paginate_by = 20
    login_url = '/testing/moderator/login/'
    
    def get_queryset(self):
        queryset = CertificateType.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class CertificateTypeCreateView(LoginRequiredMixin, CreateView):
    """Создание нового типа сертификата"""
    model = CertificateType
    form_class = CertificateTypeForm
    template_name = 'reference/certificate_type_form.html'
    success_url = reverse_lazy('reference:certificate_type_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Тип сертификата успешно создан.')
        return super().form_valid(form)


class CertificateTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование типа сертификата"""
    model = CertificateType
    form_class = CertificateTypeForm
    template_name = 'reference/certificate_type_form.html'
    success_url = reverse_lazy('reference:certificate_type_list')
    login_url = '/testing/moderator/login/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Тип сертификата успешно обновлен.')
        return super().form_valid(form)


class CertificateTypeDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление типа сертификата"""
    model = CertificateType
    template_name = 'reference/certificate_type_confirm_delete.html'
    success_url = reverse_lazy('reference:certificate_type_list')
    login_url = '/testing/moderator/login/'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Тип сертификата успешно удален.')
        return super().delete(request, *args, **kwargs)
