from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import  user_passes_test
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Role, EmployeeProfile
from audit.models import AuditLog
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import BusinessPermission
from .forms import EmployeePermissionsForm, EmployeeCreateForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .models import CustomUser
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import secrets
import string
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmployeeProfile, Role, BusinessPermission, CustomUser


User = get_user_model()


def custom_logout(request):
    logout(request)
    return redirect('/accounts/login/')

def is_admin_or_director(user):
    """Проверка, является ли пользователь админом или директором"""
    if user.is_superuser:
        return True
    roles = user.roles.all()
    return roles.filter(code__in=['admin', 'director']).exists()


@login_required
@user_passes_test(is_admin_or_director)
def user_list(request):
    """Список пользователей для управления"""
    users = User.objects.all().prefetch_related('roles', 'profile')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@user_passes_test(is_admin_or_director)
def user_permissions(request, user_id):
    """Карточка управления правами пользователя"""
    target_user = get_object_or_404(User, id=user_id)

    # === ОГРАНИЧЕНИЯ ===
    current_user = request.user
    director_role = Role.objects.filter(code='director').first()
    admin_role = Role.objects.filter(code='admin').first()

    # Проверка: может ли текущий пользователь менять права
    can_edit = True
    error_message = None

    # Если целевой пользователь - директор
    if director_role and target_user.roles.filter(id=director_role.id).exists():
        if not current_user.is_superuser:
            can_edit = False
            error_message = "Только суперпользователь может изменять права директора IT-блока."

    # Если текущий пользователь не суперпользователь и не директор
    is_current_director = current_user.roles.filter(id=director_role.id).exists() if director_role else False
    is_current_admin = current_user.roles.filter(id=admin_role.id).exists() if admin_role else False

    # Если текущий пользователь - обычный админ (не директор и не суперпользователь)
    if not current_user.is_superuser and not is_current_director and is_current_admin:
        # Обычный админ не может менять права других админов
        if admin_role and target_user.roles.filter(id=admin_role.id).exists():
            can_edit = False
            error_message = "Администратор не может изменять права других администраторов."

        # Обычный админ не может назначать директора
        if director_role and request.POST.get('roles') and str(director_role.id) in request.POST.getlist('roles'):
            can_edit = False
            error_message = "Администратор не может назначать роль директора IT-блока."

    # Если целевой пользователь - суперпользователь
    if target_user.is_superuser:
        can_edit = False
        error_message = "Права суперпользователя нельзя изменять через этот интерфейс."

    # Получаем все доступные права из системы
    all_permissions = Permission.objects.select_related('content_type').all().order_by('content_type__app_label',
                                                                                       'codename')

    # Группируем права по приложениям
    permissions_by_app = {}
    for perm in all_permissions:
        app_label = perm.content_type.app_label
        if app_label not in permissions_by_app:
            permissions_by_app[app_label] = []
        permissions_by_app[app_label].append(perm)

    # Получаем текущие роли пользователя
    user_roles = target_user.roles.all()

    # Получаем эффективные права (из ролей)
    effective_perms = target_user.get_effective_permissions()
    effective_perm_codes = set([f"{p.content_type.app_label}.{p.codename}" for p in effective_perms])

    # Получаем оверрайды (доп. права и запреты)
    extra_perms = set()
    restricted_perms = set()
    if hasattr(target_user, 'profile'):
        extra_perms = set(
            [f"{p.content_type.app_label}.{p.codename}" for p in target_user.profile.extra_permissions.all()])
        restricted_perms = set(
            [f"{p.content_type.app_label}.{p.codename}" for p in target_user.profile.restricted_permissions.all()])

    # Финальные права с учётом оверрайдов
    final_perms = (effective_perm_codes | extra_perms) - restricted_perms

    if request.method == 'POST' and can_edit:
        # Получаем выбранные роли
        selected_role_ids = request.POST.getlist('roles')

        # === ПРОВЕРКА ЛИМИТОВ ===
        # Проверка: директор может быть только один
        if director_role and str(director_role.id) in selected_role_ids:
            # Если пытаются назначить директора
            existing_director = User.objects.filter(roles=director_role).exclude(id=target_user.id).first()
            if existing_director:
                return render(request, 'accounts/user_permissions.html', {
                    'target_user': target_user,
                    'user_roles': user_roles,
                    'all_roles': Role.objects.all(),
                    'permissions_by_app': permissions_by_app,
                    'effective_perm_codes': effective_perm_codes,
                    'extra_perms': extra_perms,
                    'restricted_perms': restricted_perms,
                    'final_perms': final_perms,
                    'error_message': f'Ошибка: Роль директора уже назначена пользователю {existing_director.get_full_name() or existing_director.username}. Может быть только один директор IT-блока.',
                    'can_edit': can_edit,
                })

        # Проверка: ограничение на количество админов (максимум 5)
        if admin_role:
            admin_role_obj = Role.objects.filter(code='admin').first()
            if admin_role_obj and admin_role_obj.max_users:
                # Если добавляем роль админа
                add_admin = str(admin_role_obj.id) in selected_role_ids and not target_user.roles.filter(
                    id=admin_role_obj.id).exists()
                # Если убираем роль админа
                remove_admin = str(admin_role_obj.id) not in selected_role_ids and target_user.roles.filter(
                    id=admin_role_obj.id).exists()

                if add_admin:
                    current_admin_count = User.objects.filter(roles=admin_role_obj).count()
                    if current_admin_count >= admin_role_obj.max_users:
                        return render(request, 'accounts/user_permissions.html', {
                            'target_user': target_user,
                            'user_roles': user_roles,
                            'all_roles': Role.objects.all(),
                            'permissions_by_app': permissions_by_app,
                            'effective_perm_codes': effective_perm_codes,
                            'extra_perms': extra_perms,
                            'restricted_perms': restricted_perms,
                            'final_perms': final_perms,
                            'error_message': f'Ошибка: Достигнут лимит роли "{admin_role_obj.name}" (максимум {admin_role_obj.max_users} человек).',
                            'can_edit': can_edit,
                        })

        # Сохраняем роли
        target_user.roles.set(selected_role_ids)

        # Сохраняем оверрайды
        if not hasattr(target_user, 'profile'):
            EmployeeProfile.objects.create(user=target_user)

        profile = target_user.profile

        # Дополнительные права (те, что отмечены вручную, но не входят в роли)
        selected_extra = request.POST.getlist('extra_permissions')
        extra_perm_objects = Permission.objects.filter(codename__in=[p.split('.')[-1] for p in selected_extra])
        profile.extra_permissions.set(extra_perm_objects)

        # Запрещённые права (те, что сняты вручную, но есть в ролях)
        selected_restricted = request.POST.getlist('restricted_permissions')
        restricted_perm_objects = Permission.objects.filter(
            codename__in=[p.split('.')[-1] for p in selected_restricted])
        profile.restricted_permissions.set(restricted_perm_objects)

        # Логируем изменение прав
        AuditLog.objects.create(
            user=request.user,
            action='permission_change',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            content_type=ContentType.objects.get_for_model(User),
            object_id=target_user.id,
            description=f'Изменены права пользователя {target_user.username}',
            old_value=None,
            new_value={'roles': selected_role_ids, 'extra': selected_extra, 'restricted': selected_restricted}
        )

        return redirect('user_list')

    context = {
        'target_user': target_user,
        'user_roles': user_roles,
        'all_roles': Role.objects.all(),
        'permissions_by_app': permissions_by_app,
        'effective_perm_codes': effective_perm_codes,
        'extra_perms': extra_perms,
        'restricted_perms': restricted_perms,
        'final_perms': final_perms,
        'can_edit': can_edit,
        'error_message': error_message,
    }
    return render(request, 'accounts/user_permissions.html', context)

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def my_access(request):
    return render(request, 'my_access.html', {'user': request.user})


