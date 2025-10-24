# apps_testing/tests/forms.py
from django import forms

class TestAccessForm(forms.Form):
    password = forms.CharField(
        label="Пароль", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs): # Добавляем этот метод
        super().__init__(*args, **kwargs)
        for field_name in self.errors:
            if field_name in self.fields:
                widget = self.fields[field_name].widget
                current_class = widget.attrs.get('class', '')
                if 'is-invalid' not in current_class.split():
                    widget.attrs['class'] = f'{current_class} is-invalid'.strip()

class TestRegistrationForm(forms.Form):
    last_name = forms.CharField(
        label="Фамилия", 
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванов'
        })
    )
    first_name = forms.CharField(
        label="Имя", 
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иван'
        })
    )
    middle_name = forms.CharField(
        label="Отчество", 
        max_length=100, 

        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванович'
        })
    )

    def __init__(self, *args, **kwargs):
        """
        Переопределяем init для добавления класса is-invalid к полям с ошибками.
        Это лучший способ для интеграции с валидацией Bootstrap.
        """
        super().__init__(*args, **kwargs)
        for field in self.errors:
            attrs = self.fields[field].widget.attrs
            attrs['class'] = attrs.get('class', '') + ' is-invalid'