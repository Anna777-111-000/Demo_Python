from django import forms
from .models import EmployeeProfile, Role, BusinessPermission


class EmployeePermissionsForm(forms.ModelForm):
    """Форма для управления правами сотрудника"""

    class Meta:
        model = EmployeeProfile
        fields = ['primary_role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Группируем права по модулям
        permissions = BusinessPermission.objects.all().order_by('module', 'name')

        self.modules = {}
        for perm in permissions:
            if perm.module not in self.modules:
                self.modules[perm.module] = []
            self.modules[perm.module].append(perm)

        # Добавляем поля для каждого права (галочки)
        for perm in permissions:
            field_name = f"perm_{perm.codename}"
            initial = perm in self.instance.get_effective_permissions() if self.instance else False
            self.fields[field_name] = forms.BooleanField(
                required=False,
                initial=initial,
                label=perm.name
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)

        # Собираем выбранные права
        extra_perms = []
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('perm_') and value:
                codename = field_name.replace('perm_', '')
                try:
                    perm = BusinessPermission.objects.get(codename=codename)
                    extra_perms.append(perm)
                except BusinessPermission.DoesNotExist:
                    pass

        # Обновляем дополнительные права
        instance.extra_permissions.set(extra_perms)

        # Получаем права роли
        role_perms = instance.primary_role.get_all_permissions() if instance.primary_role else set()

        # Вычисляем какие права нужно запретить (которые есть в роли, но не выбраны)
        # или оставить как есть - логика на ваше усмотрение

        return instance


class EmployeePermissionsForm(forms.ModelForm):
    """Форма для управления правами сотрудника"""

    class Meta:
        model = EmployeeProfile
        fields = ['primary_role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Группируем права по модулям
        permissions = BusinessPermission.objects.all().order_by('module', 'name')

        self.modules = {}
        for perm in permissions:
            if perm.module not in self.modules:
                self.modules[perm.module] = []
            self.modules[perm.module].append(perm)

        # Добавляем поля для каждого права (галочки)
        for perm in permissions:
            field_name = f"perm_{perm.codename}"
            initial = perm in self.instance.get_effective_permissions() if self.instance else False
            self.fields[field_name] = forms.BooleanField(
                required=False,
                initial=initial,
                label=perm.name
            )

    def save(self, commit=True):
        instance = super().save(commit=commit)

        # Собираем выбранные права
        extra_perms = []
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('perm_') and value:
                codename = field_name.replace('perm_', '')
                try:
                    perm = BusinessPermission.objects.get(codename=codename)
                    extra_perms.append(perm)
                except BusinessPermission.DoesNotExist:
                    pass

        # Обновляем дополнительные права
        instance.extra_permissions.set(extra_perms)

        return instance


class EmployeeCreateForm(forms.Form):
    """Форма для создания нового сотрудника"""
    full_name = forms.CharField(max_length=200, label='ФИО', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    tg_nick = forms.CharField(max_length=100, required=True, label='Telegram (ник)',
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(max_length=200, required=False, label='Должность',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    primary_role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        label='Основная роль',
        widget=forms.Select(attrs={'class': 'form-select'})
    )