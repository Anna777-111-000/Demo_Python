from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from dashboards.views import dashboard
from dashboards.views import test_template
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from config.errors import error_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html', extra_context={'hide_navbar': True}), name='login'),
    path('accounts/', include('accounts.urls')),
    path('requests/', include('requests.urls')),
    path('tasks/', include('tasks.urls')),
    path('knowledge/', include('knowledge_base.urls')),
    path('access/', include('access_management.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('suggestions/', include('suggestions.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler400 = lambda request, exception=None: error_view(request, 400, exception)
handler403 = lambda request, exception=None: error_view(request, 403, exception)
handler404 = lambda request, exception=None: error_view(request, 404, exception)
handler500 = lambda request, exception=None: error_view(request, 500, exception)