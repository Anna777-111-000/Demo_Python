from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def suggestion_create(request):
    if request.method == 'POST':
        # TODO: сохранить предложение в БД
        suggestion_text = request.POST.get('suggestion', '')
        if suggestion_text:
            messages.success(request, 'Спасибо за ваше предложение!')
        else:
            messages.error(request, 'Пожалуйста, напишите предложение')
        return redirect('dashboard')

    return render(request, 'suggestions/form.html')