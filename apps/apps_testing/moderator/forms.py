# apps_testing/moderator/forms.py
from django import forms
from django.utils import timezone
from apps.apps_testing.tests.models import Test, QuestionSet, Question, TestSession
from apps.reference.models import Departments
from django.contrib.auth.forms import AuthenticationForm


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = '__all__' # Или перечислите поля явно для лучшего контроля
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'password': forms.PasswordInput(render_value=True, attrs={'class': 'form-control'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'questions_per_set': forms.NumberInput(attrs={'class': 'form-control'}),
            'question_sets': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}), # Bootstrap стилизует это через родительские классы
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.errors:
            if field_name in self.fields:
                widget = self.fields[field_name].widget
                current_class = widget.attrs.get('class', '')
                # CheckboxInput и SelectMultiple могут не требовать 'is-invalid' напрямую на инпуте
                # или это обрабатывается Bootstrap иначе. Для простоты, пока добавляем.
                if not isinstance(widget, (forms.CheckboxInput, forms.SelectMultiple)):
                    if 'is-invalid' not in current_class.split():
                        widget.attrs['class'] = f'{current_class} is-invalid'.strip()
                elif isinstance(widget, forms.SelectMultiple): # Для SelectMultiple 'is-invalid' полезен
                     if 'is-invalid' not in current_class.split():
                        widget.attrs['class'] = f'{current_class} is-invalid'.strip()

class QuestionSetForm(forms.ModelForm):
    csv_file = forms.FileField(required=False, help_text='CSV с разделителем ; : вопрос; ответ1; ответ2; ответ3; ответ4; номер правильного ответа (1-4)')
    has_header = forms.BooleanField(required=False, initial=True, label='CSV содержит заголовок')
    class Meta:
        model = QuestionSet
        fields = '__all__' # title, description
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.errors:
            if field_name in self.fields:
                widget = self.fields[field_name].widget
                current_class = widget.attrs.get('class', '')
                if 'is-invalid' not in current_class.split():
                    widget.attrs['class'] = f'{current_class} is-invalid'.strip()

    def clean_csv_file(self):
        f = self.cleaned_data.get('csv_file')
        if not f:
            return f
        # Basic validation: ensure small size and CSV-like content type
        if hasattr(f, 'content_type') and f.content_type not in ('text/csv', 'application/vnd.ms-excel', 'application/csv', 'text/plain'):
            raise forms.ValidationError('Загрузите CSV файл.')
        return f


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        # Мы явно перечисляем поля, чтобы контролировать их порядок
        fields = ['text', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,  # Сделаем поле для текста вопроса побольше
                'placeholder': 'Введите текст вопроса...'
            }),
            'option_1': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,  # Сделаем поле для текста вопроса побольше
                'placeholder': 'Вариант ответа 1'
            }),
            'option_2': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,  # Сделаем поле для текста вопроса побольше
                'placeholder': 'Вариант ответа 2'
            }),
            'option_3': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,  # Сделаем поле для текста вопроса побольше
                'placeholder': 'Вариант ответа 3'
            }),
            'option_4': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,  # Сделаем поле для текста вопроса побольше
                'placeholder': 'Вариант ответа 4'
            }),
            'correct_option': forms.Select(attrs={
                'class': 'form-select'  # Для <select> в Bootstrap используется класс form-select
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Переопределяем init для добавления класса is-invalid к полям с ошибками.
        """
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if self.errors.get(field_name):
                # Добавляем класс 'is-invalid' к виджету поля с ошибкой
                current_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f'{current_class} is-invalid'.strip()

    def clean(self):
        """
        Добавляем валидацию на уровне всей формы.
        Проверяем, что текст правильного ответа не пустой.
        """
        cleaned_data = super().clean()
        correct_option_num = cleaned_data.get("correct_option")

        if correct_option_num:
            option_field_name = f'option_{correct_option_num}'
            option_text = cleaned_data.get(option_field_name)

            if not option_text:
                self.add_error(option_field_name, "Поле с правильным вариантом ответа не может быть пустым.")

        return cleaned_data


class ModeratorLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Имя пользователя'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Пароль'}
        )
        # Добавляем 'is-invalid' для полей с ошибками
        for field_name in self.errors:
            if field_name in self.fields:
                widget = self.fields[field_name].widget
                current_class = widget.attrs.get('class', '')
                if 'is-invalid' not in current_class.split():
                    widget.attrs['class'] = f'{current_class} is-invalid'.strip()


class QuestionErrorAnalyticsForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    test = forms.ModelChoiceField(
        queryset=Test.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    question_set = forms.ModelChoiceField(
        queryset=QuestionSet.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    include_all_sets = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and start > end:
            self.add_error('end_date', 'Дата окончания раньше даты начала.')
        # Provide defaults for convenience
        if not end:
            end = timezone.localdate()
            cleaned['end_date'] = end
        if not start:
            cleaned['start_date'] = end - timezone.timedelta(days=30)
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Narrow question_set choices based on selected test (if provided)
        data = self.data or None
        test_id = None
        if data:
            test_id = data.get('test') or data.get('test_id')
        elif self.initial:
            test_id = self.initial.get('test')
        if test_id:
            try:
                test_obj = Test.objects.filter(pk=test_id).first()
                if test_obj:
                    self.fields['question_set'].queryset = test_obj.question_sets.all()
            except Exception:
                pass


class ResultsFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    participant = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия или имя'})
    )
    test = forms.ModelChoiceField(
        queryset=Test.objects.all(),
        required=False,
        empty_label='Все тесты',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ip_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IP-адрес'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.all(),
        required=False,
        empty_label='Все подразделения',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        if date_from and date_to and date_from > date_to:
            self.add_error('date_to', 'Дата окончания раньше даты начала.')
        return cleaned