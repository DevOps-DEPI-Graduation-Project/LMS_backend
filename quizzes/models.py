import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from cources.models import Course

# Configurable passing threshold (0.5 = 50%)
PASSING_PERCENTAGE = 0.5

def validate_passing_percentage(value):
    """Validates that passing percentage is between 0 and 1"""
    if not (0 <= value <= 1):
        raise ValidationError('Passing percentage must be between 0 and 1')

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

    def __str__(self):
        return self.quiz_name

    def get_completion_status(self, student=None):
        """Returns completion status and stats for a student or all students"""
        from .models import Attempt
        if student:
            attempts = Attempt.objects.filter(student=student, quiz=self)
            return {
                'total_attempts': attempts.count(),
                'completed': attempts.filter(status='completed').exists(),
                'best_score': attempts.aggregate(models.Max('score'))['score__max'] or 0
            }
        return None

    def get_quiz_stats(self):
        """Returns aggregate statistics for the quiz"""
        from django.db.models import Avg, Count
        from .models import Attempt
        return Attempt.objects.filter(quiz=self).aggregate(
            total_attempts=Count('id'),
            average_score=Avg('score'),
            students_attempted=Count('student', distinct=True)
        )


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
        default="single"
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
        """Enforces correct answer rules based on the question type."""
        if self.is_correct and self.question.question_type == 'single':
            existing = Choice.objects.filter(
                question=self.question, is_correct=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("Only one correct choice allowed for single-choice questions.")

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
    # New Slug Field for Attempt to avoid exposing IDs in URLs
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    attempt_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-attempt_date']
        unique_together = ('student', 'quiz', 'attempt_number')
        indexes = [
            models.Index(fields=['slug']), # Faster retrieval by slug
            models.Index(fields=['student', 'quiz'])
        ]

    def save(self, *args, **kwargs):
        """Auto-generates a readable unique slug for the attempt."""
        if not self.slug:
            base = f"{self.student.email}-{self.quiz.quiz_name}-at-{self.attempt_number}"
            self.slug = f"{slugify(base)}-{str(uuid.uuid4())[:4]}"
        super().save(*args, **kwargs)

    def calculate_status(self):
        """Calculates and updates the attempt status based on passing percentage"""
        passing_score = self.quiz.total_mark * PASSING_PERCENTAGE
        self.status = "passed" if self.score >= passing_score else "failed"
        self.save(update_fields=['status', 'updated_at'])

    def get_score_percentage(self):
        """Returns the score as a percentage"""
        if self.quiz.total_mark == 0:
            return 0
        return round((self.score / self.quiz.total_mark) * 100, 2)

    def is_passing(self):
        """Returns True if the attempt is a passing attempt"""
        return self.status == "passed"

    def __str__(self):
        return f"{self.student} - {self.quiz.quiz_name} - {self.slug}"


# =================== Student Answer Model ===================
class StudentAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("attempt", "question")

    def clean(self):
        if self.selected_choice.question != self.question:
            raise ValidationError("Selected choice does not belong to this question.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def is_correct(self):
        """Returns True if the selected choice is the correct answer"""
        return self.selected_choice.is_correct

    def __str__(self):
        return f"{self.attempt} - {self.question.q_name[:30]}"