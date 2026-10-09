import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from .models import Company, Contact, Deal, Activity, CrmTask
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

User = get_user_model()


# ===== ХЕЛПЕРЫ =====

def check_perm(user, codename):
    try:
        return user.employee_profile.has_permission(codename)
    except Exception:
        return False


def _require_perm(user, codename):
    if not check_perm(user, codename):
        raise PermissionDenied("Недостаточно прав")


# ===== INDEX =====

@login_required
def index(request):
    return redirect('crm:crm_dashboard')


# ===== DASHBOARD =====

@login_required
def crm_dashboard(request):
    _require_perm(request.user, 'crm_view_deal')

    qs = Deal.objects.all()
    if not check_perm(request.user, 'crm_view_all_deals'):
        qs = qs.filter(owner=request.user)

    by_stage = []
    for code, name in Deal.STAGES:
        s = qs.filter(stage=code)
        by_stage.append({
            'code': code,
            'name': name,
            'count': s.count(),
            'sum': s.aggregate(x=Sum('amount'))['x'] or 0,
        })

    total_count = qs.count()
    total_sum = qs.aggregate(x=Sum('amount'))['x'] or 0
    won = qs.filter(stage='won')
    lost = qs.filter(stage='lost')
    conversion = (won.count() / total_count * 100) if total_count else 0

    top_managers = (
        qs.filter(stage='won')
        .values('owner__username', 'owner__employee_profile__full_name')
        .annotate(total=Sum('amount'), cnt=Count('id'))
        .order_by('-total')[:5]
    )

    return render(request, 'crm/dashboard.html', {
        'total_count': total_count,
        'total_sum': total_sum,
        'by_stage': by_stage,
        'won_count': won.count(),
        'won_sum': won.aggregate(x=Sum('amount'))['x'] or 0,
        'conversion': round(conversion, 1),
        'top_managers': top_managers,
    })


# ===== KANBAN =====

@login_required
def deal_kanban(request):
    _require_perm(request.user, 'crm_view_deal')

    qs = Deal.objects.select_related('company', 'owner').all()
    if not check_perm(request.user, 'crm_view_all_deals'):
        qs = qs.filter(owner=request.user)

    columns = []
    for code, name in Deal.STAGES:
        deals = qs.filter(stage=code)
        columns.append({
            'code': code,
            'name': name,
            'deals': deals,
            'sum': deals.aggregate(s=Sum('amount'))['s'] or 0,
            'count': deals.count(),
        })

    return render(request, 'crm/deal_kanban.html', {
        'columns': columns,
        'can_change_stage': check_perm(request.user, 'crm_change_stage'),
    })


# ===== DEALS =====

@login_required
def deal_list(request):
    _require_perm(request.user, 'crm_view_deal')

    qs = Deal.objects.select_related('company', 'owner').all()

    stage = request.GET.get('stage', '')
    if stage:
        qs = qs.filter(stage=stage)

    if not check_perm(request.user, 'crm_view_all_deals'):
        qs = qs.filter(owner=request.user)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(company__name__icontains=q))

    total_amount = qs.aggregate(s=Sum('amount'))['s'] or 0

    context = {
        'deals': qs,
        'stages': Deal.STAGES,
        'current_stage': stage,
        'query': q,
        'total_amount': total_amount,
        'can_edit': check_perm(request.user, 'crm_edit_deal'),
        'can_view_all': check_perm(request.user, 'crm_view_all_deals'),
        'can_export': check_perm(request.user, 'crm_export'),
    }
    return render(request, 'crm/deal_list.html', context)


@login_required
def deal_detail(request, pk):
    _require_perm(request.user, 'crm_view_deal')
    deal = get_object_or_404(Deal, pk=pk)

    if not check_perm(request.user, 'crm_view_all_deals') and deal.owner != request.user:
        raise PermissionDenied("Это не ваша сделка")

    activities = deal.activities.select_related('author', 'contact').all()

    context = {
        'deal': deal,
        'activities': activities,
        'can_edit': check_perm(request.user, 'crm_edit_deal'),
        'can_delete': check_perm(request.user, 'crm_delete_deal'),
        'can_change_stage': check_perm(request.user, 'crm_change_stage'),
        'can_log': check_perm(request.user, 'crm_log_activity'),
        'activity_types': Activity.TYPES,
    }
    return render(request, 'crm/deal_detail.html', context)


