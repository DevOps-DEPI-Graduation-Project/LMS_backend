from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import Question, Choice
from ..serializers import (
    ChoiceSerializer,
    ChoiceStudentSerializer,
    ChoiceCreateSerializer,
)
from users.permissions import IsInstructorOrAdmin


class ChoiceViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'

    def get_permissions(self):
        """Only instructors and admins can add/edit/delete choices"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Scope choices to the parent question only"""
        return Choice.objects.filter(
            question__slug=self.kwargs.get('question_slug')
        ).select_related('question')

    def get_serializer_class(self):
        user = self.request.user
        if self.action in ['create', 'update', 'partial_update']:
            return ChoiceCreateSerializer
        if user.role in ['admin', 'instructor']:
            return ChoiceSerializer
        return ChoiceStudentSerializer

    def get_serializer_context(self):
        """Pass the parent question into the serializer context for is_correct validation"""
        context = super().get_serializer_context()
        question_slug = self.kwargs.get('question_slug')
        if question_slug:
            context['question'] = get_object_or_404(Question, slug=question_slug)
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "Choices retrieved successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Choice retrieved successfully.",
            "data": serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Add a choice to a question. Serializer handles single-correct-answer validation."""
        question = get_object_or_404(
            Question, slug=self.kwargs.get('question_slug')
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(question=question)

        return Response({
            "status": "success",
            "message": "Choice added successfully.",
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
            "message": "Choice updated successfully.",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "status": "success",
            "message": "Choice deleted successfully.",
            "data": None
        }, status=status.HTTP_200_OK)