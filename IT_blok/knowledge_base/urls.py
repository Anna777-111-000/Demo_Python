from django.urls import path
from . import views

app_name = 'knowledge'

urlpatterns = [
    path('', views.article_list, name='list'),
    path('<int:article_id>/', views.article_detail, name='detail'),
    path('create/', views.article_create, name='create'),
    path('<int:article_id>/edit/', views.article_edit, name='edit'),
    path('<int:article_id>/delete/', views.article_delete, name='delete'),
    path('api/filter/', views.article_filter_ajax, name='filter_ajax'),

]