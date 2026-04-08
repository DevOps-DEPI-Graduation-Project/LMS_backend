import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from rest_framework.test import APIRequestFactory, force_authenticate
from cources.views.courses_view import CourseListAPIView
from users.models import User

factory = APIRequestFactory()
request = factory.get('/api/courses/all/')
student = User.objects.filter(role='student').first()
print('student', student, student.role)
force_authenticate(request, user=student)
view = CourseListAPIView.as_view()
response = view(request)
print('status', response.status_code)
print(response.data)
