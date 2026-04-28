from django.contrib import admin
from .models import Quiz, Question, Choice, Attempt, StudentAnswer


# ================= Choice Inline =================
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


# ================= Question Inline =================
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True


# ================= StudentAnswer Inline =================
class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ("question", "selected_choice")
    can_delete = False


# ================= Quiz Admin =================
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):

    list_display = (
        "quiz_name",
        "course",
        "total_mark",
        "passing_percentage",
        "max_attempts"
    )

    search_fields = (
        "quiz_name",
        "course__title"
    )

    list_filter = (
        "course",
    )

    readonly_fields = (
        "slug",
        "total_mark"
    )

    prepopulated_fields = {}

    inlines = [QuestionInline]


# ================= Question Admin =================
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):

    list_display = (
        "q_name",
        "quiz",
        "mark"
    )

    search_fields = (
        "q_name",
        "quiz__quiz_name"
    )

    list_filter = (
        "quiz",
    )

    readonly_fields = (
        "slug",
    )

    inlines = [ChoiceInline]


# ================= Choice Admin =================
@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):

    list_display = (
        "text_choice",
        "question",
        "is_correct"
    )

    list_filter = (
        "is_correct",
        "question"
    )

    search_fields = (
        "text_choice",
        "question__q_name"
    )

    readonly_fields = (
        "slug",
    )


# ================= Attempt Admin =================
@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "quiz",
        "attempt_number",
        "score",
        "status",
        "attempt_date"
    )

    list_filter = (
        "status",
        "quiz",
        "attempt_date"
    )

    search_fields = (
        "student__email",
        "quiz__quiz_name"
    )

    readonly_fields = (
        "attempt_number",
        "attempt_date"
    )

    inlines = [StudentAnswerInline]


# ================= StudentAnswer Admin =================
@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):

    list_display = (
        "attempt",
        "question",
        "selected_choice"
    )

    search_fields = (
        "question__q_name",
    )

    list_filter = (
        "question",
    )