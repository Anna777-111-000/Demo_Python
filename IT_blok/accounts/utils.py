from .models import EmployeeProfile, BusinessPermission


def get_user_effective_permissions(user):
    """Получить все эффективные права пользователя"""
    try:
        profile = user.employee_profile
        return profile.get_effective_permissions()
    except EmployeeProfile.DoesNotExist:
        return set()


def user_has_permission(user, permission_codename):
    """Проверить наличие права у пользователя"""
    try:
        profile = user.employee_profile
        return profile.has_permission(permission_codename)
    except EmployeeProfile.DoesNotExist:
        return False


def get_role_permissions(role):
    """Получить все права роли (с учётом наследования)"""
    if not role:
        return set()
    return role.get_all_permissions()