def is_admin_or_director(user):
    """Проверка, имеет ли пользователь права админа или директора IT"""
    try:
        profile = user.employee_profile
        return profile.has_permission('can_assign_extra_permissions') or profile.primary_role.is_super_role
    except:
        return False

@login_required
def get_role_permissions_ajax(request):
    role_id = request.GET.get('role_id')
    if role_id:
        role = get_object_or_404(Role, id=role_id)
        permissions = role.get_all_permissions()
        perm_codenames = [p.codename for p in permissions]
        return JsonResponse({'permissions': perm_codenames})
    return JsonResponse({'permissions': []})


@login_required
def employee_list(request):
    """Список сотрудников с фильтрацией"""
    employees = EmployeeProfile.objects.select_related('primary_role', 'user').all()

    # Получаем параметры фильтрации
    search = request.GET.get('search', '').strip()
    role_id = request.GET.get('role', '')

    # Фильтрация по поиску (ФИО или email)
    if search:
        employees = employees.filter(
            models.Q(full_name__icontains=search) |
            models.Q(corporate_email__icontains=search) |
            models.Q(tg_nick__icontains=search)
        )

    # Фильтрация по роли
    if role_id:
        employees = employees.filter(primary_role_id=role_id)

    # Получаем список ролей для фильтра
    all_roles = Role.objects.all()

    context = {
        'employees': employees,
        'title': 'Управление сотрудниками',
        'search': search,
        'selected_role': role_id,
        'all_roles': all_roles,
    }
    return render(request, 'accounts/employee_list.html', context)


