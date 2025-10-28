from django import forms

from .models import Employees, Posts


class HireNewEmployeeForm(forms.ModelForm):
    start_date = forms.DateField(label='Дата начала', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Employees
        fields = ['last_name', 'first_name', 'middle_name', 'birth_date', 'gender', 'phone', 'email']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
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
    target_post = forms.ModelChoiceField(queryset=Posts.objects.none(), label='Новая позиция')
    start_date = forms.DateField(label='Дата начала', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_post'].queryset = Posts.objects.filter(status=Posts.STATUS_VACANT, is_active=True)
        self.fields['target_post'].widget.attrs.update({'class': 'form-select'})


class EmployeesForm(forms.ModelForm):
    class Meta:
        model = Employees
        fields = ['last_name', 'first_name', 'middle_name', 'birth_date', 'gender', 'phone', 'email']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
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

