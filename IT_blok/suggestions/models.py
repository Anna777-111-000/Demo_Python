from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Suggestion(models.Model):
    """Временная модель предложения"""
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Предложение'
        verbose_name_plural = 'Предложения'

    def __str__(self):
        return self.title