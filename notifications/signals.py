import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Announcement, Notification


# =================== HELPER ===================
def send_to_course_students(course, title, body, notification_type):
    """Broadcast a notification to all students enrolled in a given course."""
    if not course:
        return

    from cources.models import Enrollment  # Local import to prevent circular import
    enrolled_user_ids = Enrollment.objects.filter(
        course=course
    ).values_list('student', flat=True)

    if not enrolled_user_ids.exists():
        return

    # slug must be generated manually here because bulk_create skips save()
    notifications = [
        Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            slug=f"notif-{uuid.uuid4().hex[:12]}"
        )
        for user_id in enrolled_user_ids
    ]

    with transaction.atomic():
        Notification.objects.bulk_create(notifications)


# =================== SIGNALS ===================

@receiver(post_save, sender=Announcement)
def notify_announcement(sender, instance, created, **kwargs):
    """Notify enrolled students when a new announcement is posted."""
    if created:
        send_to_course_students(
            course=instance.course,
            title=f"New Announcement: {instance.title}",
            body=instance.content,
            notification_type='announcement'
        )


@receiver(post_save, sender='materials.Material')
def notify_material(sender, instance, created, **kwargs):
    """Notify enrolled students when a new material is uploaded."""
    if created:
        send_to_course_students(
            course=instance.course,
            title="New Material Available",
            body=f"New resources have been added to {instance.course.title}.",
            notification_type='new_material'
        )


@receiver(post_save, sender='videos.Video')
def notify_video(sender, instance, created, **kwargs):
    """Notify enrolled students when a new video lecture is uploaded."""
    if created:
        send_to_course_students(
            course=instance.course,
            title="New Video Lecture",
            body=f"A new video has been uploaded to {instance.course.title}.",
            notification_type='new_video'
        )


@receiver(post_save, sender='cources.Enrollment')
def notify_enrollment_confirmation(sender, instance, created, **kwargs):
    """Send a confirmation notification directly to the student upon enrollment."""
    if created:
        Notification.objects.create(
            user=instance.student,
            title="Enrollment Confirmed",
            body=f"You have been successfully enrolled in {instance.course.title}.",
            notification_type='enrollment_confirmed'
        )