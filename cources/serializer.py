from rest_framework import serializers
from .models import Course

#=================== Course Serializers ===================
class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'price',
            'category',
            'level',
            'image',
            'is_active',
        ]

#=================== Course Serializer for Listing and Detail Views ===================
class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(source='instructor.user.first_name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'price',
            'category',
            'level',
            'image',
            'created_at',
            'is_active',
            'instructor_name'
        ]
