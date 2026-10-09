from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .views import user_list, user_permissions, custom_logout


app_name = 'accounts'

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def my_access(request):
    return render(request, 'my_access.html', {'user': request.user})

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('my-access/', views.my_access, name='my_access'),
    path('manage/', user_list, name='user_list'),
    path('manage/<int:user_id>/permissions/', user_permissions, name='user_permissions'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/permissions/', views.employee_permissions, name='employee_permissions'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    path('<int:employee_id>/generate-password/', views.employee_generate_password, name='employee_generate_password'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:employee_id>/permissions/', views.employee_permissions, name='employee_permissions'),
    path('employees/<int:employee_id>/update-credentials/', views.update_credentials, name='update_credentials'),
path('employees/<int:employee_id>/detail/', views.employee_detail, name='employee_detail'),

    # Личный кабинет
    path('profile/', views.my_profile, name='my_profile'),
    path('change-password/', views.change_my_password, name='change_my_password'),
    path('password-reset/', views.password_reset_request, name='password_reset'),

    # API
    path('api/role-permissions/', views.get_role_permissions_ajax, name='role_permissions_api'),

    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    path('profile/', views.profile_view, name='profile_view'),

]