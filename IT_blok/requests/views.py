from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AdminRequestForm, DevelopmentRequestForm
from .models import RequestToAdmin
from .models import RequestComment
from accounts.models import EmployeeProfile
from django.contrib import messages


@login_required
def request_list(request):
    """Список запросов"""
    requests = RequestToAdmin.objects.all()

    # Фильтрация по статусу
    status = request.GET.get('status', '')
    if status:
        requests = requests.filter(status=status)

    # Для разных ролей разная видимость
    user = request.user
    try:
        profile = user.employee_profile
        # Если не админ и не директор - видит только свои запросы
        if not profile.has_permission('can_view_all_requests_short'):
            requests = requests.filter(created_by=user)
    except:
        requests = requests.filter(created_by=user)

    context = {
        'requests': requests,
        'title': 'Запросы админам',
        'status_filter': status,
    }
    return render(request, 'requests/list.html', context)


@login_required
def request_create(request):
    """Создание нового запроса"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')

        request_obj = RequestToAdmin.objects.create(
            title=title,
            description=description,
            created_by=request.user
        )

        messages.success(request, f'Запрос #{request_obj.id} создан')
        return redirect('requests:detail', pk=request_obj.id)

    return render(request, 'requests/create.html', {'title': 'Новый запрос'})


@login_required
def request_detail(request, pk):
    """Детальная страница запроса"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    # Проверка прав на просмотр
    user = request.user
    can_view = False

    try:
        profile = user.employee_profile
        if (profile.has_permission('can_view_all_requests_detail') or
                profile.has_permission('can_view_department_requests') or
                request_obj.created_by == user or
                request_obj.assigned_to == user):
            can_view = True
    except:
        if request_obj.created_by == user:
            can_view = True

    if not can_view:
        messages.error(request, 'У вас нет прав для просмотра этого запроса')
        return redirect('requests:list')

    context = {
        'request': request_obj,
        'title': f'Запрос #{request_obj.id}'
    }
    return render(request, 'requests/detail.html', context)


@login_required
def request_take(request, pk):
    """Взять запрос в работу"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    if request_obj.status != 'new':
        messages.error(request, 'Запрос уже взят в работу')
        return redirect('requests:detail', pk=pk)

    request_obj.status = 'in_progress'
    request_obj.assigned_to = request.user
    request_obj.taken_at = timezone.now()
    request_obj.save()

    messages.success(request, f'Запрос #{request_obj.id} взят в работу')
    return redirect('requests:detail', pk=pk)


@login_required
def request_close(request, pk):
    """Закрыть запрос"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    if request_obj.status != 'in_progress':
        messages.error(request, 'Закрыть можно только запрос в работе')
        return redirect('requests:detail', pk=pk)

    request_obj.status = 'done'
    request_obj.closed_at = timezone.now()
    request_obj.save()

    messages.success(request, f'Запрос #{request_obj.id} закрыт')
    return redirect('requests:detail', pk=pk)


@login_required
def request_reject(request, pk):
    """Отклонить запрос"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        request_obj.status = 'rejected'
        request_obj.rejection_reason = reason
        request_obj.closed_at = timezone.now()
        request_obj.save()

        messages.success(request, f'Запрос #{request_obj.id} отклонён')
        return redirect('requests:detail', pk=pk)

    return render(request, 'requests/reject.html', {'request': request_obj})


@login_required
def request_comment(request, pk):
    """Добавить комментарий"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            RequestComment.objects.create(
                request=request_obj,
                author=request.user,
                text=text
            )
            messages.success(request, 'Комментарий добавлен')

    return redirect('requests:detail', pk=pk)


