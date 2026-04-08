import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from users.models import User
from cources.models import Course, Enrollment
from django.db.models import Avg, Count, Exists, OuterRef

student = User.objects.filter(role='student').first()
print('student:', student and student.email, 'role:', student and student.role)
qs = Course.objects.annotate(
    avg_rating=Avg('ratings__rate'),
    ratings_count=Count('ratings'),
    students_count=Count('enrollments', distinct=True)
).order_by('-created_at')
if student:
    qs = qs.annotate(
        is_enrolled=Exists(
            Enrollment.objects.filter(student=student, course=OuterRef('pk'))
        )
    )
print('course exists:', bool(qs.exists()))
first = qs.first()
print('has is_enrolled:', hasattr(first, 'is_enrolled'))
print('value:', getattr(first, 'is_enrolled', None))
for course in qs[:5]:
    print(course.slug, getattr(course, 'is_enrolled', None))
