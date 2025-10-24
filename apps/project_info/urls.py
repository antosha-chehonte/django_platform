from django.urls import path
from apps.project_info.views import project_description_page

app_name = 'project_info'

urlpatterns = [
    path('', project_description_page, name='project_description'),
]