from django.db import models
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field  # добавьте импорт


class Article(models.Model):
    CATEGORY_CHOICES = (
        ('guide', '📘 Руководство'),
        ('faq', '❓ Частые вопросы'),
        ('troubleshooting', '🔧 Решение проблем'),
        ('policy', '📋 Политики и правила'),
        ('other', '📄 Другое'),
    )

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Категория")
    tags = models.CharField(max_length=200, blank=True, verbose_name="Теги",
                            help_text="Через запятую, например: python, django, настройка")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='articles',
                                   verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано",
                                       help_text="Снимите галочку, чтобы сохранить как черновик")

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-created_at']