from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from quizzes.models import Question, Choice, Quiz
from quizzes.serializers import (
    ChoiceSerializer,
    ChoiceStudentSerializer,
    ChoiceCreateSerializer,
)
from users.permissions import IsInstructorOrAdmin
from utils.apiResponse import success_response, error_response
from utils.pagination import QuizzesPagination


class ChoiceListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List choices for a question",
        responses={
            200: ChoiceSerializer(many=True),
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Choices']
    )
    def get(self, request, quiz_slug, question_slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=question_slug, quiz=quiz)
        user = request.user

        if user.role == 'admin':
            pass
        elif user.role == 'instructor':
            if quiz.course.instructor.user != user:
                return error_response("You can only view choices for your own quizzes.", status_code=403)
        else:
            if not quiz.course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", status_code=403)

        queryset = Choice.objects.filter(question=question)
        
        # Pagination
        paginator = QuizzesPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        if paginated_queryset is None:
            if user.role in ['admin', 'instructor']:
                serializer = ChoiceSerializer(queryset, many=True)
            else:
                serializer = ChoiceStudentSerializer(queryset, many=True)
            return success_response("Choices retrieved successfully.", data=serializer.data)
        
        if user.role in ['admin', 'instructor']:
            serializer = ChoiceSerializer(paginated_queryset, many=True)
        else:
            serializer = ChoiceStudentSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(
            serializer.data,
            message="Choices retrieved successfully."
        )


class ChoiceCreateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Create a choice for a question",
        request_body=ChoiceCreateSerializer,
        responses={
            201: ChoiceSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Choices']
    )
    def post(self, request, quiz_slug, question_slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=question_slug, quiz=quiz)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only add choices to your own quizzes.", status_code=403)

        serializer = ChoiceCreateSerializer(data=request.data, context={'question': question})
        serializer.is_valid(raise_exception=True)
        serializer.save(question=question)
        return success_response("Choice added successfully.", serializer.data, status.HTTP_201_CREATED)


class ChoiceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get choice details",
        responses={
            200: ChoiceSerializer,
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Choices']
    )
    def get(self, request, quiz_slug, question_slug, slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=question_slug, quiz=quiz)
        choice = get_object_or_404(Choice, slug=slug, question=question)
        user = request.user

        if user.role == 'admin':
            pass
        elif user.role == 'instructor':
            if quiz.course.instructor.user != user:
                return error_response("You can only view choices for your own quizzes.", None, status.HTTP_403_FORBIDDEN)
        else:
            if not quiz.course.enrollments.filter(student=user).exists():
                return error_response("You are not enrolled in this course.", None, status.HTTP_403_FORBIDDEN)

        if user.role in ['admin', 'instructor']:
            serializer = ChoiceSerializer(choice)
        else:
            serializer = ChoiceStudentSerializer(choice)
        return success_response("Choice retrieved successfully.", serializer.data)


class ChoiceUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Update a choice",
        request_body=ChoiceCreateSerializer,
        responses={
            200: ChoiceSerializer,
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Choices']
    )
    def patch(self, request, quiz_slug, question_slug, slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=question_slug, quiz=quiz)
        choice = get_object_or_404(Choice, slug=slug, question=question)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only update choices for your own quizzes.", None, status.HTTP_403_FORBIDDEN)

        serializer = ChoiceCreateSerializer(choice, data=request.data, partial=True, context={'question': question})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response("Choice updated successfully.", serializer.data)


class ChoiceDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Delete a choice",
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
        tags=['Choices']
    )
    def delete(self, request, quiz_slug, question_slug, slug):
        quiz = get_object_or_404(Quiz, slug=quiz_slug)
        question = get_object_or_404(Question, slug=question_slug, quiz=quiz)
        choice = get_object_or_404(Choice, slug=slug, question=question)

        if request.user.role == 'instructor':
            if quiz.course.instructor.user != request.user:
                return error_response("You can only delete choices for your own quizzes.", None, status.HTTP_403_FORBIDDEN)

        choice.delete()
        return success_response("Choice deleted successfully.", None)


