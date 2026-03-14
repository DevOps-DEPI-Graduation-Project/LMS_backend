from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from quizzes.models import Quiz, Question
from quizzes.serializers import (
    QuestionSerializer,
    QuestionStudentSerializer,
    QuestionCreateSerializer,
)
from users.permissions import IsInstructorOrAdmin


def success_response(message, data=None, status_code=200):
    return Response({"success": True, "status": status_code, "message": message, "data": data}, status=status_code)

def error_response(message, data=None, status_code=400):
    return Response({"success": False, "status": status_code, "message": message, "data": data}, status=status_code)


@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=['Questions']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=['Questions']))
class QuestionViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
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
        return success_response("Questions retrieved successfully.", data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("Question retrieved successfully.", data=serializer.data)

    def create(self, request, *args, **kwargs):
        quiz = get_object_or_404(Quiz, slug=self.kwargs.get('quiz_slug'))

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only add questions to your own quizzes.", status_code=403)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz=quiz)
        return success_response("Question added successfully.", data=serializer.data, status_code=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("Question updated successfully.", data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response("Question deleted successfully.")