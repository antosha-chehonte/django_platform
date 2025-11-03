from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Departments(models.Model):
    """Справочник подразделений организации"""
    name = models.CharField(max_length=200, verbose_name="Название подразделения")
    code = models.CharField(max_length=50, unique=True, verbose_name="Код подразделения")
    sorting = models.CharField(max_length=20, blank=True, verbose_name="Код сортировки")
    description = models.TextField(blank=True, verbose_name="Описание")
    
    # Дополнительная информация
    dep_short_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Короткое наименование"
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name="Официальный адрес электронной почты"
    )
    
    # Адрес местонахождения
    zipcode = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Почтовый индекс"
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Город"
    )
    
    street = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Улица"
    )
    
    bldg = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Здание/Строение"
    )
    
    # Сетевая информация
    net_id = models.CharField(
        max_length=4,
        blank=True,
        verbose_name="Идентификатор сетевого узла"
    )
    
    ip = models.GenericIPAddressField(
        protocol='IPv4',
        null=True,
        blank=True,
        verbose_name="Начальный IP адрес сети"
    )
    
    mask = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(32)],
        verbose_name="Префикс маски подсети (0-32)"
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительское подразделение"
    )
    is_logical = models.BooleanField(default=False, verbose_name="Логическое подразделение")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Подразделение"
        verbose_name_plural = "Подразделения"
        ordering = ['sorting', 'name']

    def __str__(self):
        return f"{self.name}"


class Postname(models.Model):
    """Справочник должностей"""
    name = models.CharField(max_length=200, verbose_name="Название должности")
    code = models.CharField(max_length=50, unique=True, verbose_name="Код должности")
    sorting = models.CharField(max_length=20, blank=True, verbose_name="Код сортировки")
    description = models.TextField(blank=True, verbose_name="Описание")
    category = models.CharField(max_length=100, blank=True, verbose_name="Категория должности")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ['sorting', 'name']

    def __str__(self):
        return f"{self.name}"


class ITAsset(models.Model):
    """Справочник информационных систем и информационных объектов организации"""
    
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Информационный актив"
        verbose_name_plural = "Информационные активы"
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class CertificateType(models.Model):
    """Справочник типов сертификатов цифровой подписи"""
    
    name = models.CharField(max_length=200, verbose_name="Название типа")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Тип сертификата"
        verbose_name_plural = "Типы сертификатов"
        ordering = ['name']
    
    def __str__(self):
        return self.name
