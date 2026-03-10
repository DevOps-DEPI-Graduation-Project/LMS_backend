from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import uuid

# =================== Announcement ===================
class Announcement(models.Model):

    TARGET_CHOICES = (
        ('all_users', 'All Users'),
        ('all_students', 'All Students'),
        ('all_instructors', 'All Instructors'),
        ('course_students', 'Course Students'),
        ('specific_users', 'Specific Users'),
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_announcements'
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    content = models.TextField()
    target_type = models.CharField(max_length=30, choices=TARGET_CHOICES)
    course = models.ForeignKey(
        'cources.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements'
    )
    specific_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='specific_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.target_type == 'course_students' and not self.course:
            raise ValidationError("Course must be selected for course_students target.")
        if self.target_type == 'specific_users' and not self.specific_users.exists():
            raise ValidationError("You must select specific users for this target type.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - by {self.sender.email}"


# =================== Announcement Recipient ===================
class AnnouncementRecipient(models.Model):

    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="recipients"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcement_recipients"
    )

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('announcement', 'user')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['announcement']),
        ]
        ordering = ['-created_at']

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    def __str__(self):
        return f"{self.user.email} -> {self.announcement.title}"


# =================== Notification ===================
class Notification(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_read']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"notif-{str(uuid.uuid4())[:12]}"
        super().save(*args, **kwargs)

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def __str__(self):
        return f"To: {self.user.email} - {self.title}"