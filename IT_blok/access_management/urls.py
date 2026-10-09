from django.urls import path
from . import views

app_name = 'access'

urlpatterns = [
    path('', views.access_list, name='list'),
    path('my/', views.my_access, name='my_access'),
    path('create/', views.access_create, name='create'),
    path('<int:access_id>/revoke/', views.access_revoke, name='revoke'),
    path('<int:access_id>/detail/', views.access_detail, name='detail'),
]