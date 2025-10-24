# apps_testing/moderator/views.py
import logging

from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.db.models import Count
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings

from apps.apps_testing.tests.models import Test, QuestionSet, Question, TestResult, UserAnswer
from .forms import TestForm, QuestionSetForm, QuestionForm, ModeratorLoginForm, QuestionErrorAnalyticsForm, ResultsFilterForm
from .mixins import ModeratorRequiredMixin, LogCreateUpdateMixin, LogDeleteMixin


class ModeratorLoginView(LoginView):
    template_name = 'apps_testing/moderator/login.html'
    form_class = ModeratorLoginForm # Используем кастомную форму


class ModeratorDashboardView(ModeratorRequiredMixin, TemplateView):
    template_name = 'apps_testing/moderator/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tests_count'] = Test.objects.count()
        context['qsets_count'] = QuestionSet.objects.count()
        context['results_count'] = TestResult.objects.count()
        return context


# --- Управление Наборами Вопросов ---
class QuestionSetListView(ModeratorRequiredMixin, ListView):
    model = QuestionSet
    template_name = 'apps_testing/moderator/question_set_list.html'
    context_object_name = 'qsets'


class QuestionSetCreateView(ModeratorRequiredMixin, LogCreateUpdateMixin, CreateView):
    model = QuestionSet
    form_class = QuestionSetForm
    template_name = 'apps_testing/moderator/question_set_form.html'
    success_url = reverse_lazy('moderator:qset_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        csv_file = form.cleaned_data.get('csv_file')
        has_header = form.cleaned_data.get('has_header')
        if csv_file:
            import csv, io
            content_bytes = csv_file.read()
            try:
                decoded = content_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    decoded = content_bytes.decode('cp1251')
                except UnicodeDecodeError:
                    decoded = content_bytes.decode('utf-8', errors='ignore')
            reader = csv.reader(io.StringIO(decoded), delimiter=';')
            if has_header:
                try:
                    next(reader)
                except StopIteration:
                    reader = []

            created = 0
            for row in reader:
                # Skip empty lines
                if not row or all((str(cell).strip() == '' for cell in row)):
                    continue
                if len(row) < 6:
                    continue
                question_text = row[0].strip()
                option_1 = row[1].strip()
                option_2 = row[2].strip()
                option_3 = row[3].strip()
                option_4 = row[4].strip()
                try:
                    correct_option = int(row[5])
                except (ValueError, TypeError):
                    continue
                if correct_option not in (1, 2, 3, 4):
                    continue
                Question.objects.create(
                    question_set=self.object,
                    text=question_text,
                    option_1=option_1,
                    option_2=option_2,
                    option_3=option_3,
                    option_4=option_4,
                    correct_option=correct_option,
                )
                created += 1
        return response


class QuestionSetUpdateView(ModeratorRequiredMixin, LogCreateUpdateMixin, UpdateView):
    model = QuestionSet
    form_class = QuestionSetForm
    template_name = 'apps_testing/moderator/question_set_form.html'
    success_url = reverse_lazy('moderator:qset_list')


class QuestionSetDeleteView(ModeratorRequiredMixin, LogDeleteMixin, DeleteView):
    model = QuestionSet
    template_name = 'apps_testing/moderator/confirm_delete.html'
    success_url = reverse_lazy('moderator:qset_list')


# --- Управление Вопросами в Наборе ---
class QuestionListView(ModeratorRequiredMixin, DetailView):
    model = QuestionSet
    template_name = 'apps_testing/moderator/question_list.html'
    context_object_name = 'qset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['questions'] = self.object.questions.all()
        return context

class QuestionCreateView(ModeratorRequiredMixin, LogCreateUpdateMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'apps_testing/moderator/question_form.html'

    def get_context_data(self, **kwargs):
        """Добавляем QuestionSet в контекст для использования в шаблоне."""
        context = super().get_context_data(**kwargs)
        # Получаем объект QuestionSet по pk из URL
        context['qset'] = get_object_or_404(QuestionSet, pk=self.kwargs['qset_pk'])
        return context

    def form_valid(self, form):
        # Привязываем вопрос к правильному набору
        qset = get_object_or_404(QuestionSet, pk=self.kwargs['qset_pk'])
        form.instance.question_set = qset
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('moderator:question_list', kwargs={'pk': self.kwargs['qset_pk']})


# apps_testing/moderator/views.py

class QuestionUpdateView(ModeratorRequiredMixin, LogCreateUpdateMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'apps_testing/moderator/question_form.html'

    def get_context_data(self, **kwargs):
        """Добавляем QuestionSet в контекст для единообразия."""
        context = super().get_context_data(**kwargs)
        # Здесь object уже существует, поэтому мы можем взять qset из него
        context['qset'] = self.object.question_set
        return context

    def get_success_url(self):
        return reverse('moderator:question_list', kwargs={'pk': self.object.question_set.pk})

class QuestionDeleteView(ModeratorRequiredMixin, LogDeleteMixin, DeleteView):
    model = Question
    template_name = 'apps_testing/moderator/confirm_delete.html'

    def get_success_url(self):
        return reverse('moderator:question_list', kwargs={'pk': self.object.question_set.pk})


# --- Управление Тестами ---
class TestListView(ModeratorRequiredMixin, ListView):
    model = Test
    template_name = 'apps_testing/moderator/test_list.html'
    context_object_name = 'tests'


class TestCreateView(ModeratorRequiredMixin, LogCreateUpdateMixin, CreateView):
    model = Test
    form_class = TestForm
    template_name = 'apps_testing/moderator/test_form.html'
    success_url = reverse_lazy('moderator:test_list')


class TestUpdateView(ModeratorRequiredMixin, LogCreateUpdateMixin, UpdateView):
    model = Test
    form_class = TestForm
    template_name = 'apps_testing/moderator/test_form.html'
    success_url = reverse_lazy('moderator:test_list')


class TestDeleteView(ModeratorRequiredMixin, LogDeleteMixin, DeleteView):
    model = Test
    template_name = 'apps_testing/moderator/confirm_delete.html'
    success_url = reverse_lazy('moderator:test_list')


# --- Управление Результатами ---
class ResultListView(ModeratorRequiredMixin, ListView):
    model = TestResult
    template_name = 'apps_testing/moderator/result_list.html'
    context_object_name = 'results'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('session', 'session__test')
        form = ResultsFilterForm(self.request.GET or None)
        if form.is_valid():
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            participant = form.cleaned_data.get('participant')

            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            if participant:
                queryset = queryset.filter(
                    session__last_name__icontains=participant
                ) | queryset.filter(
                    session__first_name__icontains=participant
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ResultsFilterForm(self.request.GET or None)
        return context


class ResultDeleteView(ModeratorRequiredMixin, LogDeleteMixin, DeleteView):
    model = TestResult
    template_name = 'apps_testing/moderator/confirm_delete.html'
    success_url = reverse_lazy('moderator:result_list')


# --- Экспорт в PDF ---
def export_result_pdf(request, result_id):
    result = get_object_or_404(TestResult.objects.select_related('session__test'), pk=result_id)
    incorrect_answers = result.session.answers.filter(is_correct=False).select_related('question')
    incorrect_answers_count = result.answered_questions - result.correct_answers

    html_string = render_to_string('apps_testing/pdf/test_result_report.html', {
        'result': result,
        'incorrect_answers': incorrect_answers,
        'incorrect_answers_count': incorrect_answers_count,
    })

    css = CSS(settings.BASE_DIR / 'static/css/pdf_styles.css')
    pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="result_{result.id}.pdf"'

    logger = logging.getLogger('moderator_actions')
    logger.info(f"Модератор '{request.user.username}' экспортировал в PDF результат {result.id}")

    return response


class QuestionErrorAnalyticsView(ModeratorRequiredMixin, TemplateView):
    template_name = 'apps_testing/moderator/question_error_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = QuestionErrorAnalyticsForm(self.request.GET or None)
        rankings = []
        if form.is_valid():
            start = form.cleaned_data['start_date']
            end = form.cleaned_data['end_date']
            test = form.cleaned_data['test']
            qset = form.cleaned_data['question_set']
            include_all_sets = form.cleaned_data.get('include_all_sets')

            answers = UserAnswer.objects.filter(
                answered_at__date__gte=start,
                answered_at__date__lte=end,
                is_correct=False,
            ).select_related('question', 'session__test', 'question__question_set')

            if test:
                answers = answers.filter(session__test=test)
                if include_all_sets:
                    # Limit to any question set attached to the selected test
                    answers = answers.filter(question__question_set__in=test.question_sets.all())
            if qset and not include_all_sets:
                answers = answers.filter(question__question_set=qset)

            rankings = (
                answers.values('question_id', 'question__text', 'question__question_set__title')
                .annotate(incorrect_count=Count('id'))
                .order_by('-incorrect_count', 'question_id')
            )

        context['form'] = form
        context['rankings'] = rankings
        return context
