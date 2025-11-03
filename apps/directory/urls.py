from django.urls import path
from . import views

app_name = 'directory'

urlpatterns = [
    path('', views.DirectoryListView.as_view(), name='directory'),
]

