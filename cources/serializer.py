from rest_framework import serializers
from django.db.models import Avg, Count

from users.models import Instructor
from .models import Course, Package, CourseRating, Enrollment


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
        ]


# =================== Package Serializers ===================
class GetAllPackagesSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    instructor_name = serializers.CharField(
        source='instructor.user.first_name',
        read_only=True
    )
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'title',
            'slug',
            'price',
            'created_at',
            'instructor_name',
            'courses',
            'categories',
        ]

    def get_categories(self, obj):
        return list(
            obj.courses.values_list('category', flat=True).distinct()
        )


class PackageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'title',
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
        fields = ('rate',)

    def validate_rate(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rate must be between 1 and 5"
            )
        return value

    def validate(self, attrs):
        request = self.context.get('request')
        course = self.context.get('course')

        if not request or not course:
            raise serializers.ValidationError(
                "Invalid rating context"
            )

        user = request.user

        # الطالب ميقيّمش نفس الكورس مرتين
        if CourseRating.objects.filter(
            course=course,
            student=user
        ).exists():
            raise serializers.ValidationError(
                {"detail": "You have already rated this course"}
            )

        return attrs
    
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
            raise serializers.ValidationError("You are already enrolled in this course")
        return enrollment