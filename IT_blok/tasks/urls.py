from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:task_id>/', views.task_detail, name='detail'),
    path('<int:task_id>/status/', views.task_update_status, name='update_status'),

    # API для Канбан-доски
    path('api/tasks/', views.task_list_api, name='task_list_api'),
    path('api/tasks/<int:task_id>/', views.task_detail_api, name='task_detail_api'),
    path('api/tasks/<int:task_id>/update-status/', views.task_update_status_api, name='task_update_status_api'),
    path('api/tasks/<int:task_id>/update/', views.task_update_api, name='task_update_api'),
    path('api/tasks/create/', views.task_create_api, name='task_create_api'),
    path('api/users/', views.users_api, name='users_api'),
    path('api/tasks/<int:task_id>/take/', views.task_take_api, name='task_take_api'),
    path('api/tasks/<int:task_id>/complete/', views.task_complete_api, name='task_complete_api'),
    path('api/tasks/<int:task_id>/defer/', views.task_defer_api, name='task_defer_api'),
]