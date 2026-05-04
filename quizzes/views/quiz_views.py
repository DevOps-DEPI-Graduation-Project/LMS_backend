from django.db.models import Avg, Max, Count, Q, Prefetch, Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Quiz, Attempt
from cources.models import Course
from ..serializers import (
    QuizListSerializer,
    CourseQuizCreateSerializer,
    QuizDetailInstructorSerializer,
    QuizDetailStudentSerializer,
    SubmitAttemptSerializer,
    AttemptResultSerializer,
)
from users.permissions import IsInstructorOrAdmin, IsStudent
from utils.apiResponse import success_response, error_response
from utils.pagination import QuizzesPagination


class CourseQuizListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all quizzes for the specified course",
        responses={
            200: QuizListSerializer(many=True),
            403: "Forbidden"
        },
        tags=['Quizzes']
    )
    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            if not course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", None, status.HTTP_403_FORBIDDEN)

        quizzes = Quiz.objects.filter(course=course).select_related('course').order_by('-created_at')
        
        if user.role == 'student':
            quizzes = quizzes.annotate(
                attempts_count=Count('attempts', filter=Q(attempts__student=user)),
                best_score_value=Max('attempts__score', filter=Q(attempts__student=user)),
                passed_count=Count('attempts', filter=Q(attempts__student=user, attempts__status='passed'))
            )
        else:
            # For instructors/admins, prefetch questions to avoid N+1 if needed
            quizzes = quizzes.prefetch_related('questions__choices')

        # Pagination
        paginator = QuizzesPagination()
        paginated_queryset = paginator.paginate_queryset(quizzes, request)

        # Calculate statistics
        statistics = {
            "overall_best_score": "0%",
            "completed_quizzes": f"0 / {quizzes.count()}"
        }

        if user.role == 'student':
            total_course_marks = quizzes.aggregate(Sum('total_mark'))['total_mark__sum'] or 0
            
            # Sum of best scores for each quiz attempted by the student in this course
            total_best_score = Attempt.objects.filter(
                student=user, 
                quiz__course=course
            ).values('quiz').annotate(
                max_score=Max('score')
            ).aggregate(total=Sum('max_score'))['total'] or 0

            overall_best_score_pct = 0
            if total_course_marks > 0:
                overall_best_score_pct = round((total_best_score / total_course_marks) * 100)
            
            # Number of unique quizzes passed by the student in this course
            passed_quizzes_count = Attempt.objects.filter(
                student=user, 
                quiz__course=course, 
                status='passed'
            ).values('quiz').distinct().count()
            
            total_quizzes_count = quizzes.count()
            
            statistics = {
                "overall_best_score": f"{overall_best_score_pct}%",
                "completed_quizzes": f"{passed_quizzes_count} / {total_quizzes_count}"
            }

        if paginated_queryset is None:
            serializer = QuizListSerializer(quizzes, many=True, context={'request': request})
            return success_response("Course quizzes retrieved successfully.", {
                "total_quizzes": quizzes.count(),
                "quizzes": serializer.data,
                "statistics": statistics
            })
        
        serializer = QuizListSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(
            serializer.data,
            message="Course quizzes retrieved successfully.",
            extra_data={"statistics": statistics}
        )

    @swagger_auto_schema(
        operation_description="Create a new quiz for the specified course",
        request_body=CourseQuizCreateSerializer,
        responses={
            201: QuizDetailInstructorSerializer,
            400: "Bad Request",
            403: "Forbidden"
        },
        tags=['Quizzes']
    )
    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            return error_response("Only instructors and admins can create quizzes.", None, status.HTTP_403_FORBIDDEN)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only add quizzes to your own course.", None, status.HTTP_403_FORBIDDEN)

        serializer = CourseQuizCreateSerializer(data=request.data, context={'request': request, 'course': course})
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return success_response(
            "Quiz created successfully.",
            QuizDetailInstructorSerializer(quiz).data,
            status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="Update an existing quiz for the specified course",
        request_body=CourseQuizCreateSerializer,
        responses={
            200: QuizDetailInstructorSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def patch(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            return error_response("Only instructors and admins can update quizzes.", None, status.HTTP_403_FORBIDDEN)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only update quizzes for your own course.", None, status.HTTP_403_FORBIDDEN)

        quiz_slug = request.data.get('slug') or request.data.get('quiz_slug')
        if not quiz_slug:
            return error_response("Quiz slug is required for update.", None, status.HTTP_400_BAD_REQUEST)

        quiz = get_object_or_404(Quiz, slug=quiz_slug, course=course)

        serializer = CourseQuizCreateSerializer(
            instance=quiz,
            data=request.data,
            partial=True,
            context={'request': request, 'course': course}
        )
        serializer.is_valid(raise_exception=True)
        updated_quiz = serializer.save()

        return success_response(
            "Quiz updated successfully.",
            QuizDetailInstructorSerializer(updated_quiz).data
        )

    @swagger_auto_schema(
        operation_description="Delete an existing quiz from the specified course",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'slug': openapi.Schema(type=openapi.TYPE_STRING, description='Quiz slug to delete')
            },
            required=['slug']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def delete(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        user = request.user

        if user.role == 'student':
            return error_response("Only instructors and admins can delete quizzes.", None, status.HTTP_403_FORBIDDEN)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only delete quizzes from your own course.", None, status.HTTP_403_FORBIDDEN)

        quiz_slug = request.data.get('slug') or request.data.get('quiz_slug')
        if not quiz_slug:
            return error_response("Quiz slug is required for delete.", None, status.HTTP_400_BAD_REQUEST)

        quiz = get_object_or_404(Quiz, slug=quiz_slug, course=course)
        quiz.delete()
        return success_response("Quiz deleted successfully.", None)


class QuizListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all quizzes",
        responses={
            200: QuizListSerializer(many=True)
        },
        tags=['Quizzes']
    )
    def get(self, request):
        user = request.user
        queryset = Quiz.objects.select_related('course').order_by('-created_at')

        if user.role == 'admin':
            pass
        elif user.role == 'instructor':
            queryset = queryset.filter(course__instructor__user=user)
        else:
            queryset = queryset.filter(course__enrollments__student=user).distinct()

        if user.role == 'student':
            queryset = queryset.annotate(
                attempts_count=Count('attempts', filter=Q(attempts__student=user)),
                best_score_value=Max('attempts__score', filter=Q(attempts__student=user)),
                passed_count=Count('attempts', filter=Q(attempts__student=user, attempts__status='passed'))
            )

        # Pagination
        paginator = QuizzesPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        if paginated_queryset is None:
            serializer = QuizListSerializer(queryset, many=True, context={'request': request})
            return success_response("Quizzes retrieved successfully.", serializer.data)
        
        serializer = QuizListSerializer(paginated_queryset, many=True, context={'request': request})
        return paginator.get_paginated_response(
            serializer.data,
            message="Quizzes retrieved successfully."
        )


class QuizCreateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Create a new quiz",
        request_body=CourseQuizCreateSerializer,
        responses={
            201: CourseQuizCreateSerializer,
            400: "Bad Request",
            403: "Forbidden"
        },
        tags=['Quizzes']
    )
    def post(self, request):
        serializer = CourseQuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.role == 'instructor':
            course = serializer.validated_data.get('course')
            if course.instructor.user != request.user:
                return error_response("You can only add quizzes to your own courses.", None, status.HTTP_403_FORBIDDEN)

        serializer.save()
        return success_response("Quiz created successfully.", serializer.data, status.HTTP_201_CREATED)


class QuizDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get quiz details",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT)  # Can be QuizDetailInstructorSerializer or Student
                }
            ),
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def get(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)
        user = request.user

        if user.role == 'admin':
            pass
        elif user.role == 'instructor':
            if quiz.course.instructor.user != user:
                return error_response("You can only view your own quizzes.", None, status.HTTP_403_FORBIDDEN)
        else:
            if not quiz.course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", None, status.HTTP_403_FORBIDDEN)

        if user.role in ['admin', 'instructor']:
            serializer = QuizDetailInstructorSerializer(quiz, context={'request': request})
        else:
            serializer = QuizDetailStudentSerializer(quiz, context={'request': request})

        return success_response("Quiz retrieved successfully.", serializer.data)


class QuizUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Update a quiz",
        request_body=CourseQuizCreateSerializer,
        responses={
            200: CourseQuizCreateSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def patch(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only update your own quizzes.", None, status.HTTP_403_FORBIDDEN)

        serializer = CourseQuizCreateSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("Quiz updated successfully.", serializer.data)


class QuizDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Delete a quiz",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            ),
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def delete(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only delete your own quizzes.", None, status.HTTP_403_FORBIDDEN)

        quiz.delete()
        return success_response("Quiz deleted successfully.", None)


class QuizSubmitView(APIView):
    permission_classes = [IsStudent]

    @swagger_auto_schema(
        operation_description="Submit a quiz attempt",
        request_body=SubmitAttemptSerializer,
        responses={
            201: AttemptResultSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def post(self, request, slug):
        quiz = get_object_or_404(Quiz, slug=slug)

        if request.user.role != 'student':
            return error_response("Only students can submit attempts.", None, status.HTTP_403_FORBIDDEN)

        serializer = SubmitAttemptSerializer(data=request.data, context={'request': request, 'quiz': quiz})
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()

        return success_response(
            "Attempt submitted successfully.",
            AttemptResultSerializer(attempt).data,
            status.HTTP_201_CREATED
        )


class QuizMyResultsView(APIView):
    permission_classes = [IsStudent]

    @swagger_auto_schema(
        operation_description="Get my quiz results",
        responses={
            200: AttemptResultSerializer(many=True),
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Quizzes']
    )
    def get(self, request, slug):
        if request.user.role != 'student':
            return error_response("Only students can view their results.", None, status.HTTP_403_FORBIDDEN)

        quiz = get_object_or_404(Quiz, slug=slug)
        attempts = Attempt.objects.filter(
            student=request.user, quiz=quiz
        ).select_related('quiz').prefetch_related(
            'answers__selected_choice',
            'answers__question__choices'
        )

        return success_response(
            "Results retrieved successfully.",
            AttemptResultSerializer(attempts, many=True).data
        )


class QuizBestScoreView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        if request.user.role != 'student':
            return error_response("Only students can view their scores.", None, status.HTTP_403_FORBIDDEN)

        quiz = get_object_or_404(Quiz, slug=slug)
        result = Attempt.objects.filter(
            student=request.user, quiz=quiz
        ).aggregate(
            best_score=Max('score'),
            attempts_used=Count('id')
        )

        return success_response("Best score retrieved successfully.", data={
            "quiz_name": quiz.quiz_name,
            "total_mark": quiz.total_mark,
            "best_score": result['best_score'] or 0,
            "attempts_used": result['attempts_used'],
            "attempts_remaining": max(0, quiz.max_attempts - result['attempts_used'])
        })


class QuizMyStatsView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        if request.user.role != 'student':
            return error_response("Only students can view their stats.", None, status.HTTP_403_FORBIDDEN)

        user = request.user
        attempts = Attempt.objects.filter(student=user)

        result = attempts.aggregate(
            average_score=Avg('score'),
            total_attempts=Count('id'),
            passed_count=Count('id', filter=Q(status='passed')),
            failed_count=Count('id', filter=Q(status='failed')),
        )

        total_quizzes = Quiz.objects.filter(
            course__enrollments__student=user
        ).distinct().count()

        return success_response("Stats retrieved successfully.", data={
            "total_quizzes": total_quizzes,
            "total_attempts": result['total_attempts'],
            "passed_exams": result['passed_count'],
            "failed_exams": result['failed_count'],
            "average_score": round(result['average_score'] or 0, 2),
        })
