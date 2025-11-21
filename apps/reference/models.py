from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import re


class Departments(models.Model):
    """Справочник подразделений организации"""
    name = models.CharField(max_length=200, verbose_name="Название подразделения")
    code = models.CharField(max_length=50, unique=True, verbose_name="Код подразделения")
    sorting = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Код сортировки",
        help_text="Путь сортировки в формате: 001, 001.001, 001.002.001 и т.д. (сегменты по 3 цифры, разделенные точкой)"
    )
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
    
    def clean(self):
        """Валидация модели"""
        super().clean()
        # Валидация sorting - должен быть в формате пути (001, 001.001, и т.д.)
        if self.sorting:
            if not re.match(r'^(\d{3})(\.\d{3})*$', self.sorting):
                raise ValidationError({
                    'sorting': 'Код сортировки должен быть в формате: 001, 001.001, 001.002.001 и т.д. (сегменты по 3 цифры, разделенные точкой)'
                })
    
    @staticmethod
    def get_next_sorting_code(parent=None, exclude_pk=None):
        """
        Генерирует следующий код сортировки для дочернего элемента.
        Возвращает код вида: parent_sorting.001, parent_sorting.002 и т.д.
        
        Args:
            parent: Родительское подразделение (опционально)
            exclude_pk: ID подразделения, которое нужно исключить из поиска (для обновления)
        """
        if parent and parent.sorting:
            # Получаем все дочерние элементы с тем же родителем
            siblings = Departments.objects.filter(parent=parent)
            if exclude_pk:
                siblings = siblings.exclude(pk=exclude_pk)
            
            # Фильтруем только те, у которых sorting начинается с parent.sorting + '.'
            # и имеет правильный формат (ровно на один уровень глубже)
            parent_prefix = parent.sorting + '.'
            siblings_list = []
            for s in siblings:
                if s.sorting and s.sorting.startswith(parent_prefix):
                    # Проверяем, что это прямой потомок (ровно на один уровень глубже)
                    remaining = s.sorting[len(parent_prefix):]
                    if re.match(r'^\d{3}$', remaining):
                        siblings_list.append(s)
            
            if siblings_list:
                # Находим максимальный код среди братьев
                max_sorting = max(siblings_list, key=lambda x: x.sorting)
                if max_sorting and max_sorting.sorting:
                    # Извлекаем последний сегмент
                    last_segment = max_sorting.sorting.split('.')[-1]
                    try:
                        next_num = int(last_segment) + 1
                        return f"{parent.sorting}.{next_num:03d}"
                    except ValueError:
                        pass
            # Если нет братьев или ошибка, начинаем с 001
            return f"{parent.sorting}.001"
        else:
            # Корневой элемент - ищем максимальный код среди корневых
            root_departments = Departments.objects.filter(parent=None)
            if exclude_pk:
                root_departments = root_departments.exclude(pk=exclude_pk)
            
            # Фильтруем только те, у которых sorting в формате 001, 002 и т.д.
            valid_roots = [d for d in root_departments if d.sorting and re.match(r'^\d{3}$', d.sorting)]
            if valid_roots:
                max_sorting = max(valid_roots, key=lambda x: int(x.sorting))
                if max_sorting and max_sorting.sorting:
                    try:
                        next_num = int(max_sorting.sorting) + 1
                        return f"{next_num:03d}"
                    except ValueError:
                        pass
            return "001"
    
    def update_children_sorting(self):
        """
        Обновляет коды сортировки всех дочерних элементов при изменении родителя.
        """
        if not self.sorting:
            return
        
        children = Departments.objects.filter(parent=self)
        for child in children:
            # Генерируем новый код на основе нового родителя
            new_sorting = Departments.get_next_sorting_code(parent=self, exclude_pk=child.pk)
            child.sorting = new_sorting
            child.save()
            # Рекурсивно обновляем потомков
            child.update_children_sorting()
    
    def get_all_descendants(self):
        """
        Возвращает все дочерние подразделения (рекурсивно).
        """
        descendants = []
        children = Departments.objects.filter(parent=self).order_by('sorting')
        for child in children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def get_level(self):
        """
        Возвращает уровень вложенности (0 для корневых элементов).
        """
        if not self.sorting:
            return 0
        return len(self.sorting.split('.')) - 1


class Postname(models.Model):
    """Справочник должностей"""
    name = models.CharField(max_length=200, verbose_name="Название должности")
    name_accusative = models.CharField(max_length=200, blank=True, verbose_name="Название должности в винительном падеже")
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
