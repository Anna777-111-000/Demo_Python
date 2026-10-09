import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Role, EmployeeProfile

User = get_user_model()

data = {
    'admin':     ('Администратор',         'it_director',  'admin'),
    'manager1':  ('Иван Менеджеров',       'sales_manager','manager'),
    'head1':     ('Пётр Руководителев',    'sales_head',   'manager'),
    'marketer1': ('Ольга Маркетинг',       'marketer',     'manager'),
    'dev1':      ('Дмитрий Разработчиков', 'it_employee',  'developer'),
    'tester1':   ('Татьяна Тестировщикова','it_employee',  'tester'),
}

for username, (full_name, role_code, worker_type) in data.items():
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"{username}: НЕТ пользователя")
        continue

    role = Role.objects.filter(codename=role_code).first()
    if not role:
        print(f"{username}: роль '{role_code}' НЕ найдена — пропускаю")
        continue

    profile, created = EmployeeProfile.objects.get_or_create(
        user=u,
        defaults={
            'full_name': full_name,
            'corporate_email': f'{username}@local',
            'worker_type': worker_type,
            'primary_role': role,
        }
    )
    if not created:
        profile.full_name = full_name
        profile.corporate_email = f'{username}@local'
        profile.worker_type = worker_type
        profile.primary_role = role
        profile.save()

    action = 'создан' if created else 'обновлён'
    print(f"{username}: профиль {action} → роль {role.name}")

print("\nВсего профилей:", EmployeeProfile.objects.count())