@login_required
def employee_create(request):
    """Создание нового сотрудника"""
    from django.contrib.auth.hashers import make_password
    import secrets
    import string

    def generate_random_password(length=12):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        username = request.POST.get('username', '').strip()
        corporate_email = request.POST.get('corporate_email', '').strip()
        personal_email = request.POST.get('personal_email', '').strip()
        tg_nick = request.POST.get('tg_nick', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', 'it')
        position = request.POST.get('position', 'Сотрудник').strip()
        role_id = request.POST.get('primary_role')

        # Валидация
        if not full_name:
            return JsonResponse({'success': False, 'error': 'ФИО обязательно для заполнения'}, status=400)

        if not corporate_email:
            return JsonResponse({'success': False, 'error': 'Корпоративная почта обязательна для заполнения'}, status=400)

        # Проверка уникальности email
        if CustomUser.objects.filter(email=corporate_email).exists():
            return JsonResponse({'success': False, 'error': f'Пользователь с почтой {corporate_email} уже существует'}, status=400)

        if EmployeeProfile.objects.filter(corporate_email=corporate_email).exists():
            return JsonResponse({'success': False, 'error': f'Профиль с почтой {corporate_email} уже существует'}, status=400)

        # Обработка логина
        if username:
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'success': False, 'error': f'Логин "{username}" уже занят'}, status=400)
        else:
            username_base = corporate_email.split('@')[0]
            username = username_base
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{username_base}_{counter}"
                counter += 1

        # Генерируем случайный пароль
        new_password = generate_random_password()

        # Создаём пользователя
        user = CustomUser.objects.create(
            username=username,
            email=corporate_email,
            password=make_password(new_password)
        )

        # Создаём профиль
        profile = EmployeeProfile.objects.create(
            user=user,
            full_name=full_name,
            corporate_email=corporate_email,
            personal_email=personal_email if personal_email else None,
            phone=phone if phone else None,
            department=department,
            position=position
        )

        # Обновляем tg_nick отдельно
        if hasattr(profile, 'tg_nick'):
            profile.tg_nick = tg_nick if tg_nick else None
            profile.save()

        # Назначаем роль
        if role_id and role_id != '':
            try:
                role = Role.objects.get(id=role_id)
                profile.primary_role = role
                profile.save()
            except Role.DoesNotExist:
                pass

        # СОХРАНЯЕМ ПАРОЛЬ В СЕССИЮ (после создания profile)
        request.session['temp_password_' + str(profile.id)] = new_password

        # Возвращаем JSON с данными для перенаправления
        return JsonResponse({
            'success': True,
            'employee_id': profile.id,
            'username': username,
            'password': new_password,
            'full_name': full_name
        })

    # GET запрос - показываем форму
    roles = Role.objects.all()
    context = {
        'title': 'Добавление сотрудника',
        'roles': roles,
        'is_create': True
    }
    return render(request, 'accounts/employee_form.html', context)