@login_required
def deal_create(request):
    _require_perm(request.user, 'crm_edit_deal')

    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            company_id = request.POST.get('company')
            if not title or not company_id:
                messages.error(request, 'Название и компания обязательны')
            else:
                deal = Deal.objects.create(
                    title=title,
                    company_id=company_id,
                    contact_id=request.POST.get('contact') or None,
                    amount=request.POST.get('amount') or 0,
                    stage=request.POST.get('stage', 'new'),
                    source=request.POST.get('source', '').strip(),
                    description=request.POST.get('description', '').strip(),
                    owner=request.user,
                )
                messages.success(request, f'Сделка «{deal.title}» создана')
                return redirect('crm:deal_detail', pk=deal.pk)
        except Exception as e:
            messages.error(request, f'Ошибка: {e}')

    context = {
        'companies': Company.objects.all(),
        'contacts': Contact.objects.select_related('company').all(),
        'stages': Deal.STAGES,
    }
    return render(request, 'crm/deal_form.html', context)


@login_required
def deal_edit(request, pk):
    _require_perm(request.user, 'crm_edit_deal')
    deal = get_object_or_404(Deal, pk=pk)

    if not check_perm(request.user, 'crm_view_all_deals') and deal.owner != request.user:
        raise PermissionDenied("Это не ваша сделка")

    if request.method == 'POST':
        deal.title = request.POST.get('title', '').strip() or deal.title
        company_id = request.POST.get('company')
        if company_id:
            deal.company_id = company_id
        deal.contact_id = request.POST.get('contact') or None
        deal.amount = request.POST.get('amount') or 0
        deal.stage = request.POST.get('stage') or deal.stage
        deal.source = request.POST.get('source', '').strip()
        deal.description = request.POST.get('description', '').strip()
        owner_id = request.POST.get('owner')
        if owner_id and check_perm(request.user, 'crm_view_all_deals'):
            deal.owner_id = owner_id
        deal.save()
        messages.success(request, 'Сделка обновлена')
        return redirect('crm:deal_detail', pk=deal.pk)

    context = {
        'deal': deal,
        'companies': Company.objects.all(),
        'contacts': Contact.objects.select_related('company').all(),
        'stages': Deal.STAGES,
        'can_reassign': check_perm(request.user, 'crm_view_all_deals'),
        'owners': User.objects.filter(is_active=True),
    }
    return render(request, 'crm/deal_form.html', context)


@login_required
def deal_change_stage(request, pk):
    _require_perm(request.user, 'crm_change_stage')
    deal = get_object_or_404(Deal, pk=pk)

    if request.method == 'POST':
        new_stage = request.POST.get('stage')
        if new_stage and new_stage in dict(Deal.STAGES):
            old = deal.get_stage_display()
            deal.stage = new_stage
            deal.save()
            messages.success(request, f'Стадия: {old} → {deal.get_stage_display()}')

    return redirect('crm:deal_detail', pk=deal.pk)


@login_required
def deal_delete(request, pk):
    _require_perm(request.user, 'crm_delete_deal')
    deal = get_object_or_404(Deal, pk=pk)

    if request.method == 'POST':
        title = deal.title
        deal.delete()
        messages.success(request, f'Сделка «{title}» удалена')
        return redirect('crm:deal_list')

    return render(request, 'crm/deal_confirm_delete.html', {'deal': deal})


@login_required
def deal_export(request):
    _require_perm(request.user, 'crm_export')

    qs = Deal.objects.select_related('company', 'owner').all()
    if not check_perm(request.user, 'crm_view_all_deals'):
        qs = qs.filter(owner=request.user)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="deals.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Название', 'Компания', 'Контакт', 'Стадия', 'Сумма', 'Валюта', 'Ответственный', 'Источник', 'Создана'])

    for d in qs:
        writer.writerow([
            d.title, d.company.name, d.contact.full_name if d.contact else '',
            d.get_stage_display(), d.amount, d.currency,
            d.owner.employee_profile.full_name if d.owner and hasattr(d.owner, 'employee_profile') else '',
            d.source, d.created_at.strftime('%Y-%m-%d'),
        ])

    return response


# ===== ACTIVITY =====

@login_required
def activity_create(request, deal_id):
    _require_perm(request.user, 'crm_log_activity')
    deal = get_object_or_404(Deal, pk=deal_id)

    if request.method == 'POST':
        Activity.objects.create(
            deal=deal,
            company=deal.company,
            kind=request.POST.get('kind', 'note'),
            subject=request.POST.get('subject', '').strip(),
            body=request.POST.get('body', '').strip(),
            author=request.user,
        )
        messages.success(request, 'Активность добавлена')

    return redirect('crm:deal_detail', pk=deal.pk)


# ===== COMPANIES =====

