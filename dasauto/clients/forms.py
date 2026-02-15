from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'client_type', 'first_name', 'last_name', 'patronymic',
            'phone', 'email', 'additional_phone', 'company_name',
            'inn', 'kpp', 'address', 'discount', 'source', 'tags', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите фамилию'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите отчество'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'additional_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название компании'}),
            'inn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ИНН'}),
            'kpp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'КПП'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Адрес'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.1}),
            'source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Откуда узнал о нас'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Теги через запятую'}),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Дополнительные заметки'}),
            'client_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            raise forms.ValidationError('Телефон обязателен для заполнения')
        return phone

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError('Имя обязательно для заполнения')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError('Фамилия обязательна для заполнения')
        return last_name

    def clean_inn(self):
        inn = self.cleaned_data.get('inn')
        client_type = self.cleaned_data.get('client_type')

        if client_type == 'legal' and not inn:
            raise forms.ValidationError('Для юридического лица ИНН обязателен')

        if inn and len(inn) not in [10, 12]:
            raise forms.ValidationError('ИНН должен содержать 10 или 12 цифр')

        return inn