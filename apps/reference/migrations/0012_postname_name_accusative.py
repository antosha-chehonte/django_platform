# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0011_departments_bldg_departments_city_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='postname',
            name='name_accusative',
            field=models.CharField(blank=True, max_length=200, verbose_name='Название должности в винительном падеже'),
        ),
    ]

