# apps_testing/tests/models.py
from django.db import models
from django.contrib.auth.models import User

# 1. Модель QuestionSet (Набор вопросов)
class QuestionSet(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название набора")
    description = models.TextField(verbose_name="Пояснение к набору")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        app_label = 'tests'
        verbose_name = "Набор вопросов"
        verbose_name_plural = "Наборы вопросов"

# 2. Модель Question (Вопрос)
class Question(models.Model):
    question_set = models.ForeignKey(QuestionSet, on_delete=models.CASCADE, related_name='questions', verbose_name="Набор вопросов")
    text = models.TextField(verbose_name="Текст вопроса")
    option_1 = models.CharField(max_length=500, verbose_name="Вариант ответа 1")
    option_2 = models.CharField(max_length=500, verbose_name="Вариант ответа 2")
    option_3 = models.CharField(max_length=500, verbose_name="Вариант ответа 3")
    option_4 = models.CharField(max_length=500, verbose_name="Вариант ответа 4")
    correct_option = models.IntegerField(choices=[(1, 'Вариант 1'), (2, 'Вариант 2'), (3, 'Вариант 3'), (4, 'Вариант 4')], verbose_name="Правильный ответ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:50]

    class Meta:
        app_label = 'tests'
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

# 3. Модель Test (Тест)
class Test(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название теста")
    description = models.TextField(blank=True, verbose_name="Описание теста")
    question_sets = models.ManyToManyField(QuestionSet, verbose_name="Наборы вопросов")
    password = models.CharField(max_length=100, verbose_name="Пароль для доступа")
    time_limit = models.IntegerField(verbose_name="Время в минутах")
    is_active = models.BooleanField(default=True, verbose_name="Доступность теста")
    questions_per_set = models.IntegerField(default=5, verbose_name="Количество случайных вопросов из каждого набора")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        app_label = 'tests'
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы" 

# 4. Модель TestSession (Сессия тестирования)
class TestSession(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sessions')
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    session_key = models.CharField(max_length=40, unique=True, verbose_name="Ключ сессии")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    selected_questions = models.JSONField(verbose_name="Список ID выбранных вопросов") # { 'order': [id1, id2, ...] }

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    def __str__(self):
        return f"Сессия {self.id} для {self.test.title} от {self.get_full_name()}"

    class Meta:
        app_label = 'tests'
        verbose_name = "Сессия тестирования"
        verbose_name_plural = "Сессии тестирования"

# 5. Модель UserAnswer (Ответ пользователя)
class UserAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    selected_option = models.IntegerField(null=True, blank=True, verbose_name="Выбранный вариант")
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'tests'
        unique_together = ('session', 'question')
        verbose_name = "Ответ пользователя"
        verbose_name_plural = "Ответы пользователей"

    def __str__(self):
        return f"Ответ на вопрос {self.question.id} в сессии {self.session.id}"

# 6. Модель TestResult (Результат теста)
class TestResult(models.Model):
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name='result')
    total_questions = models.IntegerField(verbose_name="Общее количество вопросов")
    answered_questions = models.IntegerField(verbose_name="Количество отвеченных вопросов")
    correct_answers = models.IntegerField(verbose_name="Количество правильных ответов")
    skipped_questions = models.IntegerField(verbose_name="Количество пропущенных вопросов")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Процент правильных ответов")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Результат для сессии {self.session.id} - {self.percentage}%"

    class Meta:
        app_label = 'tests'
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты тестов"
