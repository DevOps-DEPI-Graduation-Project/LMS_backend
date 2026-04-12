from django.db import models
# videos/models.py
from django.conf import settings
from cources.models import Course
from users.models import Student
from django.utils.text import slugify
import uuid

# Create your models here.
class Video(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    title = models.CharField(max_length=200)
    video_url = models.URLField(blank=True)
    slug = models.SlugField(unique=True, blank=True) 
    order = models.PositiveIntegerField()
     
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title
    
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
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'video')

    def __str__(self):
        status = "✅" if self.is_completed else "⏳"
        return f"{self.student} - {self.video.slug} ({status})"