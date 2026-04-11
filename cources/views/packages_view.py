from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView, UpdateAPIView ,DestroyAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from cources.models import Course, Enrollment, Package
from cources.serializer import CourseCreateSerializer, CourseSerializer, GetAllPackagesSerializer, PackageCreateSerializer,GetPackageDetailsSerializer
from users.models import Instructor
from users.permissions import IsInstructorOrAdmin, IsCourseOwnerOrAdmin, IsPackageOwnerOrAdmin
from utils.apiResponse import success_response, error_response
from utils.paginationPackages import paginate_queryset
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, FloatField, Prefetch, Q, Exists, OuterRef, Value, BooleanField, Case, When, F
from django.db.models.functions import Coalesce 
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

#===================get all packages===================
class GetAllPackagesAPIView(ListAPIView):

    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        is_student = user.is_authenticated and getattr(user, "role", None) == "student"

        queryset = Package.objects.prefetch_related(
            Prefetch(
                'courses',
                queryset=Course.objects.prefetch_related('ratings', 'enrollments')
            ),
            "courses__instructor__user"
        ).order_by("-created_at")

        if is_student:
            queryset = queryset.annotate(
                total_courses=Count('courses', distinct=True),
                enrolled_courses_count=Count(
                    'courses__enrollments',
                    filter=Q(courses__enrollments__student=user),
                    distinct=True
                ),
            ).annotate(
                is_enrolled=Case(
                    When(
                        total_courses=0,
                        then=Value(None)
                    ),
                    When(
                        enrolled_courses_count=F('total_courses'),
                        then=Value(True)
                    ),
                    default=Value(False),
                    output_field=BooleanField()
                )
            )
        else:
            queryset = queryset.annotate(
                is_enrolled=Value(None, output_field=BooleanField())
            )

        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category:
            queryset = queryset.filter(
                courses__category__iexact=category
            )

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(instructor__user__first_name__icontains=search)
            )

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        return paginate_queryset(
            queryset=queryset,
            request=request,
            serializer_class=self.get_serializer_class(),
            data_key="packages",
            total_key="total_packages",
            message="Packages retrieved successfully"
        )