@csrf_exempt
@require_http_methods(["POST"])
def hr_webhook(request):
    """API для HR (автоматическое создание запроса)"""
    try:
        data = json.loads(request.body)

        # Ищем или создаём пользователя
        email = data.get('email')
        # ... логика создания пользователя

        # Создаём автоматический запрос
        request_obj = RequestToAdmin.objects.create(
            title=f"Выдача доступов: {data.get('full_name')}",
            description=f"Автоматический запрос от HR. Выдать доступы новому сотруднику.",
            created_by=request.user,  # нужно получить системного пользователя
            is_auto=True,
            hr_data=data
        )

        return JsonResponse({'status': 'ok', 'request_id': request_obj.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)


@login_required
def request_assign(request, pk):
    """Назначить запрос другому админу"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    if request.method == 'POST':
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                assigned_to = User.objects.get(id=assigned_to_id)
                request_obj.assigned_to = assigned_to
                request_obj.save()
                messages.success(request, f'Запрос #{request_obj.id} назначен на {assigned_to.username}')
            except User.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
        return redirect('requests:detail', pk=pk)

    # GET запрос - показываем форму выбора
    from accounts.models import EmployeeProfile
    admins = EmployeeProfile.objects.filter(primary_role__codename='it_admin').select_related('user')

    context = {
        'request': request_obj,
        'admins': admins,
        'title': f'Назначение запроса #{request_obj.id}'
    }
    return render(request, 'requests/assign.html', context)


@login_required
def request_comment(request, pk):
    """Добавить комментарий к запросу"""
    request_obj = get_object_or_404(RequestToAdmin, id=pk)

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            RequestComment.objects.create(
                request=request_obj,
                author=request.user,
                text=text
            )
            messages.success(request, 'Комментарий добавлен')

    return redirect('requests:detail', pk=pk)


@csrf_exempt
@require_http_methods(["POST"])
def hr_webhook(request):
    """API для HR (автоматическое создание запроса)"""
    try:
        data = json.loads(request.body)

        # TODO: создать или найти пользователя
        # user = User.objects.get_or_create...

        # Создаём автоматический запрос
        request_obj = RequestToAdmin.objects.create(
            title=f"Выдача доступов: {data.get('full_name', 'Новый сотрудник')}",
            description=f"Автоматический запрос от HR. Выдать доступы новому сотруднику.\n\nДанные: {data}",
            created_by=request.user,
            is_auto=True,
            hr_data=data
        )

        return JsonResponse({'status': 'ok', 'request_id': request_obj.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)


@login_required
def create_for_admin(request):
    if request.method == 'POST':
        form = AdminRequestForm(request.POST)
        if form.is_valid():
            # Временно без сохранения в БД
            messages.success(request, 'Запрос отправлен администраторам')
            return redirect('dashboard')
    else:
        form = AdminRequestForm()

    return render(request, 'requests/guest_form.html', {
        'form': form,
        'title': 'Запрос админам',
        'icon': 'fa-headset'
    })


@login_required
def create_for_development(request):
    if request.method == 'POST':
        form = DevelopmentRequestForm(request.POST)
        if form.is_valid():
            RequestToAdmin.objects.create(
                request_type='development',
                title=f"[Разработка] {form.cleaned_data['request_type']}",
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                created_by=request.user,
            )
            messages.success(request, 'Запрос отправлен в разработку')
            return redirect('dashboard')
    else:
        form = DevelopmentRequestForm()

    return render(request, 'requests/guest_form.html', {
        'form': form,
        'title': 'Запрос в разработку',
        'icon': 'fa-code'
    })


@login_required
def all_requests(request):
    """Список всех запросов для руководства"""
    if not request.user.employee_profile.has_permission('can_view_all_requests'):
        messages.error(request, 'У вас нет прав')
        return redirect('dashboard')

    requests_list = RequestToAdmin.objects.all().order_by('-created_at')
    return render(request, 'requests/all_list.html', {'requests': requests_list})


@login_required
def create_for_admin(request):
    if request.method == 'POST':
        form = AdminRequestForm(request.POST)
        if form.is_valid():
            RequestToAdmin.objects.create(
                request_type='admin',
                title=f"[Админам] {form.cleaned_data['request_type']}",
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                created_by=request.user,
            )
            messages.success(request, 'Запрос отправлен администраторам')
            return redirect('dashboard')
    else:
        form = AdminRequestForm()

    return render(request, 'requests/guest_form.html', {
        'form': form,
        'title': 'Запрос админам',
        'icon': 'fa-headset'
    })


@login_required
def all_requests(request):
    """Страница всех заявок (только для руководства)"""
    profile = request.user.employee_profile

    # Проверка прав
    if not (profile.department == 'it' or
            profile.primary_role and profile.primary_role.codename in ['it_admin', 'it_director', 'department_head',
                                                                       'ceo']):
        messages.error(request, 'У вас нет прав для просмотра заявок')
        return redirect('dashboard')

    requests_list = RequestToAdmin.objects.all().order_by('-created_at')

    return render(request, 'requests/all_requests.html', {
        'requests': requests_list,
    })


@login_required
def create_for_admin(request):
    if request.method == 'POST':
        form = AdminRequestForm(request.POST)
        if form.is_valid():
            RequestToAdmin.objects.create(
                request_type='admin',
                title=f"[Админам] {form.cleaned_data['request_type']}",
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                created_by=request.user,
            )
            messages.success(request, 'Запрос отправлен администраторам')
            return redirect('dashboard')
    else:
        form = AdminRequestForm()

    return render(request, 'requests/guest_form.html', {
        'form': form,
        'title': 'Запрос админам',
        'icon': 'fa-headset'
    })


@login_required
def all_tickets(request):
    """Страница заявок (запросы в разработку + предложения) — только для руководства"""
    profile = request.user.employee_profile

    # Проверка прав
    if not (profile.department == 'it' or
            profile.primary_role and profile.primary_role.codename in ['it_admin', 'it_director', 'department_head',
                                                                       'ceo']):
        messages.error(request, 'У вас нет прав для просмотра заявок')
        return redirect('dashboard')

    tickets = RequestToAdmin.objects.filter(
        request_type__in=['development', 'suggestion']
    ).order_by('-created_at')

    return render(request, 'requests/all_tickets.html', {
        'tickets': tickets,
    })