@login_required
def company_list(request):
    _require_perm(request.user, 'crm_view_company')
    companies = Company.objects.select_related('owner').all()

    q = request.GET.get('q', '').strip()
    if q:
        companies = companies.filter(Q(name__icontains=q) | Q(inn__icontains=q))

    return render(request, 'crm/company_list.html', {
        'companies': companies,
        'query': q,
        'can_edit': check_perm(request.user, 'crm_edit_company'),
    })


@login_required
def company_detail(request, pk):
    _require_perm(request.user, 'crm_view_company')
    company = get_object_or_404(Company, pk=pk)

    return render(request, 'crm/company_detail.html', {
        'company': company,
        'deals': company.deals.all(),
        'contacts': company.contacts.all(),
        'activities': company.activities.select_related('author').all()[:20],
        'can_edit': check_perm(request.user, 'crm_edit_company'),
    })


@login_required
def company_create(request):
    _require_perm(request.user, 'crm_edit_company')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Название обязательно')
        else:
            company = Company.objects.create(
                name=name,
                inn=request.POST.get('inn', '').strip(),
                website=request.POST.get('website', '').strip(),
                industry=request.POST.get('industry', '').strip(),
                address=request.POST.get('address', '').strip(),
                owner=request.user,
            )
            messages.success(request, f'Компания «{company.name}» создана')
            return redirect('crm:company_detail', pk=company.pk)

    return render(request, 'crm/company_form.html', {'is_create': True})


@login_required
def company_edit(request, pk):
    _require_perm(request.user, 'crm_edit_company')
    company = get_object_or_404(Company, pk=pk)

    if request.method == 'POST':
        company.name = request.POST.get('name', '').strip() or company.name
        company.inn = request.POST.get('inn', '').strip()
        company.website = request.POST.get('website', '').strip()
        company.industry = request.POST.get('industry', '').strip()
        company.address = request.POST.get('address', '').strip()
        company.save()
        messages.success(request, 'Компания обновлена')
        return redirect('crm:company_detail', pk=company.pk)

    return render(request, 'crm/company_form.html', {'company': company, 'is_create': False})


@login_required
def company_delete(request, pk):
    _require_perm(request.user, 'crm_edit_company')
    company = get_object_or_404(Company, pk=pk)

    if request.method == 'POST':
        name = company.name
        company.delete()
        messages.success(request, f'Компания «{name}» удалена')
        return redirect('crm:company_list')

    return render(request, 'crm/company_confirm_delete.html', {'company': company})


# ===== CONTACTS =====

@login_required
def contact_create(request, company_id):
    _require_perm(request.user, 'crm_edit_company')
    company = get_object_or_404(Company, pk=company_id)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        if not full_name:
            messages.error(request, 'ФИО обязательно')
        else:
            Contact.objects.create(
                company=company,
                full_name=full_name,
                position=request.POST.get('position', '').strip(),
                phone=request.POST.get('phone', '').strip(),
                email=request.POST.get('email', '').strip(),
                tg_nick=request.POST.get('tg_nick', '').strip(),
                is_primary=bool(request.POST.get('is_primary')),
            )
            messages.success(request, f'Контакт «{full_name}» добавлен')
            return redirect('crm:company_detail', pk=company.pk)

    return render(request, 'crm/contact_form.html', {'company': company, 'is_create': True})


@login_required
def contact_edit(request, pk):
    _require_perm(request.user, 'crm_edit_company')
    contact = get_object_or_404(Contact, pk=pk)

    if request.method == 'POST':
        contact.full_name = request.POST.get('full_name', '').strip() or contact.full_name
        contact.position = request.POST.get('position', '').strip()
        contact.phone = request.POST.get('phone', '').strip()
        contact.email = request.POST.get('email', '').strip()
        contact.tg_nick = request.POST.get('tg_nick', '').strip()
        contact.is_primary = bool(request.POST.get('is_primary'))
        contact.save()
        messages.success(request, 'Контакт обновлён')
        return redirect('crm:company_detail', pk=contact.company.pk)

    return render(request, 'crm/contact_form.html', {'contact': contact, 'company': contact.company, 'is_create': False})


@login_required
def contact_delete(request, pk):
    _require_perm(request.user, 'crm_edit_company')
    contact = get_object_or_404(Contact, pk=pk)
    company_pk = contact.company.pk

    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Контакт удалён')
        return redirect('crm:company_detail', pk=company_pk)

    return render(request, 'crm/contact_confirm_delete.html', {'contact': contact})

# ===== CRM KANBAN=====

