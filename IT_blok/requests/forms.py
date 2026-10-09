from django import forms


class AdminRequestForm(forms.Form):
    REQUEST_TYPE_CHOICES = (
        ('access_self', 'Запросить доступ (мне)'),
        ('access_other', 'Выдать доступ (другому сотруднику)'),
        ('password_change', 'Смена пароля'),
        ('data_change', 'Смена личных данных'),
        ('login_problem', 'Проблема с входом'),
        ('create_account', 'Создать аккаунт на платформе'),
        ('new_employee', 'Новый сотрудник (создать всё)'),
        ('fire_employee', 'Увольнение / снятие доступа'),
        ('tech_issue', 'Техническая проблема'),
        ('other', 'Другое'),
    )

    PRIORITY_CHOICES = (
        ('low', '🟢 Низкая'),
        ('medium', '🟡 Средняя'),
        ('high', '🔴 Высокая'),
        ('urgent', '⚠️ Срочная'),
    )

    request_type = forms.ChoiceField(choices=REQUEST_TYPE_CHOICES, label="Тип запроса")
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опишите подробно ваш запрос...'}), label="Описание")
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, label="Срочность", initial='medium')


class DevelopmentRequestForm(forms.Form):
    REQUEST_TYPE_CHOICES = (
        ('site', 'Разработка сайта'),
        ('app', 'Разработка приложения'),
        ('feature', 'Доработка функционала'),
        ('bug', 'Исправление ошибки / бага'),
        ('software_issue', 'Проблема с существующим ПО'),
        ('integration', 'Интеграция с внешним сервисом / API'),
        ('optimization', 'Оптимизация / ускорение работы'),
        ('other', 'Другое'),
    )

    request_type = forms.ChoiceField(choices=REQUEST_TYPE_CHOICES, label="Тип запроса")
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Опишите подробно ваш запрос...'}), label="Описание")
    priority = forms.ChoiceField(choices=AdminRequestForm.PRIORITY_CHOICES, label="Срочность", initial='medium')