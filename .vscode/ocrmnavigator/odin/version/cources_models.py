from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid
from django.utils import timezone
from users.models import Instructor

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    category = models.CharField(max_length=100, blank=True)

    level = models.CharField(
        max_length=50,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )

    image = models.ImageField(
        upload_to='courses/',
        null=True,
        blank=True
    )
    
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )

    created_at = models.DateTimeField(default=timezone.now)  
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Package(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)

    courses = models.ManyToManyField(
        Course,
        related_name='packages',
        blank=True
    )

    description = models.TextField(blank=True, default='')

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    instructor=models.ForeignKey(
        Instructor,
        on_delete=models.SET_NULL,
        null=True,          
        related_name='packages'
    )

    created_at = models.DateTimeField(default=timezone.now)  

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{slugify(self.title)}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
User = settings.AUTH_USER_MODEL

class CourseRating(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_ratings"
    )
    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    rate = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} → {self.course} ({self.rate})"
    

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course") 

    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"
    
    