@login_required
def employee_permissions(request, employee_id):
    """Управление правами сотрудника"""
    employee = get_object_or_404(EmployeeProfile, id=employee_id)

    if request.method == 'POST':
        print("=== СОХРАНЕНИЕ ПРАВ ===")

        # 1. Сохраняем роль
        role_id = request.POST.get('primary_role')
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                employee.primary_role = role
            except Role.DoesNotExist:
                employee.primary_role = None
        else:
            employee.primary_role = None
        employee.save()

        # 2. Сохраняем дополнительные права
        role_perms = set()
        if employee.primary_role:
            role_perms = {p.codename for p in employee.primary_role.get_all_permissions()}

        all_checked_codenames = []
        for key, value in request.POST.items():
            if key.startswith('perm_') and value == 'on':
                codename = key.replace('perm_', '')
                all_checked_codenames.append(codename)

        extra_perms = []
        for codename in all_checked_codenames:
            if codename not in role_perms:
                try:
                    perm = BusinessPermission.objects.get(codename=codename)
                    extra_perms.append(perm)
                except BusinessPermission.DoesNotExist:
                    pass

        employee.extra_permissions.set(extra_perms)

        print(f"Прав от роли: {len(role_perms)}")
        print(f"Всего отмечено в форме: {len(all_checked_codenames)}")
        print(f"Доп. прав сохранено: {len(extra_perms)}")

        # ВОЗВРАЩАЕМ JSON (ВМЕСТО redirect)
        return JsonResponse({
            'success': True,
            'username': employee.user.username,
            'password': request.session.get('temp_password_' + str(employee.id), ''),
            'full_name': employee.full_name
        })

    # GET запрос - показываем форму
    all_permissions = BusinessPermission.objects.all().order_by('module', 'name')
    modules = {}
    for perm in all_permissions:
        module_ru = {
            'access': 'Доступы',
            'accounts': 'Пользователи и профили',
            'audit': 'Аудит и логи',
            'dashboard': 'Дашборды',
            'kb': 'База знаний',
            'notifications': 'Уведомления',
            'requests': 'Запросы админам',
            'suggestions': 'Предложения',
            'tasks': 'Задачник'
        }.get(perm.module, perm.module)

        if module_ru not in modules:
            modules[module_ru] = []
        modules[module_ru].append(perm)

    # Получаем права роли
    role_perms = set()
    if employee.primary_role:
        role_perms = {p.codename for p in employee.primary_role.get_all_permissions()}

    # Получаем доп. права
    extra_perms = {p.codename for p in employee.extra_permissions.all()}

    # Для отображения: галочка ставится, если право есть в роли ИЛИ в доп. правах
    effective_codenames = role_perms | extra_perms

    context = {
        'employee': employee,
        'modules': modules,
        'effective_codenames': effective_codenames,
        'all_roles': Role.objects.all(),
        'title': f'Права сотрудника: {employee.full_name}'
    }
    return render(request, 'accounts/employee_permissions.html', context)


@login_required
def employee_delete(request, employee_id):
    """Удаление сотрудника"""
    employee = get_object_or_404(EmployeeProfile, id=employee_id)

    if request.method == 'POST':
        full_name = employee.full_name
        user = employee.user

        # Логируем удаление
        from audit.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            description=f'Удалён сотрудник {full_name}',
            new_value={'deleted_by': request.user.username, 'deleted_at': str(timezone.now())}
        )

        # Удаляем профиль и пользователя
        employee.delete()
        user.delete()

        messages.success(request, f'Сотрудник {full_name} удалён')
        return redirect('accounts:employee_list')

    context = {
        'employee': employee,
        'title': f'Удаление сотрудника: {employee.full_name}'
    }
    return render(request, 'accounts/employee_confirm_delete.html', context)


@login_required
def profile_view(request):
    """Просмотр профиля текущего пользователя (только чтение)"""
    profile = request.user.employee_profile
    return render(request, 'accounts/profile_view.html', {
        'profile': profile,
        'user': request.user
    })


