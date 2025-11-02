from django import forms
from .models import Departments, Postname, ITAsset


class DepartmentForm(forms.ModelForm):
    """Форма для создания и редактирования подразделений"""
    
    class Meta:
        model = Departments
        fields = ['name', 'code', 'sorting', 'description', 'parent', 'is_logical', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'sorting': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'is_logical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['sorting'].required = False
        self.fields['parent'].required = False
        self.fields['parent'].queryset = Departments.objects.filter(is_active=True)
        
        # Исключаем текущий объект из списка возможных родителей
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Departments.objects.filter(
                is_active=True
            ).exclude(pk=self.instance.pk)


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

