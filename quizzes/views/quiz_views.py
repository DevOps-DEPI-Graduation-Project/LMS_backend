from django.db.models import Avg, Max, Count, Q, Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Quiz, Attempt
from cources.models import Course
from ..serializers import (
    QuizListSerializer,
    QuizCreateSerializer,
    QuizDetailInstructorSerializer,
    QuizDetailStudentSerializer,
    SubmitAttemptSerializer,
    AttemptResultSerializer,
    CourseQuizCreateSerializer,
)
from users.permissions import IsInstructorOrAdmin


def success_response(message, data=None, status_code=200):
    return Response({"success": True, "status": status_code, "message": message, "data": data}, status=status_code)

def error_response(message, data=None, status_code=400):
    return Response({"success": False, "status": status_code, "message": message, "data": data}, status=status_code)


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
                return error_response("You are not enrolled in this course.", status_code=403)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only view quizzes for your own course.", status_code=403)

        quizzes = Quiz.objects.filter(course=course).prefetch_related('questions__choices')
        serializer = QuizListSerializer(quizzes, many=True, context={'request': request})
        return success_response("Course quizzes retrieved successfully.", data=serializer.data)

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
            return error_response("Only instructors and admins can create quizzes.", status_code=403)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only add quizzes to your own course.", status_code=403)

        serializer = CourseQuizCreateSerializer(data=request.data, context={'request': request, 'course': course})
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        return success_response(
            "Quiz created successfully.",
            data=QuizDetailInstructorSerializer(quiz).data,
            status_code=201
        )

    @swagger_auto_schema(
        operation_description="Update an existing quiz for the specified course",
        request_body=QuizCreateSerializer,
        responses={
            200: QuizCreateSerializer,
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
            return error_response("Only instructors and admins can update quizzes.", status_code=403)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only update quizzes for your own course.", status_code=403)

        quiz_slug = request.data.get('slug') or request.data.get('quiz_slug')
        if not quiz_slug:
            return error_response("Quiz slug is required for update.", status_code=400)

        quiz = get_object_or_404(Quiz, slug=quiz_slug, course=course)

        serializer = QuizCreateSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if request.user.role == 'instructor':
            new_course = serializer.validated_data.get('course')
            if new_course and new_course != course:
                return error_response("Cannot move quiz to another course.", status_code=403)

        serializer.save()
        return success_response("Quiz updated successfully.", data=serializer.data)

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
            return error_response("Only instructors and admins can delete quizzes.", status_code=403)

        if user.role == 'instructor' and course.instructor.user != user:
            return error_response("You can only delete quizzes from your own course.", status_code=403)

        quiz_slug = request.data.get('slug') or request.data.get('quiz_slug')
        if not quiz_slug:
            return error_response("Quiz slug is required for delete.", status_code=400)

        quiz = get_object_or_404(Quiz, slug=quiz_slug, course=course)
        quiz.delete()
        return success_response("Quiz deleted successfully.")


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
        queryset = Quiz.objects.select_related('course')

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

        serializer = QuizListSerializer(queryset, many=True, context={'request': request})
        return success_response("Quizzes retrieved successfully.", data=serializer.data)


class QuizCreateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Create a new quiz",
        request_body=QuizCreateSerializer,
        responses={
            201: QuizCreateSerializer,
            400: "Bad Request",
            403: "Forbidden"
        },
        tags=['Quizzes']
    )
    def post(self, request):
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.role == 'instructor':
            course = serializer.validated_data.get('course')
            if course.instructor.user != request.user:
                return error_response("You can only add quizzes to your own courses.", status_code=403)

        serializer.save()
        return success_response("Quiz created successfully.", data=serializer.data, status_code=201)


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
                return error_response("You can only view your own quizzes.", status_code=403)
        else:
            if not quiz.course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", status_code=403)

        if user.role in ['admin', 'instructor']:
            serializer = QuizDetailInstructorSerializer(quiz, context={'request': request})
        else:
            serializer = QuizDetailStudentSerializer(quiz, context={'request': request})

        return success_response("Quiz retrieved successfully.", data=serializer.data)


class QuizUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Update a quiz",
        request_body=QuizCreateSerializer,
        responses={
            200: QuizCreateSerializer,
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
                return error_response("You can only update your own quizzes.", status_code=403)

        serializer = QuizCreateSerializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("Quiz updated successfully.", data=serializer.data)


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
                return error_response("You can only delete your own quizzes.", status_code=403)

        quiz.delete()
        return success_response("Quiz deleted successfully.")


class QuizSubmitView(APIView):
    permission_classes = [IsAuthenticated]

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
            return error_response("Only students can submit attempts.", status_code=403)

        serializer = SubmitAttemptSerializer(data=request.data, context={'request': request, 'quiz': quiz})
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()

        return success_response(
            "Attempt submitted successfully.",
            data=AttemptResultSerializer(attempt).data,
            status_code=201
        )


class QuizMyResultsView(APIView):
    permission_classes = [IsAuthenticated]

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
            return error_response("Only students can view their results.", status_code=403)

        quiz = get_object_or_404(Quiz, slug=slug)
        attempts = Attempt.objects.filter(
            student=request.user, quiz=quiz
        ).select_related('quiz').prefetch_related(
            'answers__selected_choice',
            'answers__question'
        )

        return success_response(
            "Results retrieved successfully.",
            data=AttemptResultSerializer(attempts, many=True).data
        )


class QuizBestScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        if request.user.role != 'student':
            return error_response("Only students can view their scores.", status_code=403)

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'student':
            return error_response("Only students can view their stats.", status_code=403)

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
