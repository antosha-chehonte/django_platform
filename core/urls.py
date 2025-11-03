from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.project_info import views as project_info
# Импортируем наше представление для главной страницы
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', include('django.contrib.auth.urls'), name='logout'),
    path('', project_info.home_page, name='home'),
    path('project-info/', include('apps.project_info.urls', namespace='project-info')),
    path('testing/', include('apps.apps_testing.tests.urls', namespace='testing')),
    path('testing/moderator/', include(('apps.apps_testing.moderator.urls', 'moderator'), namespace='moderator')),
    path('reference/', include('apps.reference.urls', namespace='reference')),
    path('hr/', include(('apps.hr.urls', 'hr'), namespace='hr')),
    path('access/', include(('apps.access_management.urls', 'access'), namespace='access')),
    path('directory/', include(('apps.directory.urls', 'directory'), namespace='directory')),
]

# Для разработки: обслуживание медиа-файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
