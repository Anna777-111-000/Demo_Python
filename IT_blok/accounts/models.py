from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class BusinessPermission(models.Model):
    """Бизнес-права (не стандартные Django permissions)"""
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    module = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Бизнес-право"
        verbose_name_plural = "Бизнес-права"


class Role(models.Model):
    """Роль сотрудника"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    is_super_role = models.BooleanField(default=False)
    permissions = models.ManyToManyField(BusinessPermission, blank=True)
    parent_role = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Родительская роль"
    )

    def __str__(self):
        return self.name

    def get_all_permissions(self):
        perms = set(self.permissions.all())
        if self.parent_role:
            perms.update(self.parent_role.get_all_permissions())
        return perms

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"


class CustomUser(AbstractUser):
    """Расширенная модель пользователя Django"""
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)


class EmployeeProfile(models.Model):
    DEPARTMENT_CHOICES = (
        ('it', '💻 IT-блок'),
        ('hr', '👥 HR'),
        ('finance', '💰 Финансы'),
        ('marketing', '📢 Маркетинг'),
        ('sales', '🤝 Продажи'),
        ('other', '📌 Другое'),
    )

    WORKER_TYPE_CHOICES = (
        ('developer', '👨‍💻 Разработчик'),
        ('admin', '🖥️ Админ'),
        ('devops', '⚙️ DevOps'),
        ('tester', '🧪 Тестировщик'),
        ('manager', '📋 Руководитель'),
        ('other', '📌 Другое'),
    )

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )

    full_name = models.CharField(max_length=200)
    tg_nick = models.CharField(max_length=100, blank=True, null=True)
    tg_chat_id = models.CharField(max_length=100, blank=True, null=True)
    corporate_email = models.EmailField(unique=True)
    personal_email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    worker_type = models.CharField(max_length=20, choices=WORKER_TYPE_CHOICES, default='other')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='other')
    position = models.CharField(max_length=200, blank=True)

    primary_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )

    extra_permissions = models.ManyToManyField(
        BusinessPermission,
        blank=True,
        related_name='users_with_extra'
    )

    restricted_permissions = models.ManyToManyField(
        BusinessPermission,
        blank=True,
        related_name='users_with_restriction'
    )

    is_active = models.BooleanField(default=True)
    hired_at = models.DateField(null=True, blank=True)
    fired_at = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    def get_effective_permissions(self):
        if self.primary_role and self.primary_role.is_super_role:
            return set(BusinessPermission.objects.all())

        base_perms = set()
        if self.primary_role:
            base_perms = self.primary_role.get_all_permissions()

        extra = set(self.extra_permissions.all())
        restricted = set(self.restricted_permissions.all())

        return (base_perms | extra) - restricted

    def has_permission(self, permission_codename):
        effective = self.get_effective_permissions()
        return any(p.codename == permission_codename for p in effective)

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"