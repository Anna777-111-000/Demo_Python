from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json
from .models import Task
from accounts.models import CustomUser
from django.utils import timezone

@login_required
def task_list(request):
    """Канбан-доска задач"""
    return render(request, 'tasks/list.html')


@login_required
def task_list_api(request):
    """API для получения задач (JSON) с учётом прав"""
    profile = getattr(request.user, 'employee_profile', None)

    # Хелпер проверки прав
    def has_perm(code):
        try:
            return profile.has_permission(code) if profile else False
        except Exception:
            return False

    # Определяем базовый queryset по правам
    if has_perm('can_view_all_tasks_brief') or has_perm('can_view_all_logs'):
        qs = Task.objects.all()
        access_level = 'all'
    elif has_perm('can_view_department_tasks'):
        dept = profile.department if profile else ''
        qs = Task.objects.filter(
            Q(assigned_to__employee_profile__department=dept) |
            Q(created_by__employee_profile__department=dept) |
            Q(assigned_to_multiple__employee_profile__department=dept)
        ).distinct()
        access_level = 'department'
    elif has_perm('can_view_own_tasks'):
        qs = Task.objects.filter(
            Q(assigned_to=request.user) |
            Q(created_by=request.user) |
            Q(assigned_to_multiple=request.user)
        ).distinct()
        access_level = 'own'
    else:
        qs = Task.objects.none()
        access_level = 'none'

    # Дополнительный фильтр из GET-параметра
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'my':
        qs = qs.filter(
            Q(assigned_to=request.user) |
            Q(created_by=request.user) |
            Q(assigned_to_multiple=request.user)
        ).distinct()
    elif filter_type == 'department' and profile and profile.department:
        dept = profile.department
        qs = qs.filter(
            Q(assigned_to__employee_profile__department=dept) |
            Q(created_by__employee_profile__department=dept)
        ).distinct()

    # Приватные задачи: private_self видит только автор
    # (или супер-роль, которая видит всё)
    if not has_perm('can_view_all_tasks_brief'):
        qs = qs.exclude(
            Q(privacy='private_self') & ~Q(created_by=request.user) & ~Q(assigned_to=request.user)
        )

    data = {
        'tasks': [
            {
                'id': t.id,
                'title': t.title,
                'status': t.status,
                'category': t.category,
                'worker_type': t.worker_type,
                'assigned_to_name': (
                    t.assigned_to.employee_profile.full_name
                    if t.assigned_to and hasattr(t.assigned_to, 'employee_profile')
                    else (t.assigned_to.username if t.assigned_to else '—')
                ),
                'deadline': t.deadline.strftime('%d.%m.%Y') if t.deadline else None,
                'priority': t.priority,
                'privacy': t.privacy,
            }
            for t in qs
        ],
        'access_level': access_level,
    }
    return JsonResponse(data)

@login_required
def task_detail_api(request, task_id):
    """API для получения данных одной задачи"""
    task = get_object_or_404(Task, id=task_id)
    users = CustomUser.objects.all()


    data = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'assigned_to_id': task.assigned_to_id,
        'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else '',
        'is_private': task.is_private if hasattr(task, 'is_private') else False,
        'users': [{'id': u.id, 'name': u.employee_profile.full_name if hasattr(u, 'employee_profile') else u.username}
                  for u in users],
        'created_by_name': task.created_by.employee_profile.full_name if hasattr(task.created_by,
                                                                                 'employee_profile') else task.created_by.username,
        'created_at': task.created_at.isoformat(),
        'taken_by_name': task.taken_by.employee_profile.full_name if task.taken_by and hasattr(task.taken_by,
                                                                                               'employee_profile') else (
            task.taken_by.username if task.taken_by else None),
        'taken_at': task.taken_at.isoformat() if task.taken_at else None,
        'privacy': task.privacy,
        'priority': task.priority,
    }
    return JsonResponse(data)


@login_required
def users_api(request):
    """API для получения списка пользователей"""
    users = CustomUser.objects.all()
    data = [{'id': u.id, 'name': u.employee_profile.full_name if hasattr(u, 'employee_profile') else u.username} for u
            in users]
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def task_update_status_api(request, task_id):
    """API для обновления статуса задачи (drag-and-drop)"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@login_required
def task_update_api(request, task_id):
    """API для обновления задачи (из модального окна)"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        data = json.loads(request.body)

        task.description = data.get('description', '')
        task.assigned_to_id = data.get('assigned_to')
        task.deadline = data.get('deadline') or None
        if hasattr(task, 'is_private'):
            task.is_private = data.get('is_private', False)
        task.save()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
def task_detail(request, task_id):
    """Детальный просмотр задачи (если нужно)"""
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'tasks/detail.html', {'task': task})


@login_required
def task_update_status(request, task_id):
    """Изменение статуса задачи (POST)"""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        status = request.POST.get('status')
        if status in dict(Task.STATUS_CHOICES):
            task.status = status
            task.save()
            messages.success(request, f'Статус задачи "{task.title}" изменён')
    return redirect('tasks:list')


@login_required
def task_create(request):
    """Создание задачи (старая форма)"""
    if request.method == 'POST':
        task = Task.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            assigned_to_id=request.POST.get('assigned_to'),
            created_by=request.user,
            deadline=request.POST.get('deadline') or None,
        )
        messages.success(request, f'Задача "{task.title}" создана')
        return redirect('tasks:list')

    users = CustomUser.objects.all()
    return render(request, 'tasks/form.html', {'users': users})


@csrf_exempt
@login_required
def task_create_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        task = Task.objects.create(
            title=data.get('title'),
            description=data.get('description', ''),
            start_date=data.get('start_date') or None,
            deadline=data.get('deadline') or None,
            priority=data.get('priority', 'medium'),
            privacy=data.get('privacy', 'public'),
            category=data.get('category', 'other'),
            worker_type=data.get('worker_type', ''),
            created_by=request.user,
            created_from=data.get('created_from', 'manual'),
        )

        # Исполнители
        assigned_users = data.get('assigned_users', [])
        if assigned_users:
            from accounts.models import CustomUser
            task.assigned_to_multiple.set(CustomUser.objects.filter(id__in=assigned_users))
            task.assigned_to_id = assigned_users[0]
            task.save()

        return JsonResponse({'success': True, 'id': task.id})

    return JsonResponse({'success': False}, status=400)


@csrf_exempt
@login_required
def task_take_api(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.taken_by = request.user
    task.taken_at = timezone.now()
    task.status = 'in_progress'
    task.save()
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def task_complete_api(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.status = 'done'
    task.completed_at = timezone.now()
    task.save()
    return JsonResponse({'success': True})

@csrf_exempt
@login_required
def task_defer_api(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.status = 'deferred'
    task.save()
    return JsonResponse({'success': True})