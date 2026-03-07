from rest_framework import serializers
from .models import Course, Package

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
class GetAllPackagesSerializer(serializers.ModelSerializer):
    courses=CourseSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(source='instructor.user.first_name', read_only=True)
    class Meta:
        model=Package
        fields=[
            'title',
            'slug',
            'price',
            'image',
            'created_at',
            'instructor_name',
            'courses'
        ]
        
class PackageCreateSerializer(serializers.ModelSerializer):
    
     class Meta:
        model=Package
        fields=[
            'title',
            'price',
            'image',
            'courses',
            'created_at'
        ]
     def create(self, validated_data):
            Course_data=validated_data.pop('courses', [])
            package=Package.objects.create(**validated_data)
            package.courses.set(Course_data)
            return package