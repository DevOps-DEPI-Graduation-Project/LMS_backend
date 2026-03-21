from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid


# =================== Announcement ===================
class Announcement(models.Model):
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    title = models.CharField(max_length=120)
    content = models.TextField()
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    course = models.ForeignKey(
        'cources.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"ann-{slugify(self.title)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


# =================== Notification ===================
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('announcement', 'Announcement'),
        ('new_material', 'New Material'),
        ('new_video', 'New Video'),
        ('new_quiz', 'New Quiz'),
        ('enrollment_confirmed', 'Enrollment Confirmed'),
        ('quiz_result', 'Quiz Result'),
        ('streak', 'Streak Achieved'),  # اتضاف لما الطالب يخلص كويز
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    title = models.CharField(max_length=120)
    body = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='announcement'
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"notif-{str(uuid.uuid4())[:12]}"
        super().save(*args, **kwargs)

    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def __str__(self):
        return f"{self.user} - {self.title}"