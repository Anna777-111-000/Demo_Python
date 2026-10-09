from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    path('', views.request_list, name='list'),
    path('create/', views.request_create, name='create'),
    path('<int:pk>/', views.request_detail, name='detail'),
    path('<int:pk>/take/', views.request_take, name='take'),
    path('<int:pk>/close/', views.request_close, name='close'),
    path('<int:pk>/reject/', views.request_reject, name='reject'),
    path('<int:pk>/assign/', views.request_assign, name='assign'),
    path('<int:pk>/comment/', views.request_comment, name='comment'),
    path('api/hr-webhook/', views.hr_webhook, name='hr_webhook'),
    path('guest/admin/', views.create_for_admin, name='create_for_admin'),
    path('guest/development/', views.create_for_development, name='create_for_development'),
    path('all/', views.all_requests, name='all_requests'),
    path('tickets/', views.all_tickets, name='all_tickets'),


]