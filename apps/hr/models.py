from django.db import models
from django.core.exceptions import ValidationError

from apps.reference.models import Postname, Departments


class Employees(models.Model):
    GENDER_CHOICES = (
        ('M', 'Мужской'),
        ('F', 'Женский'),
    )

    STATUS_ACTIVE = 'active'
    STATUS_DISMISSED = 'dismissed'
    STATUS_TEMPORARY_ABSENCE = 'temporary_absence'
    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Активен'),
        (STATUS_DISMISSED, 'Уволен'),
        (STATUS_TEMPORARY_ABSENCE, 'Временно отсутствует'),
    )

    last_name = models.CharField(max_length=150, verbose_name='Фамилия')
    first_name = models.CharField(max_length=150, verbose_name='Имя')
    middle_name = models.CharField(max_length=150, blank=True, verbose_name='Отчество')
    full_name_accusative = models.CharField(max_length=300, blank=True, verbose_name='ФИО в винительном падеже')
    birth_date = models.DateField(verbose_name='Дата рождения')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Пол')

    work_phone = models.CharField(max_length=50, blank=True, verbose_name='Рабочий телефон')
    mobile_phone = models.CharField(max_length=50, blank=True, verbose_name='Мобильный телефон')
    ip_phone = models.CharField(max_length=20, blank=True, verbose_name='IP-телефон')
    email = models.EmailField(blank=True, verbose_name='Email')

    appointment_date = models.DateField(null=True, blank=True, verbose_name='Дата назначения на должность')
    appointment_order_date = models.DateField(null=True, blank=True, verbose_name='Дата приказа о назначении')
    appointment_order_number = models.CharField(max_length=100, blank=True, verbose_name='Номер приказа о назначении')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE, verbose_name='Статус')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['last_name', 'first_name', 'middle_name']

    def save(self, *args, **kwargs):
        # Синхронизируем is_active со статусом для обратной совместимости
        self.is_active = (self.status == self.STATUS_ACTIVE)
        super().save(*args, **kwargs)

    @property
    def is_active_property(self):
        """Вычисляемое свойство для обратной совместимости"""
        return self.status == self.STATUS_ACTIVE

    def __str__(self) -> str:
        full = f"{self.last_name} {self.first_name} {self.middle_name}".strip()
        return " ".join(full.split())


class Posts(models.Model):
    STATUS_VACANT = 'vacant'
    STATUS_OCCUPIED = 'occupied'
    STATUS_CHOICES = (
        (STATUS_VACANT, 'Вакантна'),
        (STATUS_OCCUPIED, 'Занята'),
    )

    postname = models.ForeignKey(Postname, on_delete=models.PROTECT, verbose_name='Должность')
    department = models.ForeignKey(Departments, on_delete=models.PROTECT, verbose_name='Подразделение')
    employee = models.ForeignKey(Employees, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Сотрудник')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_VACANT, verbose_name='Статус')

    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Штатная позиция'
        verbose_name_plural = 'Штатные позиции'

    def clean(self):
        super().clean()
        # Статус и employee должны быть согласованы
        if self.status == self.STATUS_OCCUPIED and self.employee is None:
            raise ValidationError({'employee': 'Для статуса "Занята" необходимо выбрать сотрудника.'})
        if self.status == self.STATUS_VACANT and self.employee is not None:
            raise ValidationError({'status': 'Для вакантной позиции сотрудник должен отсутствовать.'})

        # Жесткая валидация: сотрудник не может занимать более одной позиции одновременно
        if self.employee is not None:
            conflicting = Posts.objects.filter(employee=self.employee, status=self.STATUS_OCCUPIED)
            if self.pk:
                conflicting = conflicting.exclude(pk=self.pk)
            if conflicting.exists():
                raise ValidationError({'employee': 'Сотрудник уже занимает другую должность.'})

    def __str__(self) -> str:
        base = f"{self.postname}"
        if self.status == self.STATUS_OCCUPIED and self.employee:
            return f"{base} (занята: {self.employee})"
        return f"{base} (вакантна)"


class PositionHistory(models.Model):
    ACTION_HIRE = 'hire'
    ACTION_MOVE = 'move'
    ACTION_RETURN = 'return'
    ACTION_DISMISS = 'dismiss'
    ACTION_CHOICES = (
        (ACTION_HIRE, 'Принят'),
        (ACTION_MOVE, 'Перемещен'),
        (ACTION_RETURN, 'Возвращен'),
        (ACTION_DISMISS, 'Освобожден'),
    )

    employee = models.ForeignKey(Employees, on_delete=models.CASCADE, verbose_name='Сотрудник')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, verbose_name='Позиция')
    action = models.CharField(max_length=12, choices=ACTION_CHOICES, verbose_name='Действие')
    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'История позиции'
        verbose_name_plural = 'История позиций'
        ordering = ['-created_at']


