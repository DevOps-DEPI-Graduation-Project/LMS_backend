from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Quiz, Question
from ..serializers import (
    QuestionSerializer,
    QuestionStudentSerializer,
    QuestionCreateSerializer,
)
from users.permissions import IsInstructorOrAdmin


class QuestionViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'

    def get_permissions(self):
        """Only instructors and admins can add/edit/delete questions"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Scope questions to the parent quiz only"""
        return Question.objects.filter(
            quiz__slug=self.kwargs.get('quiz_slug')
        ).prefetch_related('choices')

    def get_serializer_class(self):
        user = self.request.user
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateSerializer
        if user.role in ['admin', 'instructor']:
            return QuestionSerializer
        return QuestionStudentSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "Questions retrieved successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Question retrieved successfully.",
            "data": serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Add a question to a quiz. Instructors can only add to their own quizzes."""
        quiz = get_object_or_404(Quiz, slug=self.kwargs.get('quiz_slug'))

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
        instance = self.get_object()
        instance.delete()
        return Response({
            "status": "success",
            "message": "Question deleted successfully.",
            "data": None
        }, status=status.HTTP_200_OK)