@login_required
def employee_generate_password(request, employee_id):
    """Генерация нового пароля для сотрудника (только админы/директор)"""
    employee = get_object_or_404(EmployeeProfile, id=employee_id)

    # Проверка прав
    if not request.user.employee_profile.has_permission('can_assign_extra_permissions'):
        return JsonResponse({'error': 'Нет прав'}, status=403)

    # Генерация случайного пароля (12 символов)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    new_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    # Сохраняем хеш пароля
    employee.user.password = make_password(new_password)
    employee.user.save()

    # Логируем действие
    from audit.models import AuditLog
    AuditLog.objects.create(
        user=request.user,
        action='password_change',
        description=f'Сгенерирован новый пароль для {employee.full_name}',
        new_value={'for_user': employee.user.username}
    )

    # Возвращаем пароль (только для показа один раз)
    return JsonResponse({'password': new_password})


@login_required
def my_profile(request):
    """Личный кабинет пользователя"""
    profile = request.user.employee_profile
    return render(request, 'accounts/my_profile.html', {'profile': profile})


@login_required
def change_my_password(request):
    """Смена пароля пользователем"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Неверный текущий пароль')
        elif new_password != confirm_password:
            messages.error(request, 'Новый пароль и подтверждение не совпадают')
        elif len(new_password) < 8:
            messages.error(request, 'Пароль должен содержать минимум 8 символов')
        else:
            request.user.set_password(new_password)
            request.user.save()

            # Логируем смену пароля
            from audit.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='password_change',
                description='Пользователь сменил пароль самостоятельно'
            )

            messages.success(request, 'Пароль успешно изменён. Пожалуйста, войдите заново.')
            return redirect('/accounts/login/')

    return render(request, 'accounts/change_password.html')


def password_reset_request(request):
    """Запрос на восстановление пароля через Telegram"""
    if request.method == 'POST':
        tg_nick = request.POST.get('tg_nick', '').strip()
        if tg_nick.startswith('@'):
            tg_nick = tg_nick[1:]

        try:
            profile = EmployeeProfile.objects.get(tg_nick=tg_nick)

            # Генерируем временный пароль
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))

            profile.user.set_password(temp_password)
            profile.user.save()

            # Логируем восстановление
            from audit.models import AuditLog
            AuditLog.objects.create(
                user=profile.user,
                action='password_reset',
                description=f'Восстановление пароля через Telegram для {tg_nick}'
            )

            # TODO: Отправить сообщение в Telegram ботом
            # Сейчас просто показываем сообщение и перенаправляем

            messages.success(request, f'Временный пароль отправлен в Telegram @{tg_nick}')
            return redirect('/accounts/login/')

        except EmployeeProfile.DoesNotExist:
            messages.error(request, 'Пользователь с таким Telegram не найден')
            return redirect('/accounts/password-reset/')

    return render(request, 'accounts/password_reset.html')

@login_required
def profile_view(request):
    profile = request.user.employee_profile
    return render(request, 'accounts/profile_view.html', {'profile': profile})

@login_required
def profile_edit(request):
    profile = request.user.employee_profile
    if request.method == 'POST':
        profile.phone = request.POST.get('phone', '')
        profile.tg_nick = request.POST.get('tg_nick', '')
        profile.position = request.POST.get('position', '')
        profile.save()
        return redirect('accounts:profile_view')
    return render(request, 'accounts/profile_edit.html', {'profile': profile})


@csrf_exempt
@login_required
def update_credentials(request, employee_id):
    """Обновление логина сотрудника (только админы/директор)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешён'}, status=405)

    employee = get_object_or_404(EmployeeProfile, id=employee_id)

    if not request.user.employee_profile.has_permission('can_assign_extra_permissions'):
        return JsonResponse({'success': False, 'error': 'Нет прав'}, status=403)

    data = json.loads(request.body)
    new_username = data.get('username', '').strip()

    if not new_username:
        return JsonResponse({'success': False, 'error': 'Логин не может быть пустым'})

    # Проверка уникальности
    if CustomUser.objects.exclude(id=employee.user.id).filter(username=new_username).exists():
        return JsonResponse({'success': False, 'error': 'Логин уже занят'})

    employee.user.username = new_username
    employee.user.save()

    return JsonResponse({'success': True})

@login_required
def employee_detail(request, employee_id):
    employee = get_object_or_404(EmployeeProfile, id=employee_id)
    return render(request, 'accounts/employee_detail.html', {'employee': employee})


