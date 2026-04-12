from django.db import models
from cources.models import Course
from users.models import Student
from django.utils.text import slugify
import uuid
from django.core.exceptions import ValidationError


class Video(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True)
    video_upload = models.FileField(upload_to='videos/', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True)
    duration = models.DurationField(blank=True, null=True)
    order = models.PositiveIntegerField(blank=True, null=True)

    def clean(self):
        if not self.video_url and not self.video_upload:
            raise ValidationError("Either video URL or video upload must be provided.")
        if self.video_url and self.video_upload:
            raise ValidationError("Only one of video URL or video upload can be provided.")

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.order:
            last_video = Video.objects.filter(
                course=self.course
            ).aggregate(models.Max('order'))['order__max']

            self.order = (last_video or 0) + 1

        if not self.slug:
            self.slug = f"{slugify(self.title)}-{str(uuid.uuid4())[:8]}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class VideoProgress(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='video_progress'
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    is_completed = models.BooleanField(default=False)
    watched_seconds = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'video')

    def update_progress(self, current_time):
        if current_time < 0:
            return

        self.watched_seconds = float(current_time)

        if self.video.duration:
            total = self.video.duration.total_seconds()
            self.is_completed = self.watched_seconds >= total - 1
            
        else:
            self.is_completed = False

        self.save(update_fields=[
            'watched_seconds',
            'is_completed',
            'updated_at'
        ])

    def save(self, *args, **kwargs):
        if self.watched_seconds < 0:
            raise ValidationError("Watched seconds cannot be negative.")
        
        if self.video.duration:
            total = self.video.duration.total_seconds()
            if self.watched_seconds >= total - 1:
                self.is_completed = True
            else:
                self.is_completed = False
        
        super().save(*args, **kwargs)

    def __str__(self):
        status = "✅" if self.is_completed else "⏳"
        return f"{self.student} - {self.video.slug} ({status})"