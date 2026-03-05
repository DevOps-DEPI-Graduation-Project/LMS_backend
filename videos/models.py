from django.db import models
# videos/models.py
from django.conf import settings
from cources.models import Course

# Create your models here.
class Video(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True)
    duration = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField()

    def __str__(self):
        return self.title


class VideoProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='progress'
    )

    watched_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')

    def __str__(self):
        return f"{self.user} - {self.video}"