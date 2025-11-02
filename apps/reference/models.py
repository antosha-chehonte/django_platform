from django.db import models


class Departments(models.Model):
    """Справочник подразделений организации"""
    name = models.CharField(max_length=200, verbose_name="Название подразделения")
    code = models.CharField(max_length=50, unique=True, verbose_name="Код подразделения")
    sorting = models.CharField(max_length=20, blank=True, verbose_name="Код сортировки")
    description = models.TextField(blank=True, verbose_name="Описание")
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
