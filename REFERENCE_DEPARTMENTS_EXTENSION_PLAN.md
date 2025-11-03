# План доработки приложения reference для расширения модели Departments

## Обзор изменений

Добавление следующих полей в модель `Departments`:
- `dep_short_name` - короткое наименование подразделения
- `email` - официальный адрес электронной почты
- `zipcode` - почтовый индекс
- `city` - город
- `street` - улица
- `bldg` - здание/строение
- `net_id` - идентификатор сетевого узла подразделения (текст, 4 символа)
- `ip` - начальный IP адрес сети
- `mask` - префикс маски подсети

---

## Этап 1: Модель данных (apps/reference/models.py)

### 1.1. Добавление полей в модель Departments

```python
# Добавить после поля description:

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
```

### 1.2. Добавление валидаторов (если требуется)

Добавить импорты для валидаторов:
```python
from django.core.validators import MinValueValidator, MaxValueValidator
```

### 1.3. Обновление Meta класса (опционально)

При необходимости добавить новые поля в `ordering` или другие параметры Meta.

---

## Этап 2: Миграции базы данных

### 2.1. Создание миграции

```bash
python manage.py makemigrations reference
```

### 2.2. Применение миграции

```bash
python manage.py migrate reference
```

### 2.3. Проверка миграции

Проверить созданный файл миграции в `apps/reference/migrations/` на корректность.

---

## Этап 3: Формы (apps/reference/forms.py)

### 3.1. Обновление DepartmentForm

Добавить новые поля в `fields` и `widgets`:

```python
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Departments
        fields = [
            'name', 'code', 'sorting', 'description', 
            'dep_short_name', 'email',
            'zipcode', 'city', 'street', 'bldg',
            'net_id', 'ip', 'mask',
            'parent', 'is_logical', 'is_active'
        ]
        widgets = {
            # Существующие виджеты...
            'dep_short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
            'bldg': forms.TextInput(attrs={'class': 'form-control'}),
            'net_id': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '4',
                'pattern': '[A-Za-z0-9]{1,4}'
            }),
            'ip': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '192.168.1.0'
            }),
            'mask': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '32',
                'placeholder': '24'
            }),
        }
```

### 3.2. Обновление валидации формы (опционально)

Добавить кастомные валидаторы в `__init__` или метод `clean()`:
- Проверка формата `net_id` (4 символа)
- Проверка корректности IP-адреса
- Проверка диапазона mask (0-32)

### 3.3. Обновление CSVImportDepartmentForm

Обновить `help_text` для отражения новых полей:

```python
class CSVImportDepartmentForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Файл должен содержать колонки: Название;Код;Код сортировки;Описание;Короткое наименование;Email;Почтовый индекс;Город;Улица;Здание;Идентификатор узла;IP адрес;Маска;Родительское подразделение;Логическое;Активно',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
```

---

## Этап 4: Views (apps/reference/views.py)

### 4.1. Обновление DepartmentCSVImportView

Добавить обработку новых полей в метод `post()`:

```python
# В блоке обработки CSV добавить:
dep_short_name = row.get('Короткое наименование', '').strip()
email = row.get('Email', '').strip()
zipcode = row.get('Почтовый индекс', '').strip()
city = row.get('Город', '').strip()
street = row.get('Улица', '').strip()
bldg = row.get('Здание', '').strip()
net_id = row.get('Идентификатор узла', '').strip()
ip_str = row.get('IP адрес', '').strip()
mask_str = row.get('Маска', '').strip()

# Валидация net_id (если указан)
if net_id and len(net_id) > 4:
    errors.append(f"Строка {row_num}: net_id должен быть не более 4 символов")
    continue

# Валидация email (если указан)
if email:
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
    except ValidationError:
        errors.append(f"Строка {row_num}: неверный формат email")
        continue

# Валидация IP (если указан)
ip = None
if ip_str:
    try:
        from ipaddress import IPv4Address
        IPv4Address(ip_str)
        ip = ip_str
    except ValueError:
        errors.append(f"Строка {row_num}: неверный формат IP адреса")
        continue

# Валидация mask (если указана)
mask = None
if mask_str:
    try:
        mask = int(mask_str)
        if mask < 0 or mask > 32:
            errors.append(f"Строка {row_num}: маска должна быть от 0 до 32")
            continue
    except ValueError:
        errors.append(f"Строка {row_num}: неверный формат маски")
        continue

# При создании Departments.objects.create() добавить новые поля
```

### 4.2. Обновление DepartmentCSVTemplateView

Обновить заголовки CSV и примеры данных:

```python
writer.writerow([
    'Название', 'Код', 'Код сортировки', 'Описание', 
    'Короткое наименование', 'Email', 'Почтовый индекс', 
    'Город', 'Улица', 'Здание', 'Идентификатор узла', 
    'IP адрес', 'Маска', 'Родительское подразделение', 
    'Логическое', 'Активно'
])

# Примеры с новыми полями
writer.writerow([
    'Администрация', 'ADM001', 'ADM', 'Административное подразделение',
    'Админ', 'admin@company.ru', '123456', 'Москва', 
    'ул. Ленина', 'д. 1', 'ADM1', '192.168.1.0', '24',
    '', 'False', 'True'
])
```

