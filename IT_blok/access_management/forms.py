from django import forms
from django.contrib.auth import get_user_model
from .models import AccessGrant

User = get_user_model()


class AccessGrantForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Сотрудник"
    )

    class Meta:
        model = AccessGrant
        fields = ['employee', 'service_name', 'service_url', 'service_login', 'expires_at', 'comment']
        widgets = {
            'service_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Например: GitLab, Jira, VPN'}),
            'service_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://gitlab.company.com'}),
            'service_login': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Логин сотрудника в сервисе'}),
            'expires_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comment': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Дополнительная информация...'}),
        }