from django.urls import path
from . import views

app_name = 'suggestions'

urlpatterns = [
    path('create/', views.suggestion_create, name='create'),
]