### 4.3. Обновление поиска (DepartmentListView)

Добавить новые поля в поиск (опционально):

```python
def get_queryset(self):
    queryset = Departments.objects.filter(is_active=True)
    search = self.request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search) |
            Q(description__icontains=search) |
            Q(dep_short_name__icontains=search) |  # Новое
            Q(email__icontains=search) |  # Новое
            Q(city__icontains=search) |  # Новое
            Q(net_id__icontains=search)  # Новое
        )
    return queryset
```

---

## Этап 5: Шаблоны

### 5.1. Обновление departments_form.html

Добавить поля в форму создания/редактирования:

```html
<!-- После поля description -->

<!-- Короткое наименование -->
<div class="mb-3">
    <label for="{{ form.dep_short_name.id_for_label }}" class="form-label">
        {{ form.dep_short_name.label }}
    </label>
    {{ form.dep_short_name }}
    {% if form.dep_short_name.errors %}
    <div class="text-danger">{{ form.dep_short_name.errors }}</div>
    {% endif %}
</div>

<!-- Email -->
<div class="mb-3">
    <label for="{{ form.email.id_for_label }}" class="form-label">
        {{ form.email.label }}
    </label>
    {{ form.email }}
    {% if form.email.errors %}
    <div class="text-danger">{{ form.email.errors }}</div>
    {% endif %}
</div>

<!-- Адрес местонахождения -->
<div class="card mb-3">
    <div class="card-header">
        <h6 class="mb-0">Адрес местонахождения</h6>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-3">
                <label for="{{ form.zipcode.id_for_label }}" class="form-label">
                    {{ form.zipcode.label }}
                </label>
                {{ form.zipcode }}
            </div>
            <div class="col-md-9">
                <label for="{{ form.city.id_for_label }}" class="form-label">
                    {{ form.city.label }}
                </label>
                {{ form.city }}
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-8">
                <label for="{{ form.street.id_for_label }}" class="form-label">
                    {{ form.street.label }}
                </label>
                {{ form.street }}
            </div>
            <div class="col-md-4">
                <label for="{{ form.bldg.id_for_label }}" class="form-label">
                    {{ form.bldg.label }}
                </label>
                {{ form.bldg }}
            </div>
        </div>
    </div>
</div>

<!-- Сетевая информация -->
<div class="card mb-3">
    <div class="card-header">
        <h6 class="mb-0">Сетевая информация</h6>
    </div>
    <div class="card-body">
        <div class="row">
            <div class="col-md-4">
                <label for="{{ form.net_id.id_for_label }}" class="form-label">
                    {{ form.net_id.label }}
                </label>
                {{ form.net_id }}
            </div>
            <div class="col-md-4">
                <label for="{{ form.ip.id_for_label }}" class="form-label">
                    {{ form.ip.label }}
                </label>
                {{ form.ip }}
            </div>
            <div class="col-md-4">
                <label for="{{ form.mask.id_for_label }}" class="form-label">
                    {{ form.mask.label }}
                </label>
                {{ form.mask }}
            </div>
        </div>
    </div>
</div>
```

### 5.2. Обновление departments_detail.html

Добавить отображение новых полей:

```html
<!-- После поля description -->

{% if department.dep_short_name %}
<dt class="col-sm-3">Короткое наименование:</dt>
<dd class="col-sm-9">{{ department.dep_short_name }}</dd>
{% endif %}

{% if department.email %}
<dt class="col-sm-3">Email:</dt>
<dd class="col-sm-9">
    <a href="mailto:{{ department.email }}">{{ department.email }}</a>
</dd>
{% endif %}

<!-- Адрес местонахождения -->
{% if department.zipcode or department.city or department.street or department.bldg %}
<dt class="col-sm-3">Адрес:</dt>
<dd class="col-sm-9">
    {% if department.zipcode %}{{ department.zipcode }}, {% endif %}
    {% if department.city %}{{ department.city }}{% endif %}
    {% if department.street %}, {{ department.street }}{% endif %}
    {% if department.bldg %}, {{ department.bldg }}{% endif %}
</dd>
{% endif %}

<!-- Сетевая информация -->
{% if department.net_id or department.ip or department.mask %}
<dt class="col-sm-3">Сетевая информация:</dt>
<dd class="col-sm-9">
    {% if department.net_id %}
        <strong>ID узла:</strong> {{ department.net_id }}
    {% endif %}
    {% if department.ip %}
        <strong>IP:</strong> {{ department.ip }}
    {% endif %}
    {% if department.mask is not None %}
        /{{ department.mask }}
    {% endif %}
</dd>
{% endif %}
```

