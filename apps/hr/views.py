from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, View, CreateView, UpdateView, DeleteView
from django.http import HttpResponse

from .models import Posts, Employees, PositionHistory
from .forms import HireNewEmployeeForm, AssignExistingEmployeeForm, MoveEmployeeForm, PostsForm, CSVImportForm, PostsCSVImportForm
from apps.reference.models import Postname, Departments
import csv
from datetime import datetime


@login_required
def hr_home(request):
    """Главная страница управления персоналом"""
    return render(request, 'hr/index.html')


class PostsListView(LoginRequiredMixin, ListView):
    model = Posts
    template_name = 'hr/posts_list.html'
    context_object_name = 'posts'


class PostsDetailView(LoginRequiredMixin, DetailView):
    model = Posts
    template_name = 'hr/posts_detail.html'
    context_object_name = 'post'


class HireNewEmployeeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = HireNewEmployeeForm()
        return render(request, 'hr/actions/hire_new_employee.html', {'form': form, 'post': post})

    def post(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = HireNewEmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=True)
            start_date = form.cleaned_data['start_date']
            # назначаем
            post.employee = employee
            post.status = Posts.STATUS_OCCUPIED
            post.full_clean()
            post.save()
            # обновляем статус сотрудника
            employee.is_active = True
            employee.save(update_fields=['is_active'])
            # история
            PositionHistory.objects.create(
                employee=employee,
                post=post,
                action=PositionHistory.ACTION_HIRE,
                start_date=start_date,
            )
            messages.success(request, 'Сотрудник принят и назначен на позицию.')
            return redirect('hr:post_detail', pk=post.pk)
        return render(request, 'hr/actions/hire_new_employee.html', {'form': form, 'post': post})


class AssignExistingEmployeeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = AssignExistingEmployeeForm()
        return render(request, 'hr/actions/assign_existing_employee.html', {'form': form, 'post': post})

    def post(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = AssignExistingEmployeeForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data['employee']
            start_date = form.cleaned_data['start_date']
            post.employee = employee
            post.status = Posts.STATUS_OCCUPIED
            post.full_clean()
            post.save()
            employee.is_active = True
            employee.save(update_fields=['is_active'])
            PositionHistory.objects.create(
                employee=employee,
                post=post,
                action=PositionHistory.ACTION_RETURN,
                start_date=start_date,
            )
            messages.success(request, 'Сотрудник возвращен на позицию.')
            return redirect('hr:post_detail', pk=post.pk)
        return render(request, 'hr/actions/assign_existing_employee.html', {'form': form, 'post': post})


class MoveEmployeeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        form = MoveEmployeeForm()
        return render(request, 'hr/actions/move_employee.html', {'form': form, 'post': post})

    def post(self, request, pk):
        source_post = get_object_or_404(Posts, pk=pk)
        form = MoveEmployeeForm(request.POST)
        if form.is_valid():
            target_post = form.cleaned_data['target_post']
            start_date = form.cleaned_data['start_date']

            employee = source_post.employee
            if not employee:
                messages.error(request, 'На исходной позиции нет сотрудника.')
                return redirect('hr:post_detail', pk=source_post.pk)

            # закрываем историю по source
            PositionHistory.objects.filter(employee=employee, post=source_post, end_date__isnull=True).update(end_date=start_date)
            # освобождаем source
            source_post.employee = None
            source_post.status = Posts.STATUS_VACANT
            source_post.save()

            # назначаем в target
            target_post.employee = employee
            target_post.status = Posts.STATUS_OCCUPIED
            target_post.full_clean()
            target_post.save()

            PositionHistory.objects.create(
                employee=employee,
                post=target_post,
                action=PositionHistory.ACTION_MOVE,
                start_date=start_date,
            )

            messages.success(request, 'Сотрудник перемещен на новую позицию.')
            return redirect('hr:post_detail', pk=target_post.pk)
        return render(request, 'hr/actions/move_employee.html', {'form': form, 'post': source_post})


class FreePositionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Posts, pk=pk)
        employee = post.employee
        if not employee:
            messages.info(request, 'Позиция уже вакантна.')
            return redirect('hr:post_detail', pk=pk)

        # прекращаем активную запись history
        PositionHistory.objects.filter(employee=employee, post=post, end_date__isnull=True).update(end_date=request.POST.get('end_date'))

        # увольняем: позицию освобождаем, сотрудника делаем неактивным
        post.employee = None
        post.status = Posts.STATUS_VACANT
        post.save()

        employee.is_active = False
        employee.save(update_fields=['is_active'])

        PositionHistory.objects.create(
            employee=employee,
            post=post,
            action=PositionHistory.ACTION_DISMISS,
            start_date=request.POST.get('end_date'),
            end_date=request.POST.get('end_date'),
        )

        messages.success(request, 'Позиция освобождена, сотрудник уволен.')
        return redirect('hr:post_detail', pk=pk)


