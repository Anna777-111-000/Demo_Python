from django.shortcuts import render


ERROR_MESSAGES = {
    400: {
        'title': 'Неверный запрос',
        'code': '400',
        'message': 'Сервер не смог обработать запрос. Проверьте данные и попробуйте снова.',
        'icon': '⚠️',
    },
    403: {
        'title': 'Доступ запрещён',
        'code': '403',
        'message': 'У вас нет прав для просмотра этой страницы. Обратитесь к администратору.',
        'icon': '🔒',
    },
    404: {
        'title': 'Страница не найдена',
        'code': '404',
        'message': 'Такой страницы не существует или она была удалена.',
        'icon': '🔍',
    },
    500: {
        'title': 'Внутренняя ошибка сервера',
        'code': '500',
        'message': 'Что-то пошло не так на сервере. Мы уже знаем о проблеме.',
        'icon': '💥',
    },
}


def error_view(request, code=500, exception=None):
    """Универсальный обработчик ошибок: смотрит код и выводит нужный текст"""
    data = ERROR_MESSAGES.get(code, {
        'title': 'Ошибка',
        'code': str(code),
        'message': 'Произошла неизвестная ошибка.',
        'icon': '❌',
    })
    return render(request, 'errors/error.html', {
        'error': data,
        'code': code,
    })