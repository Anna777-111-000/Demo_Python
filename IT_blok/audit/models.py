from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class AuditLog(models.Model):
    ACTION_TYPES = (
        ('create', 'Создание'),
        ('update', 'Изменение'),
        ('delete', 'Удаление'),
        ('view', 'Просмотр'),
        ('login', 'Вход'),
        ('logout', 'Выход'),
        ('assign', 'Назначение'),
        ('status_change', 'Смена статуса'),
        ('permission_change', 'Изменение прав'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
        verbose_name = "Лог аудита"
        verbose_name_plural = "Логи аудита"

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"