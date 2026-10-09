from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout


@login_required
def home(request):
    """Точка входа CRM"""
    return render(request, 'crm/home.html')

def custom_logout(request):
    """Выход — работает и по GET, и по POST"""
    logout(request)
    return redirect('/accounts/login/')

def custom_logout(request):
    logout(request)
    return redirect('http://127.0.0.1:8000/accounts/login/')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('crm/', include('crm_core.urls')),
    path('accounts/logout/', custom_logout, name='logout'),
]