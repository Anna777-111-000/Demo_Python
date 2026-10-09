from .models import AuditLog


class AuditMiddleware:
    """Middleware для логирования входов и выходов"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Логируем действие после обработки запроса
        response = self.get_response(request)

        # Логируем вход пользователя
        if request.user.is_authenticated and request.method == 'POST':
            if request.path == '/admin/login/':
                AuditLog.objects.create(
                    user=request.user,
                    action='login',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    description=f'Вход в систему'
                )

        return response

    def get_client_ip(self, request):
        """Получить IP пользователя"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')