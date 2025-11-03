from django import forms
from .models import Departments, Postname, ITAsset, CertificateType


class DepartmentForm(forms.ModelForm):
    """Форма для создания и редактирования подразделений"""
    
    class Meta:
        model = Departments
        fields = [
            'name', 'code', 'sorting', 'description',
            'dep_short_name', 'email',
            'zipcode', 'city', 'street', 'bldg',
            'net_id', 'ip', 'mask',
            'parent', 'is_logical', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'sorting': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dep_short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'bldg': forms.TextInput(attrs={'class': 'form-control'}),
            'net_id': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '4',
                'pattern': '[A-Za-z0-9]{1,4}'
            }),
            'ip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '192.168.1.0'
            }),
            'mask': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '32',
                'placeholder': '24'
            }),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'is_logical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['sorting'].required = False
        self.fields['dep_short_name'].required = False
        self.fields['email'].required = False
        self.fields['zipcode'].required = False
        self.fields['city'].required = False
        self.fields['street'].required = False
        self.fields['bldg'].required = False
        self.fields['net_id'].required = False
        self.fields['ip'].required = False
        self.fields['mask'].required = False
        self.fields['parent'].required = False
        self.fields['parent'].queryset = Departments.objects.filter(is_active=True)
        
        # Исключаем текущий объект из списка возможных родителей
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Departments.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk)
    
    def clean_net_id(self):
        """Валидация net_id - максимум 4 символа"""
        net_id = self.cleaned_data.get('net_id')
        if net_id and len(net_id) > 4:
            raise forms.ValidationError('Идентификатор сетевого узла должен содержать не более 4 символов')
        return net_id
    
    def clean_mask(self):
        """Валидация mask - диапазон 0-32"""
        mask = self.cleaned_data.get('mask')
        if mask is not None and (mask < 0 or mask > 32):
            raise forms.ValidationError('Маска подсети должна быть в диапазоне от 0 до 32')
        return mask


class PostnameForm(forms.ModelForm):
    """Форма для создания и редактирования должностей"""
    
    class Meta:
        model = Postname
        fields = ['name', 'code', 'sorting', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'sorting': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['category'].required = False


class CSVImportPostnameForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Файл должен содержать колонки: Название;Код;Код сортировки;Описание;Категория',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )


class CSVImportDepartmentForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Файл должен содержать колонки: Название;Код;Код сортировки;Описание;Короткое наименование;Email;Почтовый индекс;Город;Улица;Здание;Идентификатор узла;IP адрес;Маска;Родительское подразделение;Логическое;Активно',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )


class ITAssetForm(forms.ModelForm):
    """Форма для создания и редактирования информационных активов"""
    
    class Meta:
        model = ITAsset
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False


class CertificateTypeForm(forms.ModelForm):
    """Форма для создания и редактирования типов сертификатов"""
    
    class Meta:
        model = CertificateType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False

