from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class RequestToAdmin(models.Model):
    # Определяем выборы ПЕРЕД использованием
    REQUEST_TYPE_CHOICES = (
        ('admin', 'Запрос админам'),
        ('development', 'Запрос в разработку'),
        ('suggestion', 'Предложение'),
    )

    STATUS_CHOICES = (
        ('new', '🆕 Новый'),
        ('in_progress', '⚙️ В работе'),
        ('done', '✅ Выполнен'),
        ('rejected', '❌ Отклонён'),
    )

    PRIORITY_CHOICES = (
        ('low', '🟢 Низкая'),
        ('medium', '🟡 Средняя'),
        ('high', '🔴 Высокая'),
        ('urgent', '⚠️ Срочная'),
    )

    # Поля модели
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES, default='admin')
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    taken_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    hr_data = models.JSONField(null=True, blank=True)
    is_auto = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_request_type_display()} - {self.created_by}"

    # Основная информация
    title = models.CharField(max_length=200, verbose_name='Тема запроса')
    description = models.TextField(verbose_name='Описание')

    # Кто и кому
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_requests',
        verbose_name='Автор'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        verbose_name='Исполнитель'
    )

    # Статусы
    status = models.CharField(
        max_length=20,
        default='new',
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    rejection_reason = models.TextField(blank=True, verbose_name='Причина отклонения')

    # Даты
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    taken_at = models.DateTimeField(null=True, blank=True, verbose_name='Взят в работу')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Закрыт')

    # Автоматические запросы от HR
    is_auto = models.BooleanField(default=False, verbose_name='Автоматический запрос')
    hr_data = models.JSONField(null=True, blank=True, verbose_name='Данные из HR')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запрос админам'
        verbose_name_plural = 'Запросы админам'
        permissions = [
            ('can_take_request', 'Может взять запрос в работу'),
            ('can_assign_request', 'Может назначить запрос другому'),
            ('can_close_request', 'Может закрыть запрос'),
            ('can_reject_request', 'Может отклонить запрос'),
        ]

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def save(self, *args, **kwargs):
        # Если статус меняется на "в работе" - записываем дату
        if self.status == 'in_progress' and not self.taken_at:
            self.taken_at = timezone.now()
        # Если статус меняется на "выполнен" или "отклонён" - записываем дату
        if self.status in ['done', 'rejected'] and not self.closed_at:
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)


class RequestComment(models.Model):
    """Комментарии к запросу"""

    request = models.ForeignKey(
        RequestToAdmin,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запрос'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='request_comments',
        verbose_name='Автор'
    )
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f"Комментарий к #{self.request.id} от {self.author.username}"