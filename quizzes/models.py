import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from cources.models import Course

# Configurable passing threshold is now per-quiz
# PASSING_PERCENTAGE removed from here and moved into Quiz model


# =================== Quiz Model ===================
class Quiz(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="quizzes"
    )
    quiz_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    total_mark = models.IntegerField(
        default=0,
        help_text="Auto-updated when questions are added or removed"
    )
    passing_percentage = models.PositiveIntegerField(
        default=50,
        help_text="Percentage of total mark required to pass (e.g., 50 for 50%)"
    )
    max_attempts = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of attempts allowed per student"
    )
    slug = models.SlugField(unique=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"quiz-{slugify(self.quiz_name)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def get_quiz_stats(self):
        """Returns aggregate statistics for the quiz"""
        from django.db.models import Avg, Count
        return Attempt.objects.filter(quiz=self).aggregate(
            total_attempts=Count('id'),
            average_score=Avg('score'),
            students_attempted=Count('student', distinct=True)
        )

    def __str__(self):
        return self.quiz_name


# =================== Question Model ===================
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ("single", "Single Choice"),
        ("multiple", "Multiple Choice"),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    q_name = models.TextField()
    mark = models.PositiveIntegerField(default=1)
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default="single",
        help_text="single = exactly one correct answer. multiple = one or more correct answers."
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"q-{str(uuid.uuid4())[:12]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.q_name[:50]


# =================== Choice Model ===================
class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices"
    )
    text_choice = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    def clean(self):
        """
        Enforces correct-answer rules based on question type:
        - single   → only one correct choice allowed at any time.
        - multiple → no restriction, but at least one correct is enforced at serializer level.
        """
        if self.is_correct and self.question.question_type == 'single':
            existing = Choice.objects.filter(
                question=self.question, is_correct=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Only one correct choice is allowed for single-choice questions."
                )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"c-{str(uuid.uuid4())[:12]}"
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.text_choice


# =================== Attempt Model ===================
class Attempt(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("passed", "Passed"),
        ("failed", "Failed"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts"
    )
    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Sequence of the attempt for the specific user/quiz"
    )
    score = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    attempt_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-attempt_date']
        unique_together = ('student', 'quiz', 'attempt_number')
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['student', 'quiz'])
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.student.email}-{self.quiz.quiz_name}-at-{self.attempt_number}"
            self.slug = f"{slugify(base)}-{str(uuid.uuid4())[:4]}"
        super().save(*args, **kwargs)

    def calculate_status(self):
        passing_score = self.quiz.total_mark * (self.quiz.passing_percentage / 100)
        self.status = "passed" if self.score >= passing_score else "failed"
        self.save(update_fields=['status', 'updated_at'])

    def get_score_percentage(self):
        if self.quiz.total_mark == 0:
            return 0
        return round((self.score / self.quiz.total_mark) * 100, 2)

    def is_passing(self):
        return self.status == "passed"

    def __str__(self):
        return f"{self.student} - {self.quiz.quiz_name} - {self.slug}"


# =================== Student Answer Model ===================
class StudentAnswer(models.Model):
    """
    Stores each choice selected by a student for a given question in an attempt.

    unique_together = (attempt, question, selected_choice) allows multiple rows
    per question — required for multiple-choice questions where the student can
    select more than one choice.
    """
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="student_answers")
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Allow multiple choices per question (for multiple-choice support)
        # Prevents the same choice from being submitted twice in the same attempt
        unique_together = ("attempt", "question", "selected_choice")

    def clean(self):
        if self.selected_choice.question != self.question:
            raise ValidationError("Selected choice does not belong to this question.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attempt} - {self.question.q_name[:30]}"