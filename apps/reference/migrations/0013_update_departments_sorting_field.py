# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0012_postname_name_accusative'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departments',
            name='sorting',
            field=models.CharField(
                blank=True,
                help_text='Путь сортировки в формате: 001, 001.001, 001.002.001 и т.д. (сегменты по 3 цифры, разделенные точкой)',
                max_length=100,
                verbose_name='Код сортировки'
            ),
        ),
    ]

