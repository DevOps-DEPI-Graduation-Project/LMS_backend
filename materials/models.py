from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import uuid
import os


# Limit uploaded file size to 50MB
def validate_file_size(value):
    limit = 50 * 1024 * 1024
    if value.size > limit:
        raise ValidationError("File too large. Maximum size allowed is 50MB.")


# Material Model
class Material(models.Model):

    # Each material belongs to a specific course
    course = models.ForeignKey(
        "cources.Course",
        on_delete=models.CASCADE,
        related_name="materials"
    )

    Material_Name = models.CharField(max_length=200)

    # Unique slug used for clean URLs
    slug = models.SlugField(
        unique=True,
        blank=True,
        db_index=True
    )

   

    # Store uploaded files inside media/courses/materials
    file = models.FileField(
        upload_to="courses/materials/",
        validators=[validate_file_size],
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Course Material"
        verbose_name_plural = "Course Materials"

    def save(self, *args, **kwargs):
        """
        Automatically generate a unique slug for the material
        """
        if not self.slug:
            self.slug = f"mat-{slugify(self.Material_Name)}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.Material_Name} - {self.course.title}"

    @property
    def file_extension(self):
        """
        Returns file extension (example: .pdf, .mp4)
        """
        if not self.file:
            return None
        _, extension = os.path.splitext(self.file.name)
        return extension.lower()