from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Announcement, Notification

User = get_user_model()

# ==========================================================================
# HELPER FUNCTIONS
# ==========================================================================

def send_to_course_students(course, title, body, notification_type):
    """
    Broadcasts notifications to all students enrolled in a specific course.
    Uses bulk_create for optimized database performance.
    """
    if not course:
        return

    # Import Enrollment inside the function to prevent Circular Import errors
    from cources.models import Enrollment

    # Fetching student IDs directly to minimize memory usage
    enrolled_user_ids = Enrollment.objects.filter(
        course=course,
    ).values_list('student', flat=True)

    if not enrolled_user_ids:
        return

    # Prepare notification list for bulk insertion
    notifications = [
        Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type
        )
        for user_id in enrolled_user_ids
    ]

    # Perform a single database hit to create all notifications
    with transaction.atomic():
        Notification.objects.bulk_create(notifications)


# ==========================================================================
# SIGNAL RECEIVERS
# ==========================================================================

@receiver(post_save, sender=Announcement)
def notify_announcement(sender, instance, created, **kwargs):
    """
    Triggered when a new Announcement is posted.
    Alerts all students enrolled in the corresponding course.
    """
    if created:
        send_to_course_students(
            course=instance.course,
            title=f"📢 Announcement: {instance.title}",
            body=instance.content,
            notification_type='announcement'
        )

# =================== IMPORTANT NOTE ===================
# Video and Material signals are commented out below 
# because the 'Video' and 'Material' models do not exist 
# in the 'cources' or 'materials' apps yet. 
# Uncomment them ONLY after creating those models.
# ======================================================

"""
@receiver(post_save, sender='materials.Material')
def notify_material(sender, instance, created, **kwargs):
    if created:
        send_to_course_students(
            course=instance.course,
            title="📚 New Material Available",
            body=f"New resources added to {instance.course.title}.",
            notification_type='new_material'
        )

@receiver(post_save, sender='cources.Video') # Replace with actual model once created
def notify_video(sender, instance, created, **kwargs):
    if created:
        send_to_course_students(
            course=instance.course,
            title="🎥 New Video Lecture",
            body=f"A new video has been uploaded to {instance.course.title}.",
            notification_type='new_video'
        )
"""

@receiver(post_save, sender='cources.Enrollment')
def notify_enrollment_confirmation(sender, instance, created, **kwargs):
    """
    Sends a direct welcome notification to the student upon successful enrollment.
    """
    if created:
        Notification.objects.create(
            user=instance.student,
            title="✅ Enrollment Successful",
            body=f"You have been successfully enrolled in '{instance.course.title}'.",
            notification_type='enrollment_confirmed'
        )