@login_required
def task_kanban(request):
    """Канбан-доска задач"""
    if not (check_perm(request.user, 'crm_view_own_tasks') or
            check_perm(request.user, 'crm_view_all_tasks')):
        raise PermissionDenied("Нет доступа к задачам")

    qs = CrmTask.objects.select_related('deal', 'company', 'assignee', 'author')

    # Если нет права view_all — только свои задачи
    if not check_perm(request.user, 'crm_view_all_tasks'):
        qs = qs.filter(assignee=request.user)

    columns = []
    for code, name in CrmTask.STATUS_CHOICES:
        tasks = qs.filter(status=code)
        columns.append({
            'code': code,
            'name': name,
            'tasks': tasks,
            'count': tasks.count(),
        })

    return render(request, 'crm/task_kanban.html', {
        'columns': columns,
        'can_edit': check_perm(request.user, 'crm_edit_task'),
        'can_assign': check_perm(request.user, 'crm_assign_task'),
        'statuses': CrmTask.STATUS_CHOICES,
        'priorities': CrmTask.PRIORITY_CHOICES,
    })


@login_required
def task_create(request):
    """Создание задачи (быстрая форма)"""
    _require_perm(request.user, 'crm_edit_task')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'Название обязательно')
        else:
            task = CrmTask.objects.create(
                title=title,
                description=request.POST.get('description', '').strip(),
                status=request.POST.get('status', 'todo'),
                priority=request.POST.get('priority', 'medium'),
                assignee_id=request.POST.get('assignee') or request.user.pk,
                author=request.user,
                deal_id=request.POST.get('deal') or None,
                company_id=request.POST.get('company') or None,
                due_date=request.POST.get('due_date') or None,
            )
            messages.success(request, f'Задача «{task.title}» создана')
            return redirect('crm:task_kanban')

    return render(request, 'crm/task_form.html', {
        'companies': Company.objects.all(),
        'deals': Deal.objects.select_related('company').all(),
        'statuses': CrmTask.STATUS_CHOICES,
        'priorities': CrmTask.PRIORITY_CHOICES,
        'owners': User.objects.filter(is_active=True),
        'can_assign': check_perm(request.user, 'crm_assign_task'),
    })


@login_required
def task_edit(request, pk):
    _require_perm(request.user, 'crm_edit_task')
    task = get_object_or_404(CrmTask, pk=pk)

    if request.method == 'POST':
        task.title = request.POST.get('title', '').strip() or task.title
        task.description = request.POST.get('description', '').strip()
        task.status = request.POST.get('status') or task.status
        task.priority = request.POST.get('priority') or task.priority
        task.due_date = request.POST.get('due_date') or None
        task.deal_id = request.POST.get('deal') or None
        task.company_id = request.POST.get('company') or None
        if check_perm(request.user, 'crm_assign_task'):
            task.assignee_id = request.POST.get('assignee') or task.assignee_id
        task.save()
        messages.success(request, 'Задача обновлена')
        return redirect('crm:task_kanban')

    return render(request, 'crm/task_form.html', {
        'task': task,
        'companies': Company.objects.all(),
        'deals': Deal.objects.select_related('company').all(),
        'statuses': CrmTask.STATUS_CHOICES,
        'priorities': CrmTask.PRIORITY_CHOICES,
        'owners': User.objects.filter(is_active=True),
        'can_assign': check_perm(request.user, 'crm_assign_task'),
    })


@login_required
def task_delete(request, pk):
    _require_perm(request.user, 'crm_delete_task')
    task = get_object_or_404(CrmTask, pk=pk)

    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Задача «{title}» удалена')
        return redirect('crm:task_kanban')

    return render(request, 'crm/task_confirm_delete.html', {'task': task})


@login_required
def task_move(request, pk):
    """AJAX: сменить статус задачи (для drag-and-drop)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    _require_perm(request.user, 'crm_edit_task')
    task = get_object_or_404(CrmTask, pk=pk)

    import json
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    new_status = data.get('status')
    if new_status not in dict(CrmTask.STATUS_CHOICES):
        return JsonResponse({'error': 'invalid status'}, status=400)

    task.status = new_status
    task.save()
    return JsonResponse({'ok': True, 'status': task.status})


@login_required
def task_detail(request, pk):
    _require_perm(request.user, 'crm_view_own_tasks')
    task = get_object_or_404(CrmTask, pk=pk)

    if (not check_perm(request.user, 'crm_view_all_tasks') and
            task.assignee != request.user and task.author != request.user):
        raise PermissionDenied("Нет доступа к этой задаче")

    return render(request, 'crm/task_detail.html', {
        'task': task,
        'can_edit': check_perm(request.user, 'crm_edit_task'),
        'can_delete': check_perm(request.user, 'crm_delete_task'),
    })