import uuid
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from cources.models import Course
from users.models import Student

class Video(models.Model):
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True)
    video_upload = models.FileField(upload_to='videos/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    duration = models.DurationField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['course', 'order'], name='unique_video_order_per_course')
        ]
        indexes = [
            models.Index(fields=['course', 'order'], name='idx_course_video_order'),
            models.Index(fields=['course', 'status'], name='idx_course_video_status'),
            models.Index(fields=['course', 'created_at'], name='idx_course_video_created'),
        ]

    # FIX 2: Restored strict duration verification to prevent downstream AttributeError exceptions
    @property
    def is_ready(self):
        return self.status == 'ready' and self.duration is not None

    def clean(self):
        if not self.video_url and not self.video_upload:
            raise ValidationError("Either video URL or video upload must be provided.")
        if self.video_url and self.video_upload:
            raise ValidationError("Only one of video URL or video upload can be provided.")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:50] or "video"
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:12]}"
        
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.course.title}) - [{self.status}]"


class VideoProgress(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='video_progress')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    watched_seconds = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'video'], name='unique_student_video_progress'),
            models.CheckConstraint(check=models.Q(watched_seconds__gte=0.0), name='progress_watched_seconds_non_negative')
        ]

    def _apply_progress_logic(self, current_time):
        """Encapsulates continuous increment updates while listening to dynamic player ticks."""
        if not self.video or self.video.status != 'ready' or not self.video.duration:
            return

        self.watched_seconds = max(self.watched_seconds, float(current_time))
        total_seconds = self.video.duration.total_seconds()
        self.watched_seconds = min(self.watched_seconds, total_seconds)
        self.is_completed = self.watched_seconds >= (total_seconds - 1.0)

    # FIX 1: Explicitly added a dedicated Domain Behavior method to handle Force Complete triggers.
    # It safely isolates the manual completion workflow from continuous save() calculation overrides.
    def mark_completed(self):
        if self.video and self.video.duration:
            self.watched_seconds = self.video.duration.total_seconds()
            
        self.is_completed = True
        super().save(update_fields=['watched_seconds', 'is_completed', 'updated_at'])

    def update_progress(self, current_time):
        if current_time < 0:
            return

        with transaction.atomic():
            locked_progress = VideoProgress.objects.select_for_update().get(pk=self.pk)
            locked_progress._apply_progress_logic(current_time)
            locked_progress.save(update_fields=['watched_seconds', 'is_completed', 'updated_at'])
            
            self.watched_seconds = locked_progress.watched_seconds
            self.is_completed = locked_progress.is_completed

    def save(self, *args, **kwargs):
        if self.watched_seconds < 0:
            raise ValidationError("Watched seconds cannot be negative.")
            
        self._apply_progress_logic(self.watched_seconds)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "✅" if self.is_completed else "⏳"
        return f"{self.student} - {self.video.slug} ({status})" 