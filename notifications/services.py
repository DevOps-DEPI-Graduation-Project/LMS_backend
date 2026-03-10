from django.apps import apps


# =================== Users Targeting ===================
def get_target_users(announcement):
    """
    ترجع QuerySet بالمستخدمين اللي المفروض يوصلهم الـ Announcement
    حسب target_type
    """
    User = apps.get_model('users', 'User')

    if announcement.target_type == 'all_users':
        return User.objects.filter(is_active=True).exclude(id=announcement.sender.id)

    elif announcement.target_type == 'all_students':
        return User.objects.filter(role='student', is_active=True)

    elif announcement.target_type == 'all_instructors':
        return User.objects.filter(role='instructor', is_active=True)

    elif announcement.target_type == 'course_students' and announcement.course:
        return User.objects.filter(
            enrollment__course=announcement.course,
            enrollment__status='enrolled',
            is_active=True
        )

    elif announcement.target_type == 'specific_users':
        return announcement.specific_users.filter(is_active=True)

    return User.objects.none()


# =================== Create Recipients & Notifications ===================
def create_announcement_notifications(announcement, users):
    """
    تنشئ AnnouncementRecipient و Notification لكل user
    بتستخدم bulk_create عشان تتجنب N queries
    """
    AnnouncementRecipient = apps.get_model('notifications', 'AnnouncementRecipient')
    Notification = apps.get_model('notifications', 'Notification')

    # فلتر الـ users اللي عندهم recipient بالفعل عشان نتجنب duplicates
    existing_recipient_ids = AnnouncementRecipient.objects.filter(
        announcement=announcement
    ).values_list('user_id', flat=True)

    new_users = [u for u in users if u.id not in existing_recipient_ids]

    if not new_users:
        return

    # Bulk create recipients
    AnnouncementRecipient.objects.bulk_create([
        AnnouncementRecipient(
            announcement=announcement,
            user=user
        )
        for user in new_users
    ], ignore_conflicts=True)

    # Bulk create notifications
    Notification.objects.bulk_create([
        Notification(
            user=user,
            title=announcement.title,
            body=announcement.content,
            announcement=announcement
        )
        for user in new_users
    ])


# =================== Firebase Push Notification (Placeholder) ===================
def send_push_notification(notification):
    """
    Placeholder لإرسال notification عبر Firebase لاحقًا.

    from firebase_admin import messaging
    message = messaging.Message(
        notification=messaging.Notification(
            title=notification.title,
            body=notification.body,
        ),
        token=notification.user.device_token,
    )
    response = messaging.send(message)
    notification.is_sent = True
    notification.save(update_fields=['is_sent'])
    """
    pass