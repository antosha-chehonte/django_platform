from django import forms
from apps.reference.models import ITAsset, Departments, CertificateType


class SystemAccessActiveReportForm(forms.Form):
    """Форма для отчета по активным доступам к системе"""
    system = forms.ModelChoiceField(
        queryset=ITAsset.objects.filter(is_active=True),
        label='Информационная система',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[
            ('active', 'Активные'),
            ('suspended', 'Приостановленные'),
            ('blocked', 'Заблокированные'),
        ],
        initial='active',
        label='Статус доступа',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )


class SystemAccessExpiringReportForm(forms.Form):
    """Форма для отчета по истекающим доступам"""
    report_type = forms.MultipleChoiceField(
        choices=[
            ('needs_update', 'Требуют актуализации'),
            ('expired', 'Просроченные'),
            ('expiring', 'Истекающие'),
        ],
        label='Тип отчета',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        initial=['needs_update', 'expired', 'expiring']
    )
    days = forms.IntegerField(
        label='Период для "истекающих" (дней)',
        initial=40,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class DigitalSignatureActiveReportForm(forms.Form):
    """Форма для отчета по сотрудникам с активной подписью"""
    cert_type = forms.ModelChoiceField(
        queryset=CertificateType.objects.filter(is_active=True),
        label='Тип сертификата',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все типы'
    )
    status = forms.ChoiceField(
        choices=[
            ('active', 'Активные'),
            ('revoked', 'Аннулированные'),
        ],
        initial='active',
        label='Статус подписи',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )


class DigitalSignatureMissingReportForm(forms.Form):
    """Форма для отчета по сотрудникам без подписи"""
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )
    active_only = forms.BooleanField(
        label='Только активные сотрудники',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class DigitalSignatureExpiringReportForm(forms.Form):
    """Форма для отчета по истекающим сертификатам"""
    days = forms.IntegerField(
        label='Период истечения (дней)',
        initial=40,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    active_only = forms.BooleanField(
        label='Только активные сертификаты',
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    department = forms.ModelChoiceField(
        queryset=Departments.objects.filter(is_active=True),
        label='Подразделение',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Все подразделения'
    )

