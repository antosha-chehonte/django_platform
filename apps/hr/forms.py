from django import forms

from .models import Employees, Posts


class HireNewEmployeeForm(forms.ModelForm):
    start_date = forms.DateField(label='Дата начала', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Employees
        fields = ['last_name', 'first_name', 'middle_name', 'full_name_accusative', 'birth_date', 'gender', 'work_phone', 'mobile_phone', 'ip_phone', 'email', 'appointment_date', 'appointment_order_date', 'appointment_order_number']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_accusative': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_order_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AssignExistingEmployeeForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employees.objects.none(),
        label='Сотрудник (уволен)'
    )
    start_date = forms.DateField(label='Дата начала', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employees.objects.filter(is_active=False)
        self.fields['employee'].widget.attrs.update({'class': 'form-select'})


class MoveEmployeeForm(forms.Form):
    department = forms.ModelChoiceField(
        queryset=None,
        label='Подразделение',
        required=True,
        empty_label='Выберите подразделение'
    )
    target_post = forms.ModelChoiceField(
        queryset=Posts.objects.none(),
        label='Новая позиция',
        required=True,
        empty_label='Сначала выберите подразделение'
    )
    start_date = forms.DateField(label='Дата начала', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        from apps.reference.models import Departments
        # Извлекаем исходную позицию из kwargs, если она передана
        self.source_post = kwargs.pop('source_post', None)
        
        super().__init__(*args, **kwargs)
        # Получаем подразделения, где есть вакантные позиции
        departments_with_vacancies = Departments.objects.filter(
            posts__status=Posts.STATUS_VACANT,
            posts__is_active=True
        ).distinct().order_by('sorting', 'name')
        
        self.fields['department'].queryset = departments_with_vacancies
        self.fields['department'].widget.attrs.update({'class': 'form-select', 'id': 'id_department'})
        self.fields['target_post'].widget.attrs.update({'class': 'form-select', 'id': 'id_target_post'})
        
        # Если форма была отправлена и есть department, обновляем queryset для target_post
        department_id = None
        if self.is_bound and 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
            except (ValueError, TypeError):
                pass
        
        if department_id:
            queryset = Posts.objects.filter(
                department_id=department_id,
                status=Posts.STATUS_VACANT,
                is_active=True
            ).select_related('postname', 'department').order_by('postname__name')
            
            # Исключаем исходную позицию, если она указана
            if self.source_post:
                queryset = queryset.exclude(pk=self.source_post.pk)
            
            self.fields['target_post'].queryset = queryset
        else:
            # Если department не выбран, оставляем queryset пустым, но не disabled
            # JavaScript будет управлять disabled состоянием
            self.fields['target_post'].queryset = Posts.objects.none()


class FreePositionForm(forms.Form):
    end_date = forms.DateField(
        label='Дата освобождения должности',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        # Устанавливаем текущую дату по умолчанию, если форма не заполнена
        if not self.is_bound:
            self.fields['end_date'].initial = timezone.localdate()


class EmployeesForm(forms.ModelForm):
    class Meta:
        model = Employees
        fields = ['last_name', 'first_name', 'middle_name', 'full_name_accusative', 'birth_date', 'gender', 'work_phone', 'mobile_phone', 'ip_phone', 'email', 'appointment_date', 'appointment_order_date', 'appointment_order_number']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_accusative': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'appointment_order_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PostsForm(forms.ModelForm):
    class Meta:
        model = Posts
        fields = ['department', 'postname', 'is_active']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'postname': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Файл должен содержать колонки: Фамилия;Имя;Отчество;ФИО в винительном падеже (опционально);Дата рождения (YYYY-MM-DD);Пол (M/F);Рабочий телефон;Мобильный телефон;IP-телефон (опционально);Email;Дата назначения (YYYY-MM-DD);Дата приказа (YYYY-MM-DD);Номер приказа',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )


class PostsCSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Файл должен содержать колонки: Должность;Подразделение;Сотрудник (ФИО, опционально);Статус (vacant/occupied, опционально);Активна (True/False, опционально)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
