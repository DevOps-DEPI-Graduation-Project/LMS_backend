from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

# Using absolute imports for stability across directories
from quizzes.models import Quiz, Question
from quizzes.serializers import (
    QuestionSerializer,
    QuestionStudentSerializer,
    QuestionCreateSerializer,
)
from users.permissions import IsInstructorOrAdmin

# Properly grouping all actions under 'Quiz Content'
@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Questions']))

class QuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Quiz Questions.
    Grouped under 'Quiz Content' for consistent API documentation.
    """
    lookup_field = 'slug'

    def get_permissions(self):
        """Only instructors and admins can add/edit/delete questions"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Scope questions to the parent quiz only using nested quiz_slug"""
        return Question.objects.filter(
            quiz__slug=self.kwargs.get('quiz_slug')
        ).prefetch_related('choices')

    def get_serializer_class(self):
        """Returns specialized serializers based on user role and action"""
        user = self.request.user
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateSerializer
        if user.role in ['admin', 'instructor']:
            return QuestionSerializer
        return QuestionStudentSerializer

    def list(self, request, *args, **kwargs):
        """Returns all questions for a specific quiz with their choices."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "Questions retrieved successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Returns details for a single question."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Question retrieved successfully.",
            "data": serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Creates a new question linked to a quiz.
        Instructors can only add questions to quizzes in their own courses.
        """
        quiz = get_object_or_404(Quiz, slug=self.kwargs.get('quiz_slug'))

        # Permission check: Ensure instructor owns the course this quiz belongs to
        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return Response({
                    "status": "error",
                    "message": "You can only add questions to your own quizzes.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz=quiz)

        return Response({
            "status": "success",
            "message": "Question added successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Full or partial update for a specific question."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Question updated successfully.",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """Removes a question from the quiz."""
        instance = self.get_object()
        instance.delete()
        return Response({
            "status": "success",
            "message": "Question deleted successfully.",
            "data": None
        }, status=status.HTTP_200_OK)