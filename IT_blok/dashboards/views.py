from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tasks.models import Task
from requests.models import RequestToAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def dashboard(request):
    """Главная страница в зависимости от роли пользователя"""
    profile = request.user.employee_profile

    # Проверка: сотрудник IT-блока или руководство
    if profile.department == 'it' or profile.primary_role and profile.primary_role.codename in ['it_admin',
                                                                                                'it_director',
                                                                                                'department_head',
                                                                                                'ceo']:
        context = {
            'tasks_count': Task.objects.filter(status__in=['new', 'in_progress']).count(),
            'requests_count': RequestToAdmin.objects.filter(status__in=['new', 'in_progress']).count(),
            'users_count': User.objects.filter(is_active=True).count(),
            'completed_count': Task.objects.filter(status='done').count(),
        }
        return render(request, 'dashboard.html', context)

    # Не-IT сотрудники (гости компании)
    return render(request, 'dashboard_guest.html')


def test_template(request):
    return render(request, 'test.html')