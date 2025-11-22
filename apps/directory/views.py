import re
from django.views.generic import ListView
from django.db.models import Q

from apps.hr.models import Posts, Employees


class DirectoryListView(ListView):
    """Справочник сотрудников организации"""
    model = Posts
    template_name = 'directory/directory_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        # Получаем только занятые позиции с активными сотрудниками (исключаем уволенных и временно отсутствующих)
        queryset = Posts.objects.filter(
            status=Posts.STATUS_OCCUPIED,
            employee__status=Employees.STATUS_ACTIVE,
            is_active=True
        ).select_related('department', 'postname', 'employee')

        # Поиск по запросу (регистронезависимый для SQLite)
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            # Экранируем специальные символы regex для безопасного поиска
            search_escaped = re.escape(search_query)
            
            # Используем iregex для регистронезависимого поиска в SQLite
            queryset = queryset.filter(
                Q(employee__last_name__iregex=search_escaped) |
                Q(employee__first_name__iregex=search_escaped) |
                Q(employee__middle_name__iregex=search_escaped) |
                Q(employee__email__iregex=search_escaped) |
                Q(employee__work_phone__icontains=search_query) |
                Q(employee__mobile_phone__icontains=search_query) |
                Q(postname__name__iregex=search_escaped) |
                Q(department__name__iregex=search_escaped) |
                Q(department__code__iregex=search_escaped)
            )

        queryset = queryset.order_by(
            'department__sorting', 'department__name', 'postname__sorting', 'postname__name'
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '').strip()
        return context

