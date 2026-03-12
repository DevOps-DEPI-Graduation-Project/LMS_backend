import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from cources.models import Course

PASSING_PERCENTAGE = 0.5  # Configurable passing threshold

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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"quiz-{slugify(self.quiz_name)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.quiz_name


# =================== Question Model ===================
class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    q_name = models.TextField()
    mark = models.PositiveIntegerField(default=1)
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
        """Enforces a single correct answer per question."""
        if self.is_correct:
            existing = Choice.objects.filter(
                question=self.question, is_correct=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("Only one correct choice allowed per question.")

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
            base = f"{self.student.username}-{self.quiz.quiz_name}-at-{self.attempt_number}"
            self.slug = f"{slugify(base)}-{str(uuid.uuid4())[:4]}"
        super().save(*args, **kwargs)

    def calculate_status(self):
        passing_score = self.quiz.total_mark * PASSING_PERCENTAGE
        self.status = "passed" if self.score >= passing_score else "failed"
        self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.student} - {self.quiz.quiz_name} - {self.slug}"


# =================== Student Answer Model ===================
class StudentAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("attempt", "question")

    def clean(self):
        if self.selected_choice.question != self.question:
            raise ValidationError("Selected choice does not belong to this question.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)