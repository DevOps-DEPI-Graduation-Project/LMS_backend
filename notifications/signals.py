from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings
from django.apps import apps

from .models import Announcement

# =================== Users Targeting ===================
def get_target_users(announcement):
    User = apps.get_model('users', 'User')

    if announcement.target_type == 'all_users':
        return User.objects.exclude(id=announcement.sender.id)
    elif announcement.target_type == 'all_students':
        return User.objects.filter(role='student')
    elif announcement.target_type == 'all_instructors':
        return User.objects.filter(role='instructor')
    elif announcement.target_type == 'course_students' and announcement.course:
        return announcement.course.students.all()
    elif announcement.target_type == 'specific_users':
        return announcement.specific_users.all()
    else:
        return User.objects.none()

# =================== Create Recipients & Notifications ===================
def create_announcement_notifications(announcement, users):
    AnnouncementRecipient = apps.get_model('notifications', 'AnnouncementRecipient')
    Notification = apps.get_model('notifications', 'Notification')

    for user in users:
        AnnouncementRecipient.objects.get_or_create(
            announcement=announcement,
            user=user
        )
        Notification.objects.create(
            user=user,
            title=announcement.title,
            body=announcement.content,
            announcement=announcement
        )

# =================== Signal: Post Save ===================
@receiver(post_save, sender=Announcement)
def handle_announcement_post_save(sender, instance, created, **kwargs):
    if not created:
        return

    users = get_target_users(instance)
    create_announcement_notifications(instance, users)

# =================== Signal: M2M Change ===================
@receiver(m2m_changed, sender=Announcement.specific_users.through)
def handle_specific_users_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        users = instance.specific_users.filter(pk__in=pk_set)
        create_announcement_notifications(instance, users)