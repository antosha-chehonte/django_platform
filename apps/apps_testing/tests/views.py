# apps_testing/tests/views.py
import random
import uuid
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Test, TestSession, Question, UserAnswer
from .forms import TestAccessForm, TestRegistrationForm
from .utils import generate_test_questions, calculate_test_results


def test_list(request):
    tests = Test.objects.filter(is_active=True)
    return render(request, 'apps_testing/tests/test_list.html', {'tests': tests})


def test_access(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_active=True)
    if request.method == 'POST':
        form = TestAccessForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] == test.password:
                request.session[f'test_{test_id}_passed'] = True
                return redirect('testing:test_register', test_id=test.id)
            else:
                form.add_error('password', 'Неверный пароль')
    else:
        form = TestAccessForm()
    return render(request, 'apps_testing/tests/test_access.html', {'test': test, 'form': form})


def test_register(request, test_id):
    if not request.session.get(f'test_{test_id}_passed'):
        return redirect('testing:test_access', test_id=test_id)

    test = get_object_or_404(Test, id=test_id, is_active=True)
    if request.method == 'POST':
        form = TestRegistrationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Создаем уникальный ключ сессии для пользователя
            if not request.session.session_key:
                request.session.create()
            session_key = uuid.uuid4().hex

            # Генерируем вопросы
            question_ids = generate_test_questions(test.id)
            if not question_ids:
                # Обработка случая, когда вопросов нет
                return render(request, 'apps_testing/tests/error.html', {'message': 'В этом тесте нет вопросов.'})

            # Создаем сессию тестирования
            test_session = TestSession.objects.create(
                test=test,
                first_name=data['first_name'],
                last_name=data['last_name'],
                middle_name=data['middle_name'],
                session_key=session_key,
                selected_questions={'order': question_ids}
            )

            # Сохраняем ID нашей сессии тестирования в сессию Django,
            # чтобы знать, с какой попыткой мы работаем.
            request.session['test_session_id'] = test_session.id
            return redirect('testing:test_start')
    else:
        form = TestRegistrationForm()

    return render(request, 'apps_testing/tests/test_register.html', {'test': test, 'form': form})


# Промежуточная страница для начала теста
def test_start(request):
    session_id = request.session.get('test_session_id')
    if not session_id:
        return redirect('testing:test_list')

    test_session = get_object_or_404(TestSession, id=session_id)
    if test_session.is_completed:
        return redirect('testing:test_result', session_key=test_session.session_key)

    end_time = test_session.start_time + timedelta(minutes=test_session.test.time_limit)

    context = {
        'session': test_session,
        'time_limit_seconds': test_session.test.time_limit * 60,
        'server_end_time': end_time.isoformat()
    }
    return render(request, 'apps_testing/tests/test_start.html', context)


# --- AJAX VIEWS ---
def get_session_and_check_time(request):
    """Вспомогательная функция для получения сессии и проверки времени."""
    session_id = request.session.get('test_session_id')
    if not session_id:
        raise Http404("Сессия не найдена.")

    session = get_object_or_404(TestSession.objects.select_related('test'), id=session_id)

    if session.is_completed:
        return session, True  # Сессия завершена

    time_limit = session.test.time_limit
    if timezone.now() > session.start_time + timedelta(minutes=time_limit):
        calculate_test_results(session)
        return session, True  # Время вышло

    return session, False  # Тест продолжается


def get_question_ajax(request):
    session, is_finished = get_session_and_check_time(request)
    if is_finished:
        return JsonResponse({'status': 'finished', 'result_url': reverse('testing:test_result', args=[session.session_key])})

    q_index = int(request.GET.get('index', 0))
    question_ids = session.selected_questions.get('order', [])

    if not (0 <= q_index < len(question_ids)):
        return JsonResponse({'error': 'Invalid question index'}, status=400)

    question_id = question_ids[q_index]
    question = get_object_or_404(Question, id=question_id)

    # Перемешиваем варианты ответов
    options = [
        (1, question.option_1),
        (2, question.option_2),
        (3, question.option_3),
        (4, question.option_4),
    ]
    random.shuffle(options)

    user_answer = UserAnswer.objects.filter(session=session, question=question).first()

    return JsonResponse({
        'status': 'ok',
        'question_id': question.id,
        'text': question.text,
        'options': options,
        'total_questions': len(question_ids),
        'current_index': q_index,
        'selected_option': user_answer.selected_option if user_answer else None
    })


@require_POST
def save_answer_ajax(request):
    session, is_finished = get_session_and_check_time(request)
    if is_finished:
        return JsonResponse({'status': 'finished', 'result_url': reverse('testing:test_result', args=[session.session_key])})

    question_id = request.POST.get('question_id')
    selected_option = request.POST.get('selected_option')

    if not question_id:
        return HttpResponseBadRequest("Missing question_id")

    # Валидация
    try:
        selected_option = int(selected_option) if selected_option else None
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Invalid selected_option")

    question = get_object_or_404(Question, id=question_id)

    UserAnswer.objects.update_or_create(
        session=session,
        question=question,
        defaults={'selected_option': selected_option}
    )

    return JsonResponse({'status': 'ok', 'message': 'Answer saved'})


def test_finish(request):
    session_id = request.session.get('test_session_id')
    if not session_id:
        return redirect('testing:test_list')

    test_session = get_object_or_404(TestSession, id=session_id)
    calculate_test_results(test_session)

    # Очищаем сессию
    del request.session[f'test_{test_session.test.id}_passed']
    del request.session['test_session_id']

    return redirect('testing:test_result', session_key=test_session.session_key)


def test_result(request, session_key):
    test_session = get_object_or_404(TestSession.objects.select_related('test', 'result'), session_key=session_key)

    if not test_session.is_completed:
        return redirect('testing:test_list')  # Нельзя смотреть результат до завершения

    incorrect_answers = UserAnswer.objects.filter(
        session=test_session,
        is_correct=False
    ).select_related('question')

    skipped_questions_ids = test_session.selected_questions['order']
    answered_questions_ids = list(test_session.answers.values_list('question_id', flat=True))
    skipped_ids = [qid for qid in skipped_questions_ids if qid not in answered_questions_ids]
    skipped_questions = Question.objects.filter(id__in=skipped_ids)
    incorrect_answers_count = incorrect_answers.count()

    context = {
        'session': test_session,
        'result': test_session.result,
        'incorrect_answers': incorrect_answers,
        'skipped_questions': skipped_questions,
        'incorrect_answers_count': incorrect_answers_count,
    }
    return render(request, 'apps_testing/tests/test_result.html', context)
