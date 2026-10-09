from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Article
from .forms import ArticleForm
from django.template.loader import render_to_string
from django.http import JsonResponse


def can_edit_article(user, article):
    if user.is_superuser:
        return True
    try:
        profile = user.employee_profile
        if profile.primary_role and profile.primary_role.codename in ['it_admin', 'it_director']:
            return True
        return article.created_by == user
    except:
        return False


def can_delete_article(user):
    if user.is_superuser:
        return True
    try:
        profile = user.employee_profile
        return profile.primary_role and profile.primary_role.codename in ['it_admin', 'it_director']
    except:
        return False


def can_create_article(user):
    if user.is_superuser:
        return True
    try:
        profile = user.employee_profile
        if profile.primary_role and profile.primary_role.codename in ['it_admin', 'it_director', 'department_head']:
            return True
        return profile.has_permission('can_create_article')
    except:
        return False


@login_required
def article_list(request):
    """Список статей с фильтрацией и поиском (без кнопки)"""
    # Получаем параметры из GET
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')

    # Фильтруем опубликованные статьи
    articles = Article.objects.filter(is_published=True)

    if search:
        articles = articles.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(tags__icontains=search)
        )

    if category:
        articles = articles.filter(category=category)

    # Мои статьи (все, включая черновики)
    my_articles = Article.objects.filter(created_by=request.user)

    context = {
        'articles': articles,
        'my_articles': my_articles,
        'search': search,
        'selected_category': category,
        'categories': Article.CATEGORY_CHOICES,
        'can_create': can_create_article(request.user),
    }
    return render(request, 'knowledge/list.html', context)


@login_required
def article_detail(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if not article.is_published and article.created_by != request.user and not can_delete_article(request.user):
        messages.error(request, 'Статья ещё не опубликована')
        return redirect('knowledge:list')

    context = {
        'article': article,
        'can_edit': can_edit_article(request.user, article),
        'can_delete': can_delete_article(request.user),
    }
    return render(request, 'knowledge/detail.html', context)


@login_required
def article_create(request):
    if not can_create_article(request.user):
        messages.error(request, 'У вас нет прав на создание статей')
        return redirect('knowledge:list')

    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.created_by = request.user
            article.save()
            messages.success(request, f'Статья "{article.title}" успешно создана')
            return redirect('knowledge:detail', article_id=article.id)
    else:
        form = ArticleForm()

    return render(request, 'knowledge/form.html', {'form': form, 'title': 'Создание статьи'})


@login_required
def article_edit(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if not can_edit_article(request.user, article):
        messages.error(request, 'У вас нет прав на редактирование этой статьи')
        return redirect('knowledge:detail', article_id=article.id)

    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, f'Статья "{article.title}" обновлена')
            return redirect('knowledge:detail', article_id=article.id)
    else:
        form = ArticleForm(instance=article)

    return render(request, 'knowledge/form.html', {'form': form, 'title': 'Редактирование статьи'})


@login_required
def article_delete(request, article_id):
    article = get_object_or_404(Article, id=article_id)

    if not can_delete_article(request.user):
        messages.error(request, 'У вас нет прав на удаление статей')
        return redirect('knowledge:detail', article_id=article.id)

    if request.method == 'POST':
        title = article.title
        article.delete()
        messages.success(request, f'Статья "{title}" удалена')
        return redirect('knowledge:list')

    return render(request, 'knowledge/confirm_delete.html', {'article': article})


@login_required
def article_filter_ajax(request):
    """AJAX-фильтрация статей"""
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')

    articles = Article.objects.filter(is_published=True)

    if search:
        articles = articles.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(tags__icontains=search)
        )

    if category:
        articles = articles.filter(category=category)

    html = render_to_string('knowledge/_articles_list.html', {'articles': articles})
    return JsonResponse({'html': html})