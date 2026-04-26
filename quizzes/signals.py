import uuid
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.db import transaction

from .models import Quiz, Question, Attempt
from notifications.models import Notification


# =================== Notify students when a new quiz is created ===================

@receiver(post_save, sender=Quiz)
def notify_students_new_quiz(sender, instance, created, **kwargs):
    """
    Sends a notification to all enrolled students when a new quiz is added to a course.
    Uses bulk_create for performance — avoids N+1 insert queries.
    Slugs are generated manually because bulk_create skips save().

    NOTE: This signal fires only when Quiz.save() is called directly.
    total_mark updates use Quiz.objects.filter().update() which bypasses
    this signal intentionally — avoiding unwanted re-notifications.
    """
    if not created:
        return

    from cources.models import Enrollment  # Local import to prevent circular import

    enrolled_user_ids = list(
        Enrollment.objects.filter(
            course=instance.course
        ).values_list('student', flat=True)
    )

    if not enrolled_user_ids:
        return

    Notification.objects.bulk_create([
        Notification(
            user_id=user_id,
            title="New Quiz Available",
            body=f"A new quiz '{instance.quiz_name}' has been added to {instance.course.title}.",
            notification_type='new_quiz',
            slug=f"notif-{uuid.uuid4().hex[:12]}"
        )
        for user_id in enrolled_user_ids
    ])


# =================== Auto-update Quiz total_mark ===================

@receiver(post_save, sender=Question)
def update_total_mark_on_save(sender, instance, **kwargs):
    """
    Recalculates quiz total_mark after a standalone question is added or updated.

    NOTE: During bulk nested create/update in CourseQuizCreateSerializer,
    total_mark is calculated manually and set via Quiz.objects.filter().update()
    to avoid triggering this signal on every question in the loop.
    This signal handles only the standalone /questions/ endpoint case.
    """
    _update_total_mark(instance.quiz)


@receiver(post_delete, sender=Question)
def update_total_mark_on_delete(sender, instance, **kwargs):
    """Recalculates quiz total_mark after a question is removed"""
    _update_total_mark(instance.quiz)


# =================== Auto-set attempt_number ===================

@receiver(pre_save, sender=Attempt)
def set_attempt_number(sender, instance, **kwargs):
    """
    Automatically assigns an incremented attempt_number before each new attempt is saved.

    Uses select_for_update() inside an atomic block to prevent race conditions
    when two concurrent requests try to create an attempt for the same student/quiz.

    The serializer must NOT manually set attempt_number — this signal is the
    single source of truth for attempt sequencing.
    """
    if instance.pk:
        # Already exists — this is an update, not a new attempt. Skip.
        return

    with transaction.atomic():
        last_attempt = (
            Attempt.objects
            .select_for_update()
            .filter(student=instance.student, quiz=instance.quiz)
            .order_by('attempt_number')
            .last()
        )
        instance.attempt_number = (last_attempt.attempt_number + 1) if last_attempt else 1


# =================== Helper ===================

def _update_total_mark(quiz):
    """
    Recalculates and persists quiz total_mark from the sum of all question marks.
    Uses queryset .update() instead of .save() to avoid triggering post_save signals
    and causing an infinite loop.
    """
    total = quiz.questions.aggregate(total=Sum('mark'))['total'] or 0
    Quiz.objects.filter(pk=quiz.pk).update(total_mark=total)