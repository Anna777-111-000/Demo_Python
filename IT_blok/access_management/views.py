from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import AccessGrant
from .forms import AccessGrantForm


@login_required
def access_list(request):
    """Список всех доступов (только для админов)"""
    accesses = AccessGrant.objects.select_related('employee', 'granted_by').all()

    # Фильтрация
    service_filter = request.GET.get('service', '')
    if service_filter:
        accesses = accesses.filter(service_name__icontains=service_filter)

    employee_filter = request.GET.get('employee', '')
    if employee_filter:
        accesses = accesses.filter(employee__employee_profile__full_name__icontains=employee_filter)

    # Сортировка
    sort = request.GET.get('sort', 'newest')
    if sort == 'newest':
        accesses = accesses.order_by('-granted_at')
    elif sort == 'oldest':
        accesses = accesses.order_by('granted_at')

    return render(request, 'access/list.html', {
        'accesses': accesses,
        'service_filter': service_filter,
        'employee_filter': employee_filter,
        'sort': sort,
        'now': timezone.now().date()
    })


@login_required
def my_access(request):
    """Мои доступы с фильтрацией и сортировкой"""
    accesses = AccessGrant.objects.filter(employee=request.user)

    # Фильтрация
    service_filter = request.GET.get('service', '')
    if service_filter:
        accesses = accesses.filter(service_name__icontains=service_filter)

    # Сортировка
    sort = request.GET.get('sort', 'newest')
    if sort == 'newest':
        accesses = accesses.order_by('-granted_at')
    elif sort == 'oldest':
        accesses = accesses.order_by('granted_at')

    return render(request, 'access/my_access.html', {
        'accesses': accesses,
        'service_filter': service_filter,
        'sort': sort,
        'now': timezone.now().date()
    })


@login_required
def access_create(request):
    """Выдать доступ (только для админов)"""
    if not request.user.employee_profile.has_permission('can_grant_access'):
        messages.error(request, 'У вас нет прав на выдачу доступов')
        return redirect('access:my_access')

    if request.method == 'POST':
        form = AccessGrantForm(request.POST)
        if form.is_valid():
            access = form.save(commit=False)
            access.granted_by = request.user
            access.save()
            messages.success(request,
                             f'Доступ к "{access.service_name}" выдан сотруднику {access.employee.employee_profile.full_name}')
            return redirect('access:list')
    else:
        form = AccessGrantForm()

    return render(request, 'access/form.html', {'form': form, 'title': 'Выдача доступа'})


@login_required
def access_detail(request, access_id):
    """Детальная страница доступа"""
    access = get_object_or_404(AccessGrant, id=access_id)

    if access.employee != request.user and not request.user.employee_profile.has_permission('can_view_all_accesses'):
        messages.error(request, 'У вас нет прав на просмотр этого доступа')
        return redirect('access:my_access')

    return render(request, 'access/detail.html', {
        'access': access,
        'now': timezone.now().date()
    })


@login_required
def access_revoke(request, access_id):
    """Отозвать доступ (только для админов)"""
    if not request.user.employee_profile.has_permission('can_revoke_access'):
        messages.error(request, 'У вас нет прав на отзыв доступов')
        return redirect('access:my_access')

    access = get_object_or_404(AccessGrant, id=access_id)

    if request.method == 'POST':
        service_name = access.service_name
        employee_name = access.employee.employee_profile.full_name
        access.delete()
        messages.success(request, f'Доступ к "{service_name}" отозван у {employee_name}')
        return redirect('access:list')

    return render(request, 'access/confirm_revoke.html', {'access': access})