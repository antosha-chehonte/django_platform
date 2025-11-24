from django import forms
from django.core.exceptions import ValidationError
from .models import SystemAccess, DigitalSignature
from apps.reference.models import CertificateType
from .utils.certificate_parser import parse_certificate_from_django_file, CertificateParseError


class MultipleFileInput(forms.FileInput):
    """Кастомный виджет для множественной загрузки файлов"""
    def __init__(self, attrs=None):
        # Убираем multiple из attrs перед передачей в родительский класс
        # чтобы избежать ошибки валидации
        if attrs and 'multiple' in attrs:
            attrs = attrs.copy()
            attrs.pop('multiple', None)
        super().__init__(attrs=attrs)
        # Сохраняем, что нужно добавить multiple
        self.allow_multiple = True
    
    def render(self, name, value, attrs=None, renderer=None):
        # Добавляем атрибут multiple при рендеринге
        if attrs is None:
            attrs = {}
        attrs = attrs.copy()
        attrs['multiple'] = True
        return super().render(name, value, attrs, renderer)


class SystemAccessForm(forms.ModelForm):
    class Meta:
        model = SystemAccess
        fields = [
            'employee', 'system', 'login', 'status',
            'access_granted_date', 'access_blocked_date', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'system': forms.Select(attrs={'class': 'form-select'}),
            'login': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'access_granted_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'access_blocked_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DigitalSignatureForm(forms.ModelForm):
    auto_fill_from_certificate = forms.BooleanField(
        required=False,
        initial=True,
        label='Автоматически заполнить данные из файла сертификата',
        help_text='При загрузке файла .cer или .pfx поля будут автоматически заполнены',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = DigitalSignature
        fields = [
            'employee', 'certificate_type', 'certificate_serial', 'certificate_alias',
            'expiry_date', 'carrier_serial', 'certificate_file', 'status', 'notes'
        ]
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'certificate_type': forms.Select(attrs={'class': 'form-select'}),
            'certificate_serial': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_alias': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'carrier_serial': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.cer,.pfx'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если это редактирование существующей записи, скрываем чекбокс автозаполнения
        if self.instance and self.instance.pk:
            self.fields['auto_fill_from_certificate'].widget = forms.HiddenInput()
            self.fields['auto_fill_from_certificate'].initial = False
    
    def clean(self):
        """Валидация всей формы и автоматическое заполнение полей из сертификата"""
        cleaned_data = super().clean()
        certificate_file = cleaned_data.get('certificate_file')
        auto_fill = cleaned_data.get('auto_fill_from_certificate', True)
        
        if certificate_file and auto_fill:
            try:
                # Парсим сертификат
                cert_data = parse_certificate_from_django_file(certificate_file)
                
                # Автоматически заполняем поля, если они пустые
                if not cleaned_data.get('certificate_serial'):
                    cleaned_data['certificate_serial'] = cert_data['certificate_serial']
                
                if not cleaned_data.get('certificate_alias'):
                    cleaned_data['certificate_alias'] = cert_data['certificate_alias']
                
                if not cleaned_data.get('expiry_date'):
                    cleaned_data['expiry_date'] = cert_data['expiry_date']
                
                # Сохраняем информацию о субъекте для возможного использования
                if cert_data.get('subject_name'):
                    # Добавляем информацию в notes, если она пустая
                    if not cleaned_data.get('notes'):
                        notes = f"Сертификат выдан: {cert_data['subject_name']}"
                        if cert_data.get('issuer_name'):
                            notes += f"\nИздатель: {cert_data['issuer_name']}"
                        cleaned_data['notes'] = notes
                
                # Автоматически устанавливаем статус в зависимости от срока действия
                # Устанавливаем статус всегда, если загружен файл сертификата
                from django.utils import timezone
                today = timezone.now().date()
                expiry_date = cert_data['expiry_date']
                
                # Вычисляем количество дней до истечения
                days_until_expiry = (expiry_date - today).days
                
                if expiry_date < today:
                    # Сертификат уже истек
                    cleaned_data['status'] = DigitalSignature.STATUS_NEEDS_UPDATE
                elif days_until_expiry <= 30:
                    # Сертификат истекает в течение месяца
                    cleaned_data['status'] = DigitalSignature.STATUS_NEEDS_UPDATE
                else:
                    # Сертификат действителен
                    cleaned_data['status'] = DigitalSignature.STATUS_ACTIVE
                
            except CertificateParseError as e:
                # Не блокируем сохранение, но добавляем ошибку к полю файла
                self.add_error(
                    'certificate_file',
                    f"Не удалось автоматически извлечь данные: {str(e)}. "
                    "Вы можете заполнить поля вручную."
                )
            except Exception as e:
                # Для других ошибок также показываем предупреждение
                self.add_error(
                    'certificate_file',
                    f"Ошибка при обработке файла: {str(e)}. "
                    "Проверьте формат файла или заполните поля вручную."
                )
        
        return cleaned_data


class BulkCertificateUploadForm(forms.Form):
    """Форма для массовой загрузки сертификатов"""
    certificate_files = forms.FileField(
        label='Файлы сертификатов',
        help_text='Выберите один или несколько файлов сертификатов (.cer или .pfx). Максимальный размер каждого файла: 1 МБ',
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.cer,.pfx'
        }),
        required=False  # Валидация будет в view
    )
    certificate_type = forms.ModelChoiceField(
        queryset=CertificateType.objects.filter(is_active=True),
        label='Тип сертификата',
        help_text='Выберите тип сертификата для всех загружаемых файлов (опционально)',
        required=False,
        empty_label='-- Не указан --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class CertificateImportForm(forms.Form):
    """Форма для импорта сертификатов из HTML-файла"""
    html_file = forms.FileField(
        label='HTML-файл',
        help_text='Выберите HTML-файл с информацией о сертификатах',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.html,.htm'
        }),
        required=True
    )
    certificate_type = forms.ModelChoiceField(
        queryset=CertificateType.objects.filter(is_active=True),
        label='Тип сертификата (опционально)',
        help_text='Если указан, будет использован для всех сертификатов вместо типа из HTML',
        required=False,
        empty_label='-- Использовать тип из HTML --',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean_html_file(self):
        """Валидация HTML-файла"""
        html_file = self.cleaned_data.get('html_file')
        
        if not html_file:
            raise ValidationError('Необходимо выбрать HTML-файл')
        
        # Проверка расширения файла
        filename = html_file.name.lower()
        if not (filename.endswith('.html') or filename.endswith('.htm')):
            raise ValidationError('Файл должен иметь расширение .html или .htm')
        
        # Проверка, что файл не пустой
        if html_file.size == 0:
            raise ValidationError('Файл не может быть пустым')
        
        return html_file

