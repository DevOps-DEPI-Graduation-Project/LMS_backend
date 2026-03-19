from django.db.models import Avg, Max, Count, Q, Prefetch
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Quiz, Attempt
from ..serializers import (
    QuizListSerializer,
    QuizCreateSerializer,
    QuizDetailInstructorSerializer,
    QuizDetailStudentSerializer,
    SubmitAttemptSerializer,
    AttemptResultSerializer,
)
from users.permissions import IsInstructorOrAdmin


def success_response(message, data=None, status_code=200):
    return Response({"success": True, "status": status_code, "message": message, "data": data}, status=status_code)

def error_response(message, data=None, status_code=400):
    return Response({"success": False, "status": status_code, "message": message, "data": data}, status=status_code)


class QuizViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = Quiz.objects.select_related('course')

        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('questions__choices')

        if user.role == 'admin':
            return queryset
        if user.role == 'instructor':
            return queryset.filter(course__instructor__user=user)

        # Student queryset
        queryset = queryset.filter(course__enrollments__student=user).distinct()

        # Annotate for list action to avoid N+1 queries in QuizListSerializer
        if self.action == 'list':
            queryset = queryset.annotate(
                attempts_count=Count(
                    'attempts',
                    filter=Q(attempts__student=user)
                ),
                best_score_value=Max(
                    'attempts__score',
                    filter=Q(attempts__student=user)
                ),
                passed_count=Count(
                    'attempts',
                    filter=Q(attempts__student=user, attempts__status='passed')
                )
            )

        return queryset

    def get_serializer_class(self):
        if self.action == 'submit':
            return SubmitAttemptSerializer
        if self.action == 'my_results':
            return AttemptResultSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return QuizCreateSerializer
        if getattr(self, 'swagger_fake_view', False):
            return QuizListSerializer
        user = self.request.user
        if self.action == 'list':
            return QuizListSerializer
        if self.action == 'retrieve':
            if user.role in ['admin', 'instructor']:
                return QuizDetailInstructorSerializer
            return QuizDetailStudentSerializer
        return QuizListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response("Quizzes retrieved successfully.", data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("Quiz retrieved successfully.", data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.role == 'instructor':
            course = serializer.validated_data.get('course')
            if course.instructor.user != request.user:
                return error_response("You can only add quizzes to your own courses.", status_code=403)

        serializer.save()
        return success_response("Quiz created successfully.", data=serializer.data, status_code=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("Quiz updated successfully.", data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response("Quiz deleted successfully.")

    @action(detail=True, methods=['post'], url_path='submit',
            permission_classes=[IsAuthenticated],
            serializer_class=SubmitAttemptSerializer)
    def submit(self, request, slug=None):
        quiz = self.get_object()

        if request.user.role != 'student':
            return error_response("Only students can submit attempts.", status_code=403)

        serializer = SubmitAttemptSerializer(
            data=request.data,
            context={'request': request, 'quiz': quiz}
        )
        serializer.is_valid(raise_exception=True)
        attempt = serializer.save()

        return success_response(
            "Attempt submitted successfully.",
            data=AttemptResultSerializer(attempt).data,
            status_code=201
        )

    @action(detail=True, methods=['get'], url_path='my-results',
            permission_classes=[IsAuthenticated])
    def my_results(self, request, slug=None):
        if request.user.role != 'student':
            return error_response("Only students can view their results.", status_code=403)

        quiz = self.get_object()
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

    @action(detail=True, methods=['get'], url_path='best-score',
            permission_classes=[IsAuthenticated])
    def best_score(self, request, slug=None):
        """
        Returns the student's best score for this quiz.
        GET /quizzes/{slug}/best-score/
        """
        if request.user.role != 'student':
            return error_response("Only students can view their scores.", status_code=403)

        quiz = self.get_object()
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

    @action(detail=False, methods=['get'], url_path='my-stats',
            permission_classes=[IsAuthenticated])
    def my_stats(self, request):
        """
        Returns the student's overall quiz statistics.
        GET /quizzes/my-stats/
        """
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