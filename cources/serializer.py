from rest_framework import serializers

from users.models import Instructor
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
    categories=serializers.SerializerMethodField()
    class Meta:
        model=Package
        fields=[
            'title',
            'slug',
            'price',
            'created_at',
            'instructor_name',
            'courses',
            'categories'
        ]
    def get_categories(self,object):
            return list(object.courses.values_list('category', flat=True).distinct())
        
class PackageCreateSerializer(serializers.ModelSerializer):
    
     class Meta:
        model=Package
        fields=[
            'title',
            'price',
            'courses',
            'created_at'
        ]
     def create(self, validated_data):
            Course_data=validated_data.pop('courses', [])
            package=Package.objects.create(**validated_data)
            package.courses.set(Course_data)
            return package
        
        
class InstructorsProfileSerializer(serializers.ModelSerializer):
    courses=CourseSerializer(many=True, read_only=True)
    package=GetAllPackagesSerializer(many=True, read_only=True)
    first_name=serializers.CharField(source='user.first_name', read_only=True)
    last_name=serializers.CharField(source='user.last_name', read_only=True)
    class Meta:
        model=Instructor
        fields=[
            'first_name',
            'last_name',
            'courses',
            'package',
            'bio',
            'description'
        ]