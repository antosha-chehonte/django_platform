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
    path('postname/import-csv/', views.PostnameCSVImportView.as_view(), name='postname_import_csv'),
    path('postname/download-csv-template/', views.PostnameCSVTemplateView.as_view(), name='postname_download_csv_template'),
    
    # Информационные активы
    path('itasset/', views.ITAssetListView.as_view(), name='itasset_list'),
    path('itasset/<int:pk>/', views.ITAssetDetailView.as_view(), name='itasset_detail'),
    path('itasset/create/', views.ITAssetCreateView.as_view(), name='itasset_create'),
    path('itasset/<int:pk>/update/', views.ITAssetUpdateView.as_view(), name='itasset_update'),
    path('itasset/<int:pk>/delete/', views.ITAssetDeleteView.as_view(), name='itasset_delete'),
]

