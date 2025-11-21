from django.urls import path
from . import views
from .views import (
    PostsListView, PostsDetailView,
    HireNewEmployeeView, AssignExistingEmployeeView, MoveEmployeeView, FreePositionView,
    EmployeesListView, EmployeeDetailView, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView,
    PostCreateView, PostUpdateView, PostDeleteView,
    PositionHistoryListView, GetVacantPostsView
)

app_name = 'hr'

urlpatterns = [
    path('', views.hr_home, name='home'),
    path('posts/', PostsListView.as_view(), name='posts'),
    path('posts/create/', PostCreateView.as_view(), name='post_create'),
    path('posts/<int:pk>/', PostsDetailView.as_view(), name='post_detail'),
    path('posts/<int:pk>/update/', PostUpdateView.as_view(), name='post_update'),
    path('posts/<int:pk>/delete/', PostDeleteView.as_view(), name='post_delete'),
    path('posts/<int:pk>/hire/', HireNewEmployeeView.as_view(), name='post_hire_new'),
    path('posts/<int:pk>/assign/', AssignExistingEmployeeView.as_view(), name='post_assign_existing'),
    path('posts/<int:pk>/move/', MoveEmployeeView.as_view(), name='post_move'),
    path('posts/<int:pk>/free/', FreePositionView.as_view(), name='post_free'),
    path('ajax/departments/<int:department_id>/vacant-posts/', GetVacantPostsView.as_view(), name='get_vacant_posts'),
    path('posts/import-csv/', views.PostCSVImportView.as_view(), name='post_import_csv'),
    path('posts/download-csv-template/', views.PostCSVTemplateView.as_view(), name='post_download_csv_template'),
    path('employees/', EmployeesListView.as_view(), name='employees'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/import-csv/', views.EmployeeCSVImportView.as_view(), name='employee_import_csv'),
    path('employees/download-csv-template/', views.EmployeeCSVTemplateView.as_view(), name='employee_download_csv_template'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
    path('history/', PositionHistoryListView.as_view(), name='history'),
]


