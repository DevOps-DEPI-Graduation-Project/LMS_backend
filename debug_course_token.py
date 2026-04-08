import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request
from cources.views.courses_view import CourseListAPIView
from cources.serializer import CourseSerializer
from users.models import User
from cources.models import Course

factory = APIRequestFactory()
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc1NzEzNTUzLCJpYXQiOjE3NzU2MjcxNTMsImp0aSI6ImQzOTk0YjA2NTg2OTQ4YjM4NTVkYmY1NjU1MjZhNWRmIiwidXNlcl9pZCI6IjMifQ.qVVxUfuD3N3SJKqLHgjR55bkZZEJO7MNgGuPi8MLvDg'
req = factory.get('/api/courses/all/', HTTP_AUTHORIZATION=f'Bearer {token}')
request = Request(req)
auth = JWTAuthentication()
user_auth = auth.authenticate(request)
print('authenticate result:', user_auth)
print('request user before auth:', request.user, request.user.is_authenticated)
if user_auth:
    request.user, request.auth = user_auth
    print('request user after auth:', request.user, request.user.is_authenticated)

view = CourseListAPIView()
view.request = request
view.format_kwarg = None
qs = view.get_queryset()
print('queryset example count:', qs.count())
first = qs.first()
print('first has is_enrolled attr:', hasattr(first, 'is_enrolled'))
print('first is_enrolled:', getattr(first, 'is_enrolled', None))
serializer = CourseSerializer(first, context={'request': request})
print('serializer data:', serializer.data)
