from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.hr.models import Employees, Posts


@receiver(post_save, sender=Employees)
def update_access_on_employee_change(sender, instance, **kwargs):
    """Обновление статуса доступов при изменении статуса сотрудника"""
    if not instance.is_active:
        # Импортируем здесь, чтобы избежать циклических импортов
        from .models import SystemAccess, DigitalSignature
        
        SystemAccess.objects.filter(
            employee=instance,
            status__in=[SystemAccess.STATUS_ACTIVE, SystemAccess.STATUS_SUSPENDED]
        ).update(status=SystemAccess.STATUS_NEEDS_UPDATE)
        
        DigitalSignature.objects.filter(
            employee=instance,
            status=DigitalSignature.STATUS_ACTIVE
        ).update(status=DigitalSignature.STATUS_NEEDS_UPDATE)


@receiver(post_save, sender=Posts)
@receiver(post_delete, sender=Posts)
def update_access_on_post_change(sender, instance, **kwargs):
    """Обновление статуса доступов при изменении должности сотрудника"""
    if instance.employee:
        # Импортируем здесь, чтобы избежать циклических импортов
        from .models import SystemAccess, DigitalSignature
        
        SystemAccess.objects.filter(
            employee=instance.employee,
            status__in=[SystemAccess.STATUS_ACTIVE, SystemAccess.STATUS_SUSPENDED]
        ).update(status=SystemAccess.STATUS_NEEDS_UPDATE)
        
        DigitalSignature.objects.filter(
            employee=instance.employee,
            status=DigitalSignature.STATUS_ACTIVE
        ).update(status=DigitalSignature.STATUS_NEEDS_UPDATE)

