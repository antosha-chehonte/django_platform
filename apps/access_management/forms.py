from django import forms
from .models import CertificateType, SystemAccess, DigitalSignature


class CertificateTypeForm(forms.ModelForm):
    class Meta:
        model = CertificateType
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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

