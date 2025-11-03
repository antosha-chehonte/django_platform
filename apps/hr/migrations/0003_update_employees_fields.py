# Generated manually for updating Employees model fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hr', '0002_alter_employees_gender'),
    ]

    operations = [
        migrations.RenameField(
            model_name='employees',
            old_name='phone',
            new_name='work_phone',
        ),
        migrations.AddField(
            model_name='employees',
            name='mobile_phone',
            field=models.CharField(blank=True, max_length=50, verbose_name='Мобильный телефон'),
        ),
        migrations.AddField(
            model_name='employees',
            name='appointment_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата назначения на должность'),
        ),
        migrations.AddField(
            model_name='employees',
            name='appointment_order_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата приказа о назначении'),
        ),
        migrations.AddField(
            model_name='employees',
            name='appointment_order_number',
            field=models.CharField(blank=True, max_length=100, verbose_name='Номер приказа о назначении'),
        ),
    ]

