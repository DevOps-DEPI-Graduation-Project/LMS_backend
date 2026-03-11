from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Announcement, Notification

User = get_user_model()

# =================== Helper Functions ===================

def send_to_course_students(course, title, body, notification_type):
    """
    Retrieves all active students enrolled in a specific course 
    and creates notifications for them using bulk_create for performance.
    """
    if not course:
        return

    # Filter students who are active and currently enrolled in the course
    # students = User.objects.filter(
    #     enrollment__course=course,
    #     enrollment__status='enrolled',
    #     role='student',
    #     is_active=True
    # ).distinct()

    # if not students.exists():
    #     return

    # Efficiently create multiple notifications in one database hit
    # Notification.objects.bulk_create([
    #     Notification(
    #         user=student,
    #         title=title,
    #         body=body,
    #         notification_type=notification_type
    #     )
    #     for student in students
    # ])


# =================== Announcement Signal ===================

@receiver(post_save, sender=Announcement)
def notify_announcement(sender, instance, created, **kwargs):
    """
    Triggered when a new Announcement is created.
    Sends a notification to all students enrolled in the announcement's course.
    """
    if created:
        send_to_course_students(
            course=instance.course,
            title=f"📢 {instance.title}",
            body=instance.content,
            notification_type='announcement'
        )


# =================== Material Signal ===================

@receiver(post_save, sender='materials.Material')
def notify_material(sender, instance, created, **kwargs):
    """
    Triggered when new course material is uploaded.
    Notifies students about the new file.
    """
    if created:
        send_to_course_students(
            course=instance.course,
            title=f"📄 New File: {instance.Material_Name}",
            body=f"A new file has been added to {instance.course.title}",
            notification_type='new_material'
        )


# =================== Pending Signals (Commented Out) ===================

"""
Note: The following signals are commented out because their respective 
apps (Videos, Quizzes, Enrollments) are not yet created.
Uncomment them once the models are available in 'cources' and 'videos' apps.
"""

# @receiver(post_save, sender='videos.Video') # Adjusted sender string
# def notify_video(sender, instance, created, **kwargs):
#     if created:
#         send_to_course_students(
#             course=instance.course,
#             title=f"🎥 New Video: {instance.video_Name}",
#             body=f"A new lecture has been added to {instance.course.title}",
#             notification_type='new_video'
#         )

# @receiver(post_save, sender='cources.Quiz')
# def notify_quiz(sender, instance, created, **kwargs):
#     if created:
#         send_to_course_students(
#             course=instance.course,
#             title=f"📝 New Quiz: {instance.quizName}",
#             body=f"A new quiz is ready in {instance.course.title}. Good luck!",
#             notification_type='new_quiz'
#         )

# @receiver(post_save, sender='cources.Enrollment')
# def notify_enrollment(sender, instance, created, **kwargs):
#     if created and instance.status == 'enrolled':
#         Notification.objects.create(
#             user=instance.student,
#             title="✅ Enrollment Confirmed",
#             body=f"You have been successfully enrolled in {instance.course.title}",
#             notification_type='enrollment_confirmed'
#         )