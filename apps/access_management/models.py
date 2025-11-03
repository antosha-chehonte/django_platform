from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


# Валидатор для ограничения размера файла (1 МБ)
def validate_file_size(value):
    """Валидатор для ограничения размера файла (1 МБ)"""
    max_size = 1024 * 1024  # 1 МБ
    if value.size > max_size:
        raise ValidationError(
            f'Размер файла не должен превышать {max_size / (1024 * 1024):.1f} МБ'
        )


class SystemAccess(models.Model):
    """Доступ сотрудника к информационной системе"""
    
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_BLOCKED = 'blocked'
    STATUS_DELETED = 'deleted'
    STATUS_NEEDS_UPDATE = 'needs_update'
    
    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Активен'),
        (STATUS_SUSPENDED, 'Приостановлен'),
        (STATUS_BLOCKED, 'Заблокирован'),
        (STATUS_DELETED, 'Удален'),
        (STATUS_NEEDS_UPDATE, 'Требует актуализации'),
    )
    
    employee = models.ForeignKey(
        'hr.Employees',
        on_delete=models.CASCADE,
        verbose_name='Сотрудник'
    )
    system = models.ForeignKey(
        'reference.ITAsset',
        on_delete=models.PROTECT,
        verbose_name='Система'
    )
    login = models.CharField(max_length=200, verbose_name='Логин')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name='Статус'
    )
    access_granted_date = models.DateField(verbose_name='Дата получения доступа')
    access_blocked_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата блокировки'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Доступ к системе'
        verbose_name_plural = 'Доступы к системам'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee} - {self.system} ({self.login})"
    
    def clean(self):
        """Валидация данных"""
        super().clean()
        # Валидация даты блокировки (если указана)
        if self.access_blocked_date and self.access_granted_date:
            if self.access_blocked_date < self.access_granted_date:
                raise ValidationError({
                    'access_blocked_date': 'Дата блокировки не может быть раньше даты получения доступа.'
                })


class DigitalSignature(models.Model):
    """Цифровая подпись сотрудника"""
    
    STATUS_ACTIVE = 'active'
    STATUS_REVOKED = 'revoked'
    STATUS_NEEDS_UPDATE = 'needs_update'
    
    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Активна'),
        (STATUS_REVOKED, 'Аннулирована'),
        (STATUS_NEEDS_UPDATE, 'Требует актуализации'),
    )
    
    employee = models.ForeignKey(
        'hr.Employees',
        on_delete=models.CASCADE,
        verbose_name='Сотрудник'
    )
    certificate_type = models.ForeignKey(
        'reference.CertificateType',
        on_delete=models.PROTECT,
        verbose_name='Тип сертификата'
    )
    certificate_serial = models.CharField(
        max_length=200,
        verbose_name='Серийный номер сертификата'
    )
    certificate_alias = models.CharField(
        max_length=200,
        verbose_name='Отпечаток сертификата (alias)'
    )
    expiry_date = models.DateField(verbose_name='Дата окончания срока действия')
    carrier_serial = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Серийный номер носителя (токен)'
    )
    certificate_file = models.FileField(
        upload_to='certificates/',
        verbose_name='Файл сертификата',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['cer', 'pfx']),
            validate_file_size
        ],
        help_text='Форматы: .cer, .pfx. Максимальный размер: 1 МБ'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name='Статус'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Цифровая подпись'
        verbose_name_plural = 'Цифровые подписи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee} - {self.certificate_serial}"
    
    @property
    def is_expired(self):
        """Проверка истечения срока действия"""
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

