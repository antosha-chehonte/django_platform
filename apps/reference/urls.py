from django.urls import path
from . import views

app_name = 'reference'

urlpatterns = [
    # Главная страница справочников
    path('', views.reference_home, name='reference_home'),
    
    # Подразделения
    path('departments/', views.DepartmentListView.as_view(), name='departments_list'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='departments_detail'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='departments_create'),
    path('departments/<int:pk>/update/', views.DepartmentUpdateView.as_view(), name='departments_update'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='departments_delete'),
    
    # Должности
    path('postname/', views.PostnameListView.as_view(), name='postname_list'),
    path('postname/<int:pk>/', views.PostnameDetailView.as_view(), name='postname_detail'),
    path('postname/create/', views.PostnameCreateView.as_view(), name='postname_create'),
    path('postname/<int:pk>/update/', views.PostnameUpdateView.as_view(), name='postname_update'),
    path('postname/<int:pk>/delete/', views.PostnameDeleteView.as_view(), name='postname_delete'),
]

