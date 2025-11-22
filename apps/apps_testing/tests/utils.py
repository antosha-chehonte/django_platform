# apps_testing/tests/utils.py
import random
from decimal import Decimal
from django.utils import timezone
from .models import Test, Question, TestSession, TestResult, UserAnswer


def generate_test_questions(test_id: int) -> list:
    """Генерирует и перемешивает список ID вопросов для сессии."""
    test = Test.objects.get(id=test_id)
    question_ids = []

    # .prefetch_related() для оптимизации
    question_sets = test.question_sets.prefetch_related('questions')

    for q_set in question_sets:
        # Получаем все ID вопросов для набора
        all_question_ids = list(q_set.questions.values_list('id', flat=True))
        # Выбираем случайные вопросы, если их больше, чем требуется
        count_to_select = min(len(all_question_ids), test.questions_per_set)
        question_ids.extend(random.sample(all_question_ids, count_to_select))

    random.shuffle(question_ids)
    return question_ids


def calculate_test_results(session: TestSession):
    """Подсчитывает результаты теста и создает объект TestResult."""
    if hasattr(session, 'result'):
        # Результат уже был посчитан
        return session.result

    # Перезагружаем сессию из базы данных, чтобы получить актуальный start_time
    session.refresh_from_db()

    total_questions = len(session.selected_questions.get('order', []))

    # select_related для оптимизации
    user_answers = session.answers.select_related('question').all()

    answered_count = 0
    correct_count = 0

    for answer in user_answers:
        if answer.selected_option is not None:
            answered_count += 1
            if answer.question.correct_option == answer.selected_option:
                answer.is_correct = True
                correct_count += 1
            else:
                answer.is_correct = False
        answer.save()

    skipped_count = total_questions - answered_count

    percentage = Decimal(0)
    if total_questions > 0:
        percentage = (Decimal(correct_count) / Decimal(total_questions)) * 100

    result = TestResult.objects.create(
        session=session,
        total_questions=total_questions,
        answered_questions=answered_count,
        correct_answers=correct_count,
        skipped_questions=skipped_count,
        percentage=percentage
    )

    # Устанавливаем start_time если он не был установлен
    # Используем время первого ответа как fallback
    end_time_now = timezone.now()
    
    if not session.start_time:
        first_answer = session.answers.order_by('answered_at').first()
        if first_answer and first_answer.answered_at:
            # Используем время первого ответа
            session.start_time = first_answer.answered_at
        else:
            # Если нет ответов, используем текущее время минус 1 минута
            # чтобы гарантировать разумную разницу с end_time
            from datetime import timedelta
            session.start_time = end_time_now - timedelta(minutes=1)
    
    # Убеждаемся, что start_time раньше end_time (с запасом минимум 1 секунда)
    if session.start_time >= end_time_now:
        from datetime import timedelta
        session.start_time = end_time_now - timedelta(seconds=1)
    
    session.is_completed = True
    session.end_time = end_time_now
    session.save()

    return result