class EmployeesListView(LoginRequiredMixin, ListView):
    model = Employees
    template_name = 'hr/employees_list.html'
    context_object_name = 'employees'
    paginate_by = 20


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employees
    template_name = 'hr/employee_detail.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем доступы к системам
        from apps.access_management.models import SystemAccess, DigitalSignature
        context['system_accesses'] = SystemAccess.objects.filter(employee=self.object).select_related('system')
        context['digital_signatures'] = DigitalSignature.objects.filter(employee=self.object).select_related('certificate_type')
        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employees
    from .forms import EmployeesForm
    form_class = EmployeesForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employees')

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно создан.')
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employees
    from .forms import EmployeesForm
    form_class = EmployeesForm
    template_name = 'hr/employee_form.html'
    success_url = reverse_lazy('hr:employees')

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно обновлен.')
        return super().form_valid(form)


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employees
    template_name = 'hr/employee_confirm_delete.html'
    success_url = reverse_lazy('hr:employees')

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Сотрудник успешно удален.')
        return super().post(request, *args, **kwargs)


class EmployeeCSVImportView(LoginRequiredMixin, View):
    """Импорт сотрудников из CSV файла"""
    
    def get(self, request):
        form = CSVImportForm()
        return render(request, 'hr/employee_csv_import.html', {'form': form})
    
    def post(self, request):
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                # Декодируем файл с учетом кодировки
                decoded_file = csv_file.read().decode('utf-8-sig')
                lines = decoded_file.strip().splitlines()
                
                if not lines:
                    messages.error(request, 'Файл пуст.')
                    return render(request, 'hr/employee_csv_import.html', {'form': form})
                
                imported = 0
                errors = []
                
                # Определяем, есть ли заголовок
                # Если первая строка содержит "Фамилия" или похожие слова, считаем её заголовком
                first_line_lower = lines[0].lower()
                has_header = 'фамилия' in first_line_lower or 'last' in first_line_lower
                
                if has_header:
                    # Используем DictReader с заголовком
                    csv_reader = csv.DictReader(lines, delimiter=';')
                    start_row = 2
                else:
                    # Используем обычный reader, предполагаем порядок: Фамилия, Имя, Отчество, Дата рождения, Пол, Рабочий телефон, Мобильный телефон, Email, Дата назначения, Дата приказа, Номер приказа
                    csv_reader = csv.reader(lines, delimiter=';')
                    start_row = 1
                
                for row_num, row_data in enumerate(csv_reader, start=start_row):
                    try:
                        if has_header:
                            # DictReader возвращает словарь
                            row = row_data
                            last_name = row.get('Фамилия', '').strip()
                            first_name = row.get('Имя', '').strip()
                            middle_name = row.get('Отчество', '').strip()
                            birth_date_str = row.get('Дата рождения', '').strip()
                            gender = row.get('Пол', '').strip().upper()
                            work_phone = row.get('Рабочий телефон', row.get('Телефон', '')).strip()  # Поддержка старого названия
                            mobile_phone = row.get('Мобильный телефон', '').strip()
                            email = row.get('Email', '').strip()
                            appointment_date_str = row.get('Дата назначения', '').strip()
                            appointment_order_date_str = row.get('Дата приказа', '').strip()
                            appointment_order_number = row.get('Номер приказа', '').strip()
                        else:
                            # Обычный reader возвращает список
                            if len(row_data) < 4:
                                errors.append(f"Строка {row_num}: недостаточно данных (нужно минимум 4 поля)")
                                continue
                            last_name = row_data[0].strip() if len(row_data) > 0 else ''
                            first_name = row_data[1].strip() if len(row_data) > 1 else ''
                            middle_name = row_data[2].strip() if len(row_data) > 2 else ''
                            birth_date_str = row_data[3].strip() if len(row_data) > 3 else ''
                            gender = (row_data[4].strip().upper() if len(row_data) > 4 else '')
                            work_phone = row_data[5].strip() if len(row_data) > 5 else ''
                            mobile_phone = row_data[6].strip() if len(row_data) > 6 else ''
                            email = row_data[7].strip() if len(row_data) > 7 else ''
                            appointment_date_str = row_data[8].strip() if len(row_data) > 8 else ''
                            appointment_order_date_str = row_data[9].strip() if len(row_data) > 9 else ''
                            appointment_order_number = row_data[10].strip() if len(row_data) > 10 else ''
                        
                        # Валидация обязательных полей
                        if not last_name or not first_name:
                            errors.append(f"Строка {row_num}: отсутствует фамилия или имя")
                            continue
                        
                        if not birth_date_str:
                            errors.append(f"Строка {row_num}: отсутствует дата рождения")
                            continue
                        
                        # Парсим дату
                        try:
                            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Строка {row_num}: неверный формат даты рождения. Ожидается YYYY-MM-DD, получено: {birth_date_str}")
                            continue
                        
                        # Валидация пола
                        if gender not in ['M', 'F']:
                            errors.append(f"Строка {row_num}: неверное значение пола (должно быть M или F), получено: {gender}")
                            continue
                        
                        # Парсим дату назначения (опционально)
                        appointment_date = None
                        if appointment_date_str:
                            try:
                                appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
                            except ValueError:
                                errors.append(f"Строка {row_num}: неверный формат даты назначения. Ожидается YYYY-MM-DD, получено: {appointment_date_str}")
                                continue
                        
                        # Парсим дату приказа (опционально)
                        appointment_order_date = None
                        if appointment_order_date_str:
                            try:
                                appointment_order_date = datetime.strptime(appointment_order_date_str, '%Y-%m-%d').date()
                            except ValueError:
                                errors.append(f"Строка {row_num}: неверный формат даты приказа. Ожидается YYYY-MM-DD, получено: {appointment_order_date_str}")
                                continue
                        
                        # Создаем сотрудника
                        employee = Employees.objects.create(
                            last_name=last_name,
                            first_name=first_name,
                            middle_name=middle_name,
                            birth_date=birth_date,
                            gender=gender,
                            work_phone=work_phone if work_phone else '',
                            mobile_phone=mobile_phone if mobile_phone else '',
                            email=email if email else '',
                            appointment_date=appointment_date,
                            appointment_order_date=appointment_order_date,
                            appointment_order_number=appointment_order_number if appointment_order_number else '',
                            is_active=True
                        )
                        imported += 1
                        
                    except Exception as e:
                        errors.append(f"Строка {row_num}: ошибка при обработке - {str(e)}")
                
                if imported > 0:
                    messages.success(request, f'Успешно импортировано сотрудников: {imported}')
                if errors:
                    for error in errors[:20]:  # Показываем первые 20 ошибок
                        messages.warning(request, error)
                    if len(errors) > 20:
                        messages.warning(request, f'... и еще {len(errors) - 20} ошибок')
                
                if imported == 0 and not errors:
                    messages.info(request, 'Нет данных для импорта. Проверьте формат файла.')
                
                return redirect('hr:employees')
                
            except UnicodeDecodeError:
                messages.error(request, 'Ошибка кодировки файла. Убедитесь, что файл в кодировке UTF-8.')
                return render(request, 'hr/employee_csv_import.html', {'form': form})
            except Exception as e:
                messages.error(request, f'Ошибка при чтении файла: {str(e)}')
                return render(request, 'hr/employee_csv_import.html', {'form': form})
        
        # Если форма невалидна, показываем ошибки
        for field, field_errors in form.errors.items():
            for error in field_errors:
                messages.error(request, f'{field}: {error}')
        
        return render(request, 'hr/employee_csv_import.html', {'form': form})


