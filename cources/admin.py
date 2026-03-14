    
from django.contrib import admin

from .models import Course, Package,Enrollment,CourseRating

# Register your models here.
admin.site.register(Course)
admin.site.register(Package)
admin.site.register(Enrollment)
admin.site.register(CourseRating)
