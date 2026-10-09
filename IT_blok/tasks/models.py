from django.db import models
from django.conf import settings
from django.utils import timezone


class Task(models.Model):
    # Статусы
    STATUS_CHOICES = (
        ('new', '🆕 Новая'),
        ('in_progress', '⚙️ В работе'),
        ('done', '✅ Выполнена'),
        ('deferred', '⏸️ Отложена'),
    )

    # Приоритеты
    PRIORITY_CHOICES = (
        ('low', '🟢 Низкий'),
        ('medium', '🟡 Средний'),
        ('high', '🔴 Высокий'),
        ('urgent', '⚠️ Срочный'),
    )

    # Типы видимости
    PRIVACY_CHOICES = (
        ('public', '👥 Публичная (все видят)'),
        ('private_self', '🔒 Только я'),
        ('private_management', '👁️ Я и руководство'),
    )
    CATEGORY_CHOICES = (
        ('management', '🎯 Руководство'),
        ('development', '🛠️ Разработка'),
        ('infrastructure', '⚙️ Инфраструктура'),
        ('knowledge', '📚 Знания'),
        ('other', '💬 Прочее'),
    )

    WORKER_TYPE_CHOICES = (
        ('admin', '🖥️ Админы'),
        ('developer', '👨‍💻 Программисты'),
        ('devops', '⚙️ DevOps'),
        ('tester', '🧪 Тестировщики'),
        ('manager', '📋 Руководитель'),
    )


    # Основные поля
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    worker_type = models.CharField(max_length=20, choices=WORKER_TYPE_CHOICES, blank=True)
    created_from = models.CharField(max_length=20, default='manual')  # manual, request, call
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    status = models.CharField(max_length=20, default='new', choices=STATUS_CHOICES)
    priority = models.CharField(max_length=10, default='medium', choices=PRIORITY_CHOICES)
    privacy = models.CharField(max_length=20, default='public', choices=PRIVACY_CHOICES)

    # Даты
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Кто создал
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    created_by_system = models.BooleanField(default=False)

    # Кто взял в работу
    taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taken_tasks'
    )
    taken_at = models.DateTimeField(null=True, blank=True)

    # Исполнители
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
        null=True,
        blank=True
    )
    assigned_to_multiple = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='assigned_tasks_multiple'
    )

    def __str__(self):
        return self.title

    def take_in_progress(self):
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()

    def complete(self):
        self.status = 'done'
        self.completed_at = timezone.now()
        self.save()

    def defer(self):
        self.status = 'deferred'
        self.save()

    class Meta:
        ordering = ['-created_at']


class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.title} - {self.field_name} by {self.user}"