class EmployeeCSVTemplateView(LoginRequiredMixin, View):
    """Генерация шаблона CSV файла для импорта сотрудников"""
    
    def get(self, request):
        # Создаем HTTP ответ с типом CSV без BOM
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="employees_template.csv"'
        
        # Создаем CSV writer
        writer = csv.writer(response, delimiter=';')
        
        # Записываем заголовки
        writer.writerow(['Фамилия', 'Имя', 'Отчество', 'Дата рождения', 'Пол', 'Рабочий телефон', 'Мобильный телефон', 'Email', 'Дата назначения', 'Дата приказа', 'Номер приказа'])
        
        # Добавляем пример данных
        writer.writerow(['Иванов', 'Иван', 'Иванович', '1990-05-15', 'M', '+74951234567', '+79001234567', 'ivanov@example.com', '2024-01-15', '2024-01-10', '123-ОД'])
        writer.writerow(['Петрова', 'Мария', 'Сергеевна', '1985-03-20', 'F', '+74959876543', '+79009876543', 'petrova@example.com', '2024-02-01', '2024-01-25', '45-ОД'])
        
        return response


class PositionHistoryListView(LoginRequiredMixin, ListView):
    model = PositionHistory
    template_name = 'hr/history_list.html'
    context_object_name = 'history'
    paginate_by = 25
    ordering = ['-start_date', '-created_at']

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Posts
    form_class = PostsForm
    template_name = 'hr/post_form.html'
    success_url = reverse_lazy('hr:posts')

    def form_valid(self, form):
        # Новая позиция по умолчанию вакантна
        form.instance.status = Posts.STATUS_VACANT
        messages.success(self.request, 'Штатная позиция создана.')
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Posts
    form_class = PostsForm
    template_name = 'hr/post_form.html'
    success_url = reverse_lazy('hr:posts')

    def form_valid(self, form):
        messages.success(self.request, 'Штатная позиция обновлена.')
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Posts
    template_name = 'hr/post_confirm_delete.html'
    success_url = reverse_lazy('hr:posts')

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Штатная позиция удалена.')
        return super().post(request, *args, **kwargs)


