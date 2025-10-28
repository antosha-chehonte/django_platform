# apps/project_info/views.py

from django.shortcuts import render

# Представление для главной страницы
def home_page(request):
    """
    Отображает главную страницу со списком доступных приложений.
    """
    # В будущем этот список будет формироваться динамически
    # или браться из базы данных.
    apps_list = [
        {
            'name': 'Информация о платформе',
            'description': 'Страница с подробной информацией о всей платформе и доступных приложениях.',
            'url': 'project-info:project_description',  # Имя URL из project_info.urls
        },
        {
            'name': 'Тестирование',
            'description': 'Наборы тестов для проведения дистанционного тестирования.',
            'url': 'tests:test_list'
        },
        {
            'name': 'Управление тестами',
            'description': 'Приложение для управления тестами и проверки отчетов о тестировании.',
            'url': 'moderator:dashboard'
        },
        {
            'name': 'Справочники',
            'description': 'Приложение для управления справочниками.',
            'url': 'reference:reference_home'
        },
        {
            'name': 'Управление сотрудниками',
            'description': 'Приложение для управления сведениями о сотрудниках.',
            'url': 'hr:home'
        },
    ]

    context = {
        'title': 'Главная страница',
        'apps_list': apps_list,
    }
    return render(request, 'home.html', context)


# Представление для страницы с описанием проекта
def project_description_page(request):
    """
    Отображает страницу с описанием проекта.
    """
    context = {
        'title': 'О платформе',
    }
    return render(request, 'project_info/description.html', context)