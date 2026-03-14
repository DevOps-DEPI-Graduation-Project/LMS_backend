from rest_framework import serializers
from django.db.models import Avg, Count
from rest_framework.permissions import IsAuthenticated , AllowAny
from cources.utils import calculate_course_progress, get_course_status
from users.models import Instructor, InstructorLinks
from utils.apiResponse import error_response, success_response
from .models import Course, Package, CourseRating, Enrollment
from rest_framework import status
from rest_framework.views import APIView
from users.serializers import InstructorLinksSerializer
# =================== Course Create Serializer ===================
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


# =================== Course Serializer (List / Detail) ===================
class CourseSerializer(serializers.ModelSerializer):
    instructor_name = serializers.CharField(
        source='instructor.user.first_name',
        read_only=True
    )

    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)

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
            'instructor_name',
            'avg_rating',
            'ratings_count',
            'students_count',
        ]


# =================== Instructor Links Serializer ==================


# =================== Course Detail Serializer (with instructor bio & enrollment count) ===================
class CourseDetailSerializer(serializers.ModelSerializer):
    instructor_firstname = serializers.CharField(
        source='instructor.user.first_name',
        read_only=True
    )
    
    instructor_lastname = serializers.CharField(
        source='instructor.user.last_name',
        read_only=True
    )
    
    instructor_image = serializers.ImageField(
        source='instructor.user.image',
        read_only=True
    )

    instructor_bio = serializers.CharField(
        source='instructor.bio',
        read_only=True
    )

    instructor_links = InstructorLinksSerializer(
        source="instructor.links",
        many=True,
        read_only=True
    )

    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    student_enrollment_count = serializers.IntegerField(read_only=True)

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
            'instructor_firstname',
            'instructor_lastname',
            'instructor_image',
            'instructor_bio',
            'instructor_links',
            'avg_rating',
            'ratings_count',
            'student_enrollment_count',
        ]


# =================== Package Serializers ===================
class GetAllPackagesSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(
        source='instructor.user.first_name',
        read_only=True
    )
    categories = serializers.SerializerMethodField()
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'title',
            'slug',
            'description',
            'price',
            'created_at',
            'instructor_name',
            'courses',
            'courses_count',
            'categories',
        ]

    def get_categories(self, obj):
        return list(
            obj.courses.values_list('category', flat=True).distinct()
        )

    def get_courses_count(self, obj):
        return obj.courses.count()


class PackageCreateSerializer(serializers.ModelSerializer):
    courses = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        many=True,
        slug_field='slug'
    )

    class Meta:
        model = Package
        fields = [
            'title',
            'description',
            'price',
            'courses',
            'created_at',
        ]

    def create(self, validated_data):
        courses = validated_data.pop('courses', [])
        package = Package.objects.create(**validated_data)
        package.courses.set(courses)
        return package


# =================== Instructor Profile Serializer ===================
class InstructorsProfileSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    package = GetAllPackagesSerializer(many=True, read_only=True)
    first_name = serializers.CharField(
        source='user.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='user.last_name',
        read_only=True
    )

    class Meta:
        model = Instructor
        fields = [
            'first_name',
            'last_name',
            'courses',
            'package',
            'bio',
            'description',
        ]


# =================== Course Rating Serializer ===================
class CourseRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseRating
        fields = ("rate",)

    def validate_rate(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Rate must be between 1 and 5"
            )
        return value
    
# =================== Enrollment Serializer ===================
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id", "student", "course", "enrolled_at"]
        read_only_fields = ["id", "enrolled_at", "student"]

    def create(self, validated_data):
        user = self.context["request"].user
        course = validated_data["course"]
        enrollment, created = Enrollment.objects.get_or_create(student=user, course=course)
        if not created:
            raise serializers.ValidationError({
                "You are already enrolled in this course"
            })
        return enrollment
    
    
class MyEnrollmentCourseSerializer(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "student":
            return error_response(
                message="Only students can view enrollments",
                status_code=status.HTTP_403_FORBIDDEN
            )

        enrollments = Enrollment.objects.select_related("course").filter(student=user)

        if not enrollments.exists():
            return success_response(
                message="You have no enrollments yet",
                data={
                    "total_courses": 0,
                    "courses": []
                }
            )

        courses_data = []

        for enrollment in enrollments:
            course = enrollment.course
            progress = calculate_course_progress(user, course)

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "image": course.image.url if course.image else None,
                "progress": progress,
                "status": get_course_status(progress),
                "enrolled_at": enrollment.enrolled_at.isoformat(),
            })

        return success_response(
            message="My enrollments retrieved successfully",
            data={
                "total_courses": len(courses_data),
                "courses": courses_data
            }
        )