class PostCSVImportView(LoginRequiredMixin, View):
    """Импорт штатных позиций из CSV файла"""
    
    def get(self, request):
        form = PostsCSVImportForm()
        return render(request, 'hr/post_csv_import.html', {'form': form})
    
    def post(self, request):
        form = PostsCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            try:
                # Декодируем файл с учетом кодировки
                decoded_file = csv_file.read().decode('utf-8-sig')
                lines = decoded_file.strip().splitlines()
                
                if not lines:
                    messages.error(request, 'Файл пуст.')
                    return render(request, 'hr/post_csv_import.html', {'form': form})
                
                imported = 0
                errors = []
                
                # Определяем, есть ли заголовок
                first_line_lower = lines[0].lower()
                has_header = 'должность' in first_line_lower or 'подразделение' in first_line_lower or 'post' in first_line_lower
                
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
                            postname_str = row.get('Должность', '').strip()
                            department_str = row.get('Подразделение', '').strip()
                            employee_str = row.get('Сотрудник', '').strip()
                            status_str = row.get('Статус', '').strip().lower()
                            is_active_str = row.get('Активна', '').strip()
                        else:
                            if len(row_data) < 2:
                                errors.append(f"Строка {row_num}: недостаточно данных (нужно минимум 2 поля: Должность, Подразделение)")
                                continue
                            postname_str = row_data[0].strip() if len(row_data) > 0 else ''
                            department_str = row_data[1].strip() if len(row_data) > 1 else ''
                            employee_str = row_data[2].strip() if len(row_data) > 2 else ''
                            status_str = row_data[3].strip().lower() if len(row_data) > 3 else ''
                            is_active_str = row_data[4].strip() if len(row_data) > 4 else ''
                        
                        # Валидация обязательных полей
                        if not postname_str:
                            errors.append(f"Строка {row_num}: отсутствует должность")
                            continue
                        
                        if not department_str:
                            errors.append(f"Строка {row_num}: отсутствует подразделение")
                            continue
                        
                        # Поиск должности по названию или коду
                        postname = None
                        try:
                            postname = Postname.objects.get(name=postname_str, is_active=True)
                        except Postname.DoesNotExist:
                            try:
                                postname = Postname.objects.get(code=postname_str, is_active=True)
                            except Postname.DoesNotExist:
                                errors.append(f"Строка {row_num}: должность не найдена: {postname_str}")
                                continue
                        
                        # Поиск подразделения по названию или коду
                        department = None
                        try:
                            department = Departments.objects.get(name=department_str, is_active=True)
                        except Departments.DoesNotExist:
                            try:
                                department = Departments.objects.get(code=department_str, is_active=True)
                            except Departments.DoesNotExist:
                                errors.append(f"Строка {row_num}: подразделение не найдено: {department_str}")
                                continue
                        
                        # Поиск сотрудника по ФИО (опционально)
                        employee = None
                        if employee_str:
                            # Разбиваем ФИО на части
                            employee_parts = employee_str.split()
                            if len(employee_parts) >= 2:
                                last_name = employee_parts[0]
                                first_name = employee_parts[1]
                                middle_name = employee_parts[2] if len(employee_parts) > 2 else ''
                                
                                try:
                                    employee = Employees.objects.get(
                                        last_name=last_name,
                                        first_name=first_name,
                                        middle_name=middle_name,
                                        is_active=True
                                    )
                                except Employees.DoesNotExist:
                                    errors.append(f"Строка {row_num}: сотрудник не найден: {employee_str}")
                                    continue
                                except Employees.MultipleObjectsReturned:
                                    # Если несколько сотрудников, берем первого
                                    employee = Employees.objects.filter(
                                        last_name=last_name,
                                        first_name=first_name,
                                        middle_name=middle_name,
                                        is_active=True
                                    ).first()
                                    errors.append(f"Строка {row_num}: найдено несколько сотрудников с ФИО {employee_str}, выбран первый")
                        
                        # Определяем статус
                        status = Posts.STATUS_VACANT
                        if status_str:
                            if status_str in ['occupied', 'занята', 'занято']:
                                status = Posts.STATUS_OCCUPIED
                            elif status_str in ['vacant', 'вакантна', 'вакантно']:
                                status = Posts.STATUS_VACANT
                            else:
                                errors.append(f"Строка {row_num}: неверное значение статуса (должно быть vacant/occupied), получено: {status_str}")
                                continue
                        
                        # Проверяем согласованность статуса и сотрудника
                        if status == Posts.STATUS_OCCUPIED and not employee:
                            errors.append(f"Строка {row_num}: для статуса 'занята' необходимо указать сотрудника")
                            continue
                        
                        if status == Posts.STATUS_VACANT and employee:
                            errors.append(f"Строка {row_num}: для статуса 'вакантна' не должен быть указан сотрудник")
                            continue
                        
                        # Определяем is_active
                        is_active = True
                        if is_active_str:
                            is_active_str_lower = is_active_str.lower()
                            if is_active_str_lower in ['false', '0', 'нет', 'no']:
                                is_active = False
                            elif is_active_str_lower in ['true', '1', 'да', 'yes']:
                                is_active = True
                        
                        # Создаем позицию
                        post = Posts(
                            postname=postname,
                            department=department,
                            employee=employee,
                            status=status,
                            is_active=is_active
                        )
                        try:
                            post.full_clean()
                            post.save()
                            imported += 1
                        except Exception as validation_error:
                            errors.append(f"Строка {row_num}: ошибка валидации - {str(validation_error)}")
                            continue
                        
                    except Exception as e:
                        errors.append(f"Строка {row_num}: ошибка при обработке - {str(e)}")
                
                if imported > 0:
                    messages.success(request, f'Успешно импортировано позиций: {imported}')
                if errors:
                    for error in errors[:20]:
                        messages.warning(request, error)
                    if len(errors) > 20:
                        messages.warning(request, f'... и еще {len(errors) - 20} ошибок')
                
                if imported == 0 and not errors:
                    messages.info(request, 'Нет данных для импорта. Проверьте формат файла.')
                
                return redirect('hr:posts')
                
            except UnicodeDecodeError:
                messages.error(request, 'Ошибка кодировки файла. Убедитесь, что файл в кодировке UTF-8.')
                return render(request, 'hr/post_csv_import.html', {'form': form})
            except Exception as e:
                messages.error(request, f'Ошибка при чтении файла: {str(e)}')
                return render(request, 'hr/post_csv_import.html', {'form': form})
        
        # Если форма невалидна, показываем ошибки
        for field, field_errors in form.errors.items():
            for error in field_errors:
                messages.error(request, f'{field}: {error}')
        
        return render(request, 'hr/post_csv_import.html', {'form': form})


class PostCSVTemplateView(LoginRequiredMixin, View):
    """Генерация шаблона CSV файла для импорта штатных позиций"""
    
    def get(self, request):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="posts_template.csv"'
        
        writer = csv.writer(response, delimiter=';')
        
        # Записываем заголовки
        writer.writerow(['Должность', 'Подразделение', 'Сотрудник', 'Статус', 'Активна'])
        
        # Добавляем пример данных (без сотрудника, вакантная)
        writer.writerow(['Директор', 'Администрация', '', 'vacant', 'True'])
        writer.writerow(['Менеджер', 'Отдел продаж', '', 'vacant', 'True'])
        
        # Пример с сотрудником (если есть доступные)
        try:
            dept = Departments.objects.filter(is_active=True).first()
            postname_obj = Postname.objects.filter(is_active=True).first()
            employee = Employees.objects.filter(is_active=True).first()
            if dept and postname_obj and employee:
                writer.writerow([
                    postname_obj.name,
                    dept.name,
                    f'{employee.last_name} {employee.first_name} {employee.middle_name}'.strip(),
                    'occupied',
                    'True'
                ])
        except:
            pass
        
        return response


