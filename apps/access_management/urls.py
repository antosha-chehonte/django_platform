from django.urls import path
from . import views
from .reports import views as reports

app_name = 'access'

urlpatterns = [
    # Главная страница
    path('', views.access_home, name='home'),
    
    # Доступы к системам
    path('systems/', views.SystemAccessListView.as_view(), name='system_access_list'),
    path('systems/<int:pk>/', views.SystemAccessDetailView.as_view(), name='system_access_detail'),
    path('systems/create/', views.SystemAccessCreateView.as_view(), name='system_access_create'),
    path('systems/<int:pk>/update/', views.SystemAccessUpdateView.as_view(), name='system_access_update'),
    path('systems/<int:pk>/delete/', views.SystemAccessDeleteView.as_view(), name='system_access_delete'),
    
    # Цифровые подписи
    path('signatures/', views.DigitalSignatureListView.as_view(), name='digital_signature_list'),
    path('signatures/<int:pk>/', views.DigitalSignatureDetailView.as_view(), name='digital_signature_detail'),
    path('signatures/create/', views.DigitalSignatureCreateView.as_view(), name='digital_signature_create'),
    path('signatures/<int:pk>/update/', views.DigitalSignatureUpdateView.as_view(), name='digital_signature_update'),
    path('signatures/<int:pk>/delete/', views.DigitalSignatureDeleteView.as_view(), name='digital_signature_delete'),
    path('signatures/<int:pk>/download/', views.DigitalSignatureDownloadView.as_view(), name='digital_signature_download'),
    path('signatures/parse-certificate/', views.CertificateParseAjaxView.as_view(), name='certificate_parse_ajax'),
    
    # Отчеты
    path('reports/', reports.ReportsHomeView.as_view(), name='reports_home'),
    path('reports/system-access/active/', reports.SystemAccessActiveReportView.as_view(), name='report_system_access_active'),
    path('reports/system-access/expiring/', reports.SystemAccessExpiringReportView.as_view(), name='report_system_access_expiring'),
    path('reports/digital-signature/active/', reports.DigitalSignatureActiveReportView.as_view(), name='report_signature_active'),
    path('reports/digital-signature/missing/', reports.DigitalSignatureMissingReportView.as_view(), name='report_signature_missing'),
    path('reports/digital-signature/expiring/', reports.DigitalSignatureExpiringReportView.as_view(), name='report_signature_expiring'),
]

