# Generated manually for data migration

from django.db import migrations


def migrate_certificate_type_data(apps, schema_editor):
    """Перенос данных CertificateType из access_management в reference"""
    # Получаем старую модель из access_management
    OldCertificateType = apps.get_model('access_management', 'CertificateType')
    # Получаем новую модель из reference
    NewCertificateType = apps.get_model('reference', 'CertificateType')
    
    # Переносим все записи, сохраняя ID
    # Для этого используем bulk_create с указанием ID
    old_objects = list(OldCertificateType.objects.all())
    new_objects = []
    
    for old_obj in old_objects:
        new_obj = NewCertificateType(
            id=old_obj.id,  # Сохраняем старый ID
            name=old_obj.name,
            description=old_obj.description,
            is_active=old_obj.is_active,
            created_at=old_obj.created_at,
            updated_at=old_obj.updated_at
        )
        new_objects.append(new_obj)
    
    # Используем bulk_create для сохранения с ID
    if new_objects:
        NewCertificateType.objects.bulk_create(new_objects)


def reverse_migrate_certificate_type_data(apps, schema_editor):
    """Обратный перенос (для rollback)"""
    NewCertificateType = apps.get_model('reference', 'CertificateType')
    # При откате просто удаляем данные из новой модели
    # Старая модель будет восстановлена автоматически
    NewCertificateType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0009_add_certificate_type'),
        ('access_management', '0002_alter_digitalsignature_certificate_file'),
    ]

    operations = [
        migrations.RunPython(
            migrate_certificate_type_data,
            reverse_migrate_certificate_type_data
        ),
    ]

