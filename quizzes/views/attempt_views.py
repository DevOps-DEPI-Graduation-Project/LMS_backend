from django.utils.decorators import method_decorator
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from quizzes.models import Attempt, Quiz
from quizzes.serializers import AttemptListSerializer
from users.permissions import IsInstructorOrAdmin
from django.shortcuts import get_object_or_404
from utils.apiResponse import success_response, error_response


class AttemptListView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="List attempts",
        manual_parameters=[
            openapi.Parameter('quiz_slug', openapi.IN_QUERY, description="Filter by quiz slug", type=openapi.TYPE_STRING)
        ],
        responses={
            200: AttemptListSerializer(many=True),
            403: "Forbidden"
        },
        tags=['Student Performance']
    )
    def get(self, request, quiz_slug=None):
        user = request.user
        queryset = Attempt.objects.select_related(
            "student",
            "quiz__course",
            "quiz__course__instructor"
        ).prefetch_related("answers")

        if user.role == "instructor":
            queryset = queryset.filter(quiz__course__instructor__user=user)

        if quiz_slug:
            quiz = get_object_or_404(Quiz, slug=quiz_slug)
            if user.role == "instructor" and quiz.course.instructor.user != user:
                return error_response("You can only view attempts for your own quizzes.", None, status.HTTP_403_FORBIDDEN)
            queryset = queryset.filter(quiz__slug=quiz_slug)

        serializer = AttemptListSerializer(queryset, many=True)
        return success_response("Attempts retrieved successfully.", serializer.data)


class AttemptDetailView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]

    @swagger_auto_schema(
        operation_description="Get attempt details",
        responses={
            200: AttemptListSerializer,
            403: "Forbidden",
            404: "Not Found"
        },
        tags=['Student Performance']
    )
    def get(self, request, slug):
        user = request.user
        instance = get_object_or_404(Attempt, slug=slug)

        if user.role == "instructor":
            if instance.quiz.course.instructor.user != user:
                return error_response("You can only view attempts for your own quizzes.", None, status.HTTP_403_FORBIDDEN)

        serializer = AttemptListSerializer(instance)
        return success_response("Attempt retrieved successfully.", serializer.data)


