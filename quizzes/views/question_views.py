from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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


class QuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List questions for a quiz",
        responses={
            200: QuestionSerializer(many=True),
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Questions']
    )
    def get(self, request, quiz_slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        user = request.user

        if user.role == 'admin':
            pass
        elif user.role == 'instructor':
            if quiz.course.instructor.user != user:
                return error_response("You can only view questions for your own quizzes.", status_code=403)
        else:
            if not quiz.course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", status_code=403)

        queryset = Question.objects.filter(quiz=quiz).prefetch_related('choices')
        if user.role in ['admin', 'instructor']:
            serializer = QuestionSerializer(queryset, many=True)
        else:
            serializer = QuestionStudentSerializer(queryset, many=True)
        return success_response("Questions retrieved successfully.", data=serializer.data)


class QuestionCreateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Create a question for a quiz",
        request_body=QuestionCreateSerializer,
        responses={
            201: QuestionSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Questions']
    )
    def post(self, request, quiz_slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only add questions to your own quizzes.", status_code=403)

        serializer = QuestionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(quiz=quiz)
        return success_response("Question added successfully.", data=serializer.data, status_code=201)


class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get question details",
        responses={
            200: QuestionSerializer,
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Questions']
    )
    def get(self, request, quiz_slug, slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=slug, quiz=quiz)
        user = request.user

        if user.role == 'admin':
            pass
        elif user.role == 'instructor':
            if quiz.course.instructor.user != user:
                return error_response("You can only view questions for your own quizzes.", status_code=403)
        else:
            if not quiz.course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", status_code=403)

        if user.role in ['admin', 'instructor']:
            serializer = QuestionSerializer(question)
        else:
            serializer = QuestionStudentSerializer(question)
        return success_response("Question retrieved successfully.", data=serializer.data)


class QuestionUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Update a question",
        request_body=QuestionCreateSerializer,
        responses={
            200: QuestionSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Questions']
    )
    def patch(self, request, quiz_slug, slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=slug, quiz=quiz)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only update questions for your own quizzes.", status_code=403)

        serializer = QuestionCreateSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("Question updated successfully.", data=serializer.data)


class QuestionDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Delete a question",
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
        tags=['Questions']
    )
    def delete(self, request, quiz_slug, slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=slug, quiz=quiz)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only delete questions for your own quizzes.", status_code=403)

        question.delete()
        return success_response("Question deleted successfully.")


