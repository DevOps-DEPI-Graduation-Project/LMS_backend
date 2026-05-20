from rest_framework import serializers
from django.db.models import Avg, Count
from rest_framework.permissions import IsAuthenticated , AllowAny
from cources.utils import calculate_course_progress, get_course_status
from users.models import Instructor, InstructorLinks, Student
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
    instructor_name = serializers.SerializerMethodField()
    avg_rating = serializers.FloatField(read_only=True)
    ratings_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    
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
            'is_enrolled'
        ]

    def get_instructor_name(self, obj):
        instructor = getattr(obj, 'instructor', None)
        if not instructor or not getattr(instructor, 'user', None):
            return None

        user = instructor.user
        full_name = ' '.join(filter(None, [user.first_name, user.last_name])).strip()
        return full_name or getattr(user, 'email', None)

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if getattr(request.user, 'role', None) != 'student':
            return None
        if hasattr(obj, 'is_enrolled') and obj.is_enrolled is not None:
            return bool(obj.is_enrolled)
        return Enrollment.objects.filter(student=request.user, course=obj).exists()

# =================== Instructor courses Serializer ==================

class InstructorCourseSerializer(serializers.ModelSerializer):
    ratings_count = serializers.IntegerField(read_only=True)
    students_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'title',
            'slug',
            'created_at',
            'ratings_count',
            'students_count',
        ]

    def get_instructor_name(self, obj):
        instructor = getattr(obj, 'instructor', None)
        if not instructor or not getattr(instructor, 'user', None):
            return None

        user = instructor.user
        full_name = ' '.join(filter(None, [user.first_name, user.last_name])).strip()
        return full_name or getattr(user, 'email', None)


# =================== Course Detail Serializer (with instructor bio & enrollment count) ===================
class CourseDetailSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    
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
            'instructor_name',
            # 'instructor_firstname',
            # 'instructor_lastname',
            'instructor_image',
            'instructor_bio',
            'instructor_links',
            'avg_rating',
            'ratings_count',
            'student_enrollment_count',
            'is_enrolled'
        ]

    def get_instructor_name(self, obj):
        instructor = getattr(obj, 'instructor', None)
        if not instructor or not getattr(instructor, 'user', None):
            return None

        user = instructor.user
        full_name = ' '.join(filter(None, [user.first_name, user.last_name])).strip()
        return full_name or getattr(user, 'email', None)

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if getattr(request.user, 'role', None) != 'student':
            return None
        if hasattr(obj, 'is_enrolled') and obj.is_enrolled is not None:
            return bool(obj.is_enrolled)
        return Enrollment.objects.filter(student=request.user, course=obj).exists()

# ================== course students ====================
class CourseStudentSerializer(serializers.ModelSerializer):
    student_slug = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_email = serializers.SerializerMethodField()
    enrollment_date = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ['student_slug', 'student_name', 'student_email', 'enrollment_date', 'progress']

    def get_student_slug(self, obj):
        return obj.student.slug

    def get_student_name(self, obj):
        first = obj.student.first_name or ""
        last = obj.student.last_name or ""
        return f"{first} {last}".strip() or obj.student.email

    def get_student_email(self, obj):
        return obj.student.email

    def get_enrollment_date(self, obj):
        return obj.enrolled_at.date()

    def get_progress(self, obj):
        return calculate_course_progress(obj.student, obj.course)
# =================== Package Serializers ===================

class GetAllPackagesSerializer(serializers.ModelSerializer):
    
    course_slugs = serializers.SlugRelatedField(
        source="courses",
        many=True,
        read_only=True,
        slug_field="slug"
    )
    instructor_name = serializers.SerializerMethodField()
    courses_count = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'title',
            'instructor_name',
            'slug',
            'description',
            'price',
            'created_at',
            'courses_count',
            'avg_rating',
            'categories',
            'course_slugs',
            'is_enrolled'
        ]

    def get_instructor_name(self, obj):
        instructor = getattr(obj, 'instructor', None)
        if not instructor or not getattr(instructor, 'user', None):
            return None

        user = instructor.user
        full_name = ' '.join(filter(None, [user.first_name, user.last_name])).strip()
        return full_name or getattr(user, 'email', None)

    def get_is_enrolled(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if getattr(request.user, 'role', None) != 'student':
            return None
        if hasattr(obj, 'is_enrolled') and obj.is_enrolled is not None:
            return bool(obj.is_enrolled)

        course_ids = list(obj.courses.values_list('pk', flat=True))
        if not course_ids:
            return None
        enrolled_count = Enrollment.objects.filter(
            student=request.user,
            course__in=course_ids
        ).values('course').distinct().count()
        return enrolled_count == len(course_ids)
    def get_courses_count(self, obj):
        return obj.courses.count()

    def get_categories(self, obj):
        return list(
            obj.courses.values_list('category', flat=True).distinct()
        )

    def get_avg_rating(self, obj):
        avg = obj.courses.aggregate(avg=Avg('ratings__rate'))['avg']
        return round(avg or 0, 2)

# =================== Package Details ===================

class GetPackageDetailsSerializer(serializers.ModelSerializer):
    courses = CourseDetailSerializer(many=True, read_only=True)

    course_slugs = serializers.SlugRelatedField(
        source="courses",
        many=True,
        read_only=True,
        slug_field="slug"
    )
    
    instructor_name = serializers.SerializerMethodField() 
    courses_count = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'title',
            'instructor_name',
            'slug',
            'description',
            'price',
            'created_at',
            'courses_count',
            'avg_rating',    
            'categories',
            'courses',
            'course_slugs'
        ]

    def get_instructor_name(self, obj):
        instructor = getattr(obj, 'instructor', None)
        if not instructor or not getattr(instructor, 'user', None):
            return None

        user = instructor.user
        full_name = ' '.join(filter(None, [user.first_name, user.last_name])).strip()
        return full_name or getattr(user, 'email', None)
    def get_courses_count(self, obj):
        return obj.courses.count()

    def get_categories(self, obj):
        return list(
            obj.courses.values_list('category', flat=True).distinct()
        )

    def get_avg_rating(self, obj):
        avg = obj.courses.aggregate(avg=Avg('ratings__rate'))['avg']
        return round(avg or 0, 2)



# ========================= Create Package =========================

class PackageCreateSerializer(serializers.ModelSerializer):
    courses = serializers.SlugRelatedField(
        queryset=Course.objects.all(),
        many=True,
        slug_field='slug',
        write_only=True
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

        enrollments = (
            Enrollment.objects
            .select_related("course", "course__instructor", "course__instructor__user")
            .filter(student=user)
        )

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
            student = Student.objects.get(user=user)
            course = enrollment.course
            progress = calculate_course_progress(student, course)

            instructor = getattr(course, "instructor", None)
            user_obj = getattr(instructor, "user", None)

            instructor_name = None
            if user_obj:
                instructor_name = (
                    f"{user_obj.first_name} {user_obj.last_name}".strip()
                    or user_obj.username
                )

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "instructor_name": instructor_name,
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
        
class CourseEnrollmentStudentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source="student.user.first_name",
        read_only=True
    )
    student_email = serializers.EmailField(
        source="student.user.email",
        read_only=True
    )
    progress = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student_name",
            "student_email",
            "enrolled_at",
            "progress",
            "status",
        ]

    def get_progress(self, obj):
        return calculate_course_progress(obj.student, obj.course)

    def get_status(self, obj):
        progress = self.get_progress(obj)
        return get_course_status(progress)