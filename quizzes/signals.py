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
    """
    if not created:
        return

    # Import here to avoid circular imports
    from cources.models import Enrollment

    enrolled_user_ids = Enrollment.objects.filter(
        course=instance.course,
    ).values_list('student', flat=True)

    if not enrolled_user_ids.exists():
        return

    Notification.objects.bulk_create([
        Notification(
            user_id=user_id,
            title="New Quiz Added!",
            body=f"A new quiz '{instance.quiz_name}' has been added to {instance.course.title}.",
            notification_type='new_quiz'
        )
        for user_id in enrolled_user_ids
    ])


# =================== Auto-update Quiz total_mark ===================

@receiver(post_save, sender=Question)
def update_total_mark_on_save(sender, instance, **kwargs):
    """Recalculates quiz total_mark after a question is added or updated"""
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
    when two requests try to create an attempt for the same student/quiz simultaneously.
    """
    if not instance.pk:  # Only on creation, not updates
        with transaction.atomic():
            last_attempt = Attempt.objects.select_for_update().filter(
                student=instance.student,
                quiz=instance.quiz
            ).order_by('attempt_number').last()
            instance.attempt_number = last_attempt.attempt_number + 1 if last_attempt else 1


# =================== Helper ===================

def _update_total_mark(quiz):
    """
    Recalculates and persists quiz total_mark from the sum of all question marks.
    Uses queryset .update() instead of .save() to avoid triggering post_save signals.
    """
    total = quiz.questions.aggregate(total=Sum('mark'))['total'] or 0
    Quiz.objects.filter(pk=quiz.pk).update(total_mark=total)