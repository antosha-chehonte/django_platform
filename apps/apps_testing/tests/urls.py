# apps_testing/tests/urls.py
from django.urls import path, reverse_lazy
from . import views

app_name = 'tests'

urlpatterns = [
    path('', views.test_list, name='test_list'),
    path('test/<int:test_id>/', views.test_access, name='test_access'),
    path('test/<int:test_id>/register/', views.test_register, name='test_register'),
    path('test/start/', views.test_start, name='test_start'),
    path('test/finish/', views.test_finish, name='test_finish'),
    path('test/result/<str:session_key>/', views.test_result, name='test_result'),

    # AJAX-эндпоинты
    path('ajax/get-question/', views.get_question_ajax, name='ajax_get_question'),
    path('ajax/save-answer/', views.save_answer_ajax, name='ajax_save_answer'),
]
