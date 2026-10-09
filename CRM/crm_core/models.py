from django.db import models
from django.conf import settings


class Company(models.Model):
    """Клиент-компания"""
    name = models.CharField(max_length=255, verbose_name="Название")
    inn = models.CharField(max_length=20, blank=True, verbose_name="ИНН")
    website = models.URLField(blank=True, verbose_name="Сайт")
    industry = models.CharField(max_length=100, blank=True, verbose_name="Отрасль")
    address = models.TextField(blank=True, verbose_name="Адрес")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='crm_companies', verbose_name="Ответственный"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        ordering = ['name']

    def __str__(self):
        return self.name


class Contact(models.Model):
    """Контактное лицо клиента"""
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='contacts', verbose_name="Компания"
    )
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    position = models.CharField(max_length=150, blank=True, verbose_name="Должность")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    tg_nick = models.CharField(max_length=100, blank=True, verbose_name="Telegram")
    is_primary = models.BooleanField(default=False, verbose_name="Основной контакт")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"
        ordering = ['-is_primary', 'full_name']

    def __str__(self):
        return f"{self.full_name} ({self.company.name})"


class Deal(models.Model):
    """Сделка"""
    STAGES = (
        ('new', '🆕 Новый лид'),
        ('qualified', '✅ Квалифицирован'),
        ('proposal', '📄 Предложение'),
        ('negotiation', '🤝 Переговоры'),
        ('won', '🏆 Успешно'),
        ('lost', '❌ Провал'),
    )

    title = models.CharField(max_length=255, verbose_name="Название")
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE,
        related_name='deals', verbose_name="Компания"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='deals', verbose_name="Контакт"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name="Сумма")
    currency = models.CharField(max_length=3, default='RUB', verbose_name="Валюта")
    stage = models.CharField(max_length=20, choices=STAGES, default='new', verbose_name="Стадия")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='crm_deals', verbose_name="Ответственный"
    )
    source = models.CharField(max_length=100, blank=True, verbose_name="Источник")
    expected_close = models.DateField(null=True, blank=True, verbose_name="Ожидаемое закрытие")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="Закрыто")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Сделка"
        verbose_name_plural = "Сделки"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.company.name}"


class Activity(models.Model):
    """Взаимодействие с клиентом"""
    TYPES = (
        ('call', '📞 Звонок'),
        ('email', '✉️ Письмо'),
        ('meeting', '📅 Встреча'),
        ('note', '📝 Заметка'),
    )

    deal = models.ForeignKey(
        Deal, on_delete=models.CASCADE, null=True, blank=True,
        related_name='activities', verbose_name="Сделка"
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, null=True, blank=True,
        related_name='activities', verbose_name="Компания"
    )
    contact = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='activities', verbose_name="Контакт"
    )
    kind = models.CharField(max_length=20, choices=TYPES, verbose_name="Тип")
    subject = models.CharField(max_length=255, blank=True, verbose_name="Тема")
    body = models.TextField(blank=True, verbose_name="Содержание")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='crm_activities', verbose_name="Автор"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Активность"
        verbose_name_plural = "Активности"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_kind_display()} — {self.subject or self.deal or self.company}"



class CrmTask(models.Model):
    """Задача внутри CRM (для менеджеров)"""

    STATUS_CHOICES = (
        ('todo', '📋 К выполнению'),
        ('in_progress', '⚙️ В работе'),
        ('review', '🔍 На проверке'),
        ('done', '✅ Готово'),
    )

    PRIORITY_CHOICES = (
        ('low', '🟢 Низкий'),
        ('medium', '🟡 Средний'),
        ('high', '🔴 Высокий'),
    )

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    deal = models.ForeignKey(
        Deal, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='crm_tasks', verbose_name="Сделка"
    )
    company = models.ForeignKey(
        Company, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='crm_tasks', verbose_name="Компания"
    )

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='crm_tasks_assigned', verbose_name="Исполнитель"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='crm_tasks_author', verbose_name="Автор"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo', verbose_name="Статус")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="Приоритет")
    due_date = models.DateField(null=True, blank=True, verbose_name="Срок")
    order = models.IntegerField(default=0, verbose_name="Порядок в колонке")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершено")

    class Meta:
        verbose_name = "CRM-задача"
        verbose_name_plural = "CRM-задачи"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.status == 'done' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'done':
            self.completed_at = None
        super().save(*args, **kwargs)