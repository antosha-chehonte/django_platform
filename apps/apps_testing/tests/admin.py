from django.contrib import admin

from .models import (
    QuestionSet,
    Question,
    Test,
    TestSession,
    UserAnswer,
    TestResult,
)


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_set", "text", "correct_option", "created_at")
    list_filter = ("question_set",)
    search_fields = ("text",)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "time_limit", "questions_per_set", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    filter_horizontal = ("question_sets",)


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "test", "last_name", "first_name", "is_completed", "start_time", "end_time", "ip_address")
    list_filter = ("is_completed", "test")
    search_fields = ("last_name", "first_name", "middle_name", "session_key", "ip_address")


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "question", "selected_option", "is_correct", "answered_at")
    list_filter = ("is_correct",)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "total_questions",
        "answered_questions",
        "correct_answers",
        "skipped_questions",
        "percentage",
        "created_at",
    )

from django.contrib import admin

# Register your models here.
