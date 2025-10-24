# apps_testing/moderator/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'moderator'

urlpatterns = [
    path('', views.ModeratorDashboardView.as_view(), name='dashboard'),
    path('login/', views.ModeratorLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    # Question Sets
    path('question-sets/', views.QuestionSetListView.as_view(), name='qset_list'),
    path('question-sets/add/', views.QuestionSetCreateView.as_view(), name='qset_create'),
    path('question-sets/<int:pk>/edit/', views.QuestionSetUpdateView.as_view(), name='qset_update'),
    path('question-sets/<int:pk>/delete/', views.QuestionSetDeleteView.as_view(), name='qset_delete'),

    # Questions
    path('question-sets/<int:pk>/questions/', views.QuestionListView.as_view(), name='question_list'),
    path('question-sets/<int:qset_pk>/questions/add/', views.QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/edit/', views.QuestionUpdateView.as_view(), name='question_update'),
    path('questions/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),

    # Tests
    path('tests/', views.TestListView.as_view(), name='test_list'),
    path('tests/add/', views.TestCreateView.as_view(), name='test_create'),
    path('tests/<int:pk>/edit/', views.TestUpdateView.as_view(), name='test_update'),
    path('tests/<int:pk>/delete/', views.TestDeleteView.as_view(), name='test_delete'),

    # Results
    path('results/', views.ResultListView.as_view(), name='result_list'),
    path('results/<int:pk>/delete/', views.ResultDeleteView.as_view(), name='result_delete'),
    path('results/<int:result_id>/pdf/', views.export_result_pdf, name='export_pdf'),

    # Analytics
    path('analytics/question-errors/', views.QuestionErrorAnalyticsView.as_view(), name='question_error_analytics'),
]
