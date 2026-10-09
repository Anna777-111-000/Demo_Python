from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.index, name='index'),

    # Дашборд
    path('dashboard/', views.crm_dashboard, name='crm_dashboard'),

    # Канбан
    path('kanban/', views.deal_kanban, name='deal_kanban'),

    # Deals
    path('deals/', views.deal_list, name='deal_list'),
    path('deals/create/', views.deal_create, name='deal_create'),
    path('deals/export/', views.deal_export, name='deal_export'),
    path('deals/<int:pk>/', views.deal_detail, name='deal_detail'),
    path('deals/<int:pk>/edit/', views.deal_edit, name='deal_edit'),
    path('deals/<int:pk>/delete/', views.deal_delete, name='deal_delete'),
    path('deals/<int:pk>/stage/', views.deal_change_stage, name='deal_change_stage'),
    path('deals/<int:deal_id>/activity/', views.activity_create, name='activity_create'),

    # Companies
    path('companies/', views.company_list, name='company_list'),
    path('companies/create/', views.company_create, name='company_create'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('companies/<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('companies/<int:pk>/delete/', views.company_delete, name='company_delete'),

    # Contacts
    path('companies/<int:company_id>/contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),

    # Tasks (Kanban)
    path('tasks/', views.task_kanban, name='task_kanban'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/move/', views.task_move, name='task_move'),
]