#=================== Create Package ===================
class PackageCreateAPIView(CreateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    permission_classes=[IsInstructorOrAdmin]
    # permission_classes=[AllowAny]
    
    def create(self,request, *args, **kwargs):
        serializer=self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid package data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(instructor=request.user.instructor_profile)
        return success_response(
            message="Package created successfully",
            data=serializer.data,
            status_code=status.HTTP_201_CREATED
        )
        
##################### Package Retrieve ######################
class PackageRetrieveAPIView(RetrieveAPIView):
    serializer_class = GetPackageDetailsSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user

        is_student = user.is_authenticated and getattr(user, "role", None) == "student"
        # student_obj = getattr(user, "student", None) if is_student else None

        courses_qs = (
            Course.objects
            .select_related("instructor__user")
            .annotate(
                avg_rating=Coalesce(Avg("ratings__rate"), 0.0),
                ratings_count=Count("ratings", distinct=True),
                students_count=Count("enrollments", distinct=True),
            )
        )

        if is_student:
            courses_qs = courses_qs.annotate(
                is_enrolled=Exists(
                    Enrollment.objects.filter(
                        student=user,   
                        course=OuterRef("pk")
                    )
                )
            )
        else:
            courses_qs = courses_qs.annotate(
                is_enrolled=Value(None, output_field=BooleanField())
            )

        return (
            Package.objects
            .select_related("instructor__user")
            .prefetch_related(
                Prefetch("courses", queryset=courses_qs)
            )
        )
        
    def get_serializer_context(self):
        context=super().get_serializer_context()
        context['request']=self.request
        return context
    
    def retrieve(self, request, *args, **kwargs):
        try:
            package = self.get_queryset().get(slug=kwargs["slug"])
        except Package.DoesNotExist:
            return error_response("Package not found", 404)

        user = request.user
        is_student = user.is_authenticated and getattr(user, "role", None) == "student"

        courses_data = []
        enrolled_courses = 0
        courses = list(package.courses.all())
        total_courses = len(courses)
        if total_courses == 0:
            return success_response(
                message="Package has no courses",
                data={
                    "title": package.title,
                    "slug": package.slug,
                    "description": package.description,
                    "price": package.price,
                    "courses_count": 0,
                    "is_enrolled": None,
                    "courses": []
                }
            )
        courses = list(package.courses.all())
        total_courses = len(courses)

        all_true = True
        any_false = False
        all_null = True

        for course in courses:
            is_enrolled = getattr(course, "is_enrolled", None)

            if is_enrolled is True:
                enrolled_courses += 1
                all_null = False
            elif is_enrolled is False:
                all_true = False
                any_false = True
                all_null = False
            else:  # None
                all_true = False

            instructor_name = None
            if course.instructor and course.instructor.user:
                u = course.instructor.user
                instructor_name = (
                    f"{u.first_name} {u.last_name}".strip() or u.email
                )

            courses_data.append({
                "title": course.title,
                "slug": course.slug,
                "image": request.build_absolute_uri(course.image.url)
                if course.image else None,
                "avg_rating": course.avg_rating,
                "ratings_count": course.ratings_count,
                "students_count": course.students_count,
                "is_enrolled": is_enrolled,
                "instructor_name": instructor_name,
            })
            package_is_enrolled = None

            if total_courses > 0:
                if all_null:
                    package_is_enrolled = None
                elif all_true:
                    package_is_enrolled = True
                else:
                    package_is_enrolled = False

        return success_response(
            message="Package retrieved successfully",
            data={
                "title": package.title,
                "slug": package.slug,
                "description": package.description,
                "price": package.price,
                "courses_count": total_courses,
                "is_enrolled": package_is_enrolled,
                "courses": courses_data,
            }
        )
        
##=================== Update Package ===================

class PackageUpdateAPIView(UpdateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def update(self, request, *args, **kwargs):
        try:
            package=self.get_object()
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer=self.get_serializer(
            package, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message="Invalid package data",
                errors=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()
        return success_response(
            message="Package updated successfully",
            data=serializer.data
        )
        
        
#=================== Delete Package ===================
class PackageDeleteAPIView(DestroyAPIView):
    queryset=Package.objects.all()
    permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def destroy(self, request, *args, **kwargs):
      try:
          package=self.get_object()
      except Package.DoesNotExist:
          return error_response(
              message="Package not found",
              status_code=status.HTTP_404_NOT_FOUND
             )  
      package.delete()
      return success_response(
            message="Package deleted successfully",
            data=None
        )
      
    #   instructor list of packages
    
class InstructorPackagesListAPIView(ListAPIView):
    
    Package.objects.prefetch_related(
        Prefetch('courses', queryset=Course.objects.prefetch_related('ratings', 'enrollments'))
    )
    
    serializer_class = GetAllPackagesSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        instructor_slug = self.kwargs.get('instructor_slug')
        user = self.request.user
        is_student = user.is_authenticated and getattr(user, 'role', None) == 'student'
        try:
            instructor = Instructor.objects.get(user__slug=instructor_slug)
            queryset = Package.objects.filter(instructor=instructor).prefetch_related(
                "courses", "courses__instructor__user"
            ).order_by("-created_at")
            if is_student:
                queryset = queryset.annotate(
                    total_courses=Count('courses', distinct=True),
                    enrolled_courses_count=Count(
                        'courses__enrollments',
                        filter=Q(courses__enrollments__student=user),
                        distinct=True
                    ),
                    is_enrolled=Case(
                        When(
                            total_courses=F('enrolled_courses_count'),
                            total_courses__gt=0,
                            then=Value(True)
                        ),
                        When(
                            total_courses__gt=0,
                            then=Value(False)
                        ),
                        default=Value(None),
                        output_field=BooleanField()
                    )
                )
            else:
                queryset = queryset.annotate(
                    is_enrolled=Value(None, output_field=BooleanField())
                )
            return queryset
        except Instructor.DoesNotExist:
            return Package.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        return paginate_queryset(
            queryset=queryset,
            request=request,
            serializer_class=self.get_serializer_class(),
            data_key="packages",
            total_key="total_packages",
            message="Instructor packages retrieved successfully"
        )
    
#====================add course to package===================
class AddCourseToPackageAPIView(UpdateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    # permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def update(self, request, *args, **kwargs):

        try:
            package = self.get_object()
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        course_slugs = request.data.get('course_slugs', [])
        

        courses = Course.objects.filter(slug__in=course_slugs, instructor=package.instructor)

        if not courses.exists():
            return error_response(
                message="No valid courses found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        package.courses.add(*courses)

        return success_response(
            message="Courses added to package successfully"
        ) 
        


class EnrollPackageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, package_slug):
        user = request.user

        # check role
        if user.role != "student":
            return error_response(
                message="Only students can enroll in packages",
                status_code=status.HTTP_403_FORBIDDEN
            )

        try:
            package = Package.objects.prefetch_related("courses").get(
                slug=package_slug
            )
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        courses = list(package.courses.all())

        if not courses:
            return success_response(
                message="Package has no courses",
                data={
                    "package": {
                        "title": package.title,
                        "slug": package.slug,
                        "is_enrolled": None,
                        "courses": []
                    }
                }
            )

        enrolled_courses = []

        # ensure atomic operation
        with transaction.atomic():
            for course in courses:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=user,
                    course=course
                )
                enrolled_courses.append({
                    "title": course.title,
                    "slug": course.slug,
                    "image": course.image.url if course.image else None,
                    "is_enrolled": True
                })

        return success_response(
            message="Package enrolled successfully",
            data={
                "package": {
                    "title": package.title,
                    "slug": package.slug,
                    "is_enrolled": True,
                    "courses": enrolled_courses
                }
            }
        )
##===================get courses in package===================
class PackageCoursesListAPIView(ListAPIView):
    
    Package.objects.prefetch_related(
        Prefetch('courses', queryset=Course.objects.prefetch_related('ratings', 'enrollments'))
    )
    
    queryset=Package.objects.all()
    serializer_class=CourseSerializer
    permission_classes=[AllowAny]
    def get_queryset(self):
        package_slug=self.kwargs.get('slug')
        user = self.request.user
        is_student = user.is_authenticated and getattr(user, 'role', None) == 'student'

        try:
            package=self.queryset.get(slug=package_slug)
            queryset = package.courses.annotate(
                avg_rating=Avg('ratings__rate'),
                ratings_count=Count('ratings'),
                students_count=Count('enrollments')
            )
            if is_student:
                queryset = queryset.annotate(
                    is_enrolled=Exists(
                        Enrollment.objects.filter(
                            student=user,
                            course=OuterRef('pk')
                        )
                    )
                )
            else:
                queryset = queryset.annotate(
                    is_enrolled=Value(None, output_field=BooleanField())
                )
            return queryset
        except Package.DoesNotExist:
            return Course.objects.none()
        
        
#=================== Remove Course from Package ===================
class RemoveCourseFromPackageAPIView(UpdateAPIView):
    queryset=Package.objects.all()
    serializer_class=PackageCreateSerializer
    permission_classes=[IsAuthenticated, IsPackageOwnerOrAdmin]
    lookup_field = "slug"
    def update(self, request, *args, **kwargs):

        try:
            package = self.get_object()
        except Package.DoesNotExist:
            return error_response(
                message="Package not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        course_slugs = request.data.get('course_slugs', [])

        courses = Course.objects.filter(slug__in=course_slugs, instructor=package.instructor)

        if not courses.exists():
            return error_response(
                message="No valid courses found",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        package.courses.remove(*courses)

        return success_response(
            message="Courses removed from package successfully",
        )
    