from rest_framework import serializers
from .models import Course


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
        
        
        
    ### package serializer
# class AllPackageSerializer(serializers.ModelSerializer):
#         class Meta:
#             model = Package
#             fields = [
#                 'title',
#                 'slug',
#                 'courses',
#                 'price',
#             ]

# class PackageCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Package
#         fields = [
#             'title',
#             'slug',
#             'courses',
#             'price',
#         ]  
#         def create(self, validated_data):
#             courses_data = validated_data.pop('courses', [])
#             package = Package.objects.create(**validated_data)
#             package.courses.set(courses_data)
#             return package
    