### 5.3. Обновление departments_list.html (опционально)

По желанию добавить колонки в таблицу списка или фильтры для поиска.

### 5.4. Обновление departments_csv_import.html

Обновить инструкции по формату CSV с новыми полями:

```html
<p><strong>Опциональные колонки:</strong></p>
<ul>
    <!-- Существующие... -->
    <li>Короткое наименование (может быть пустым)</li>
    <li>Email (может быть пустым, формат: example@domain.com)</li>
    <li>Почтовый индекс (может быть пустым)</li>
    <li>Город (может быть пустым)</li>
    <li>Улица (может быть пустой)</li>
    <li>Здание (может быть пустым)</li>
    <li>Идентификатор узла (может быть пустым, максимум 4 символа)</li>
    <li>IP адрес (может быть пустым, формат: 192.168.1.0)</li>
    <li>Маска (может быть пустым, значение от 0 до 32)</li>
</ul>
```

---

## Этап 6: Админ-панель (apps/reference/admin.py)

### 6.1. Обновление DepartmentsAdmin

#### 6.1.1. Обновление list_display

```python
list_display = ('code', 'name', 'dep_short_name', 'email', 'city', 'net_id', 'parent', 'is_active', 'created_at')
```

#### 6.1.2. Обновление search_fields

```python
search_fields = ('name', 'code', 'description', 'dep_short_name', 'email', 'city', 'net_id')
```

#### 6.1.3. Обновление fieldsets

```python
fieldsets = (
    ('Основная информация', {
        'fields': ('code', 'name', 'dep_short_name', 'description', 'email')
    }),
    ('Адрес местонахождения', {
        'fields': ('zipcode', 'city', 'street', 'bldg'),
        'classes': ('collapse',)
    }),
    ('Сетевая информация', {
        'fields': ('net_id', 'ip', 'mask'),
        'classes': ('collapse',)
    }),
    ('Иерархия', {
        'fields': ('parent',)
    }),
    ('Статус', {
        'fields': ('is_active', 'is_logical')
    }),
    ('Даты', {
        'fields': ('created_at', 'updated_at'),
        'classes': ('collapse',)
    }),
)
```

---

## Этап 7: Валидация и тестирование

### 7.1. Валидация полей модели

- Проверить корректность типов данных
- Проверить ограничения длины (net_id - 4 символа)
- Проверить валидацию IP адреса
- Проверить диапазон mask (0-32)

### 7.2. Тестирование форм

- Создание нового подразделения со всеми полями
- Редактирование существующего подразделения
- Валидация обязательных полей
- Валидация форматов (email, IP, mask)

### 7.3. Тестирование CSV импорта

- Импорт с новыми полями
- Импорт с частично заполненными полями
- Импорт с неверными форматами данных
- Проверка обработки ошибок

### 7.4. Тестирование админ-панели

- Отображение новых полей в списке
- Поиск по новым полям
- Создание/редактирование через админку

### 7.5. Тестирование шаблонов

- Отображение новых полей в детальном виде
- Отображение в форме создания/редактирования
- Корректность валидации на фронтенде

---

## Этап 8: Документация

### 8.1. Обновление документации модели

Добавить описание новых полей в docstring модели `Departments`.

### 8.2. Обновление README (если есть)

Документировать изменения в структуре данных.

### 8.3. Комментарии в коде

Добавить комментарии к новым полям, объясняющие их назначение.

---

## Порядок выполнения

1. **Этап 1**: Добавление полей в модель
2. **Этап 2**: Создание и применение миграций
3. **Этап 3**: Обновление форм
4. **Этап 4**: Обновление views (CSV импорт)
5. **Этап 5**: Обновление шаблонов
6. **Этап 6**: Обновление админ-панели
7. **Этап 7**: Тестирование всех компонентов
8. **Этап 8**: Документация

---

## Замечания

1. **Обратная совместимость**: Все новые поля должны быть `blank=True` или `null=True` для существующих записей
2. **Валидация IP**: Использовать `GenericIPAddressField` для автоматической валидации
3. **Валидация mask**: Добавить валидатор для диапазона 0-32
4. **Валидация net_id**: Максимум 4 символа, можно добавить regex паттерн
5. **Email валидация**: Django EmailField автоматически валидирует формат
6. **CSV импорт**: Убедиться, что обработка новых полей корректна при отсутствии заголовков

---

## Примеры данных для тестирования

### Пример корректных данных:
- `dep_short_name`: "Админ"
- `email`: "admin@company.ru"
- `zipcode`: "123456"
- `city`: "Москва"
- `street`: "ул. Ленина"
- `bldg`: "д. 1, стр. 2"
- `net_id`: "ADM1"
- `ip`: "192.168.1.0"
- `mask`: 24

### Пример CSV строки:
```
Администрация;ADM001;ADM;Административное подразделение;Админ;admin@company.ru;123456;Москва;ул. Ленина;д. 1;ADM1;192.168.1.0;24;;False;True
```

