from django.urls import path
from . import views

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
    
    # Типы сертификатов
    path('certificate-types/', views.CertificateTypeListView.as_view(), name='certificate_type_list'),
    path('certificate-types/create/', views.CertificateTypeCreateView.as_view(), name='certificate_type_create'),
    path('certificate-types/<int:pk>/update/', views.CertificateTypeUpdateView.as_view(), name='certificate_type_update'),
    path('certificate-types/<int:pk>/delete/', views.CertificateTypeDeleteView.as_view(), name='certificate_type_delete'),
]

