# apps_testing/tests/apps_testing.py
from django.apps import AppConfig


class TestsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.apps_testing.tests'
