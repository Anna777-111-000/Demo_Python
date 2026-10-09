from django import template

register = template.Library()

@register.filter
def has_permission(user, perm_codename):
    """Проверяет наличие права у пользователя"""
    if not user.is_authenticated:
        return False
    try:
        profile = user.employee_profile
        return profile.has_permission(perm_codename)
    except:
        return False

@register.filter
def is_super_role(user):
    """Проверяет, является ли роль супер-ролью (директор)"""
    if not user.is_authenticated:
        return False
    try:
        profile = user.employee_profile
        return profile.primary_role and profile.primary_role.is_super_role
    except:
        return False