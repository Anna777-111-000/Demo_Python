from django.db import models
from django.conf import settings


class AccessGrant(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='access_grants')
    service_name = models.CharField(max_length=100, verbose_name="Название сервиса")
    service_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Ссылка на сервис")
    service_login = models.CharField(max_length=200, blank=True, verbose_name="Логин")
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='granted_access')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField(null=True, blank=True, verbose_name="Срок действия")
    comment = models.TextField(blank=True, verbose_name="Комментарий")

    def __str__(self):
        return f"{self.employee} → {self.service_name}"

    def get_service_logo(self):
        """Получить URL логотипа сервиса (через Google Favicon)"""
        if not self.service_url:
            return None
        from urllib.parse import urlparse
        try:
            parsed = urlparse(self.service_url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            return f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
        except:
            return None