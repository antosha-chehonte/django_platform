# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0005_employees_full_name_accusative_employees_ip_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='employees',
            name='status',
            field=models.CharField(choices=[('active', 'Активен'), ('dismissed', 'Уволен'), ('temporary_absence', 'Временно отсутствует')], default='active', max_length=20, verbose_name='Статус'),
        ),
        migrations.RunPython(
            # Устанавливаем статус на основе is_active для существующих записей
            lambda apps, schema_editor: apps.get_model('hr', 'Employees').objects.filter(is_active=False).update(status='dismissed'),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]

