from django.contrib import admin
from django.urls import path, include
from apps.project_info import views as project_info
# Импортируем наше представление для главной страницы
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', include('django.contrib.auth.urls'), name='logout'),
    path('', project_info.home_page, name='home'),
    path('project-info/', include('apps.project_info.urls', namespace='project-info')),
    path('testing/', include('apps.apps_testing.tests.urls', namespace='testing')),
    path('testing/moderator/', include(('apps.apps_testing.moderator.urls', 'moderator'), namespace='moderator')),
]
