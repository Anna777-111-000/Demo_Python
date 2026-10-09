# Первый запуск (после клонирования)
## подтянуть ветку и перейти в неё
```
git fetch --all
git checkout it_crm_razrab
git pull origin it_crm_razrab
```
## IT_blok (порт 8000)
```
cd IT_blok
python -m venv .venv
.venv\Scripts\activate
pip install Django==5.0 django-ckeditor-5 pillow
python manage.py migrate
python manage.py loaddata accounts/fixtures/business_permissions.json
python manage.py loaddata accounts/fixtures/roles.json
python manage.py loaddata accounts/fixtures/users.json
python manage.py createsuperuser
python manage.py runserver
```
## CRM (порт 8001) — новое окно
```
cd CRM
python -m venv .venv
.venv\Scripts\activate
pip install Django==5.0 django-ckeditor-5 pillow
python manage.py runserver 8001
```
# Последующие запуски (всё уже установлено)
## Окно 1 — IT_blok
```
cd IT_blok
.venv\Scripts\activate
python manage.py runserver
```
## Окно 2 — CRM
```
cd CRM
.venv\Scripts\activate
python manage.py runserver 8001
```
