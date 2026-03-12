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


class QuizViewSet(viewsets.ModelViewSet):

    lookup_field = "slug"

    def get_permissions(self):

        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsInstructorOrAdmin()]

        return [IsAuthenticated()]

    def get_queryset(self):

        user = self.request.user

        queryset = Quiz.objects.select_related("course")

        if self.action == "retrieve":
            queryset = queryset.prefetch_related("questions__choices")

        if user.role == "admin":
            return queryset

        if user.role == "instructor":
            return queryset.filter(
                course__instructor__user=user
            )

        return queryset.filter(
            course__enrollment__student=user
        ).distinct()

    def get_serializer_class(self):

        user = self.request.user

        if self.action == "list":
            return QuizListSerializer

        if self.action in ["create", "update", "partial_update"]:
            return QuizCreateSerializer

        if self.action == "retrieve":

            if user.role in ["admin", "instructor"]:
                return QuizDetailInstructorSerializer

            return QuizDetailStudentSerializer

        return QuizListSerializer

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "status": "success",
            "message": "Quizzes retrieved successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):

        instance = self.get_object()

        serializer = self.get_serializer(instance)

        return Response({
            "status": "success",
            "message": "Quiz retrieved successfully.",
            "data": serializer.data
        })

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        if request.user.role == "instructor":

            course = serializer.validated_data.get("course")

            if course.instructor.user != request.user:
                return Response({
                    "status": "error",
                    "message": "You can only add quizzes to your own courses.",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

        serializer.save()

        return Response({
            "status": "success",
            "message": "Quiz created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response({
            "status": "success",
            "message": "Quiz updated successfully.",
            "data": serializer.data
        })

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()

        instance.delete()

        return Response({
            "status": "success",
            "message": "Quiz deleted successfully.",
            "data": None
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="submit",
        permission_classes=[IsAuthenticated]
    )
    def submit(self, request, slug=None):

        quiz = self.get_object()

        if request.user.role != "student":
            return Response({
                "status": "error",
                "message": "Only students can submit attempts.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        # منع إعادة الامتحان

        if Attempt.objects.filter(
                student=request.user,
                quiz=quiz
        ).exists():

            return Response({
                "status": "error",
                "message": "You have already attempted this quiz.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmitAttemptSerializer(
            data=request.data,
            context={
                "request": request,
                "quiz": quiz
            }
        )

        serializer.is_valid(raise_exception=True)

        attempt = serializer.save()

        return Response({
            "status": "success",
            "message": "Attempt submitted successfully.",
            "data": AttemptResultSerializer(attempt).data
        }, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["get"],
        url_path="my-results",
        permission_classes=[IsAuthenticated]
    )
    def my_results(self, request, slug=None):

        if request.user.role != "student":
            return Response({
                "status": "error",
                "message": "Only students can view their results.",
                "data": None
            }, status=status.HTTP_403_FORBIDDEN)

        quiz = self.get_object()

        attempts = Attempt.objects.filter(
            student=request.user,
            quiz=quiz
        ).select_related("quiz").prefetch_related(
            "answers__selected_choice",
            "answers__question"
        )

        return Response({
            "status": "success",
            "message": "Results retrieved successfully.",
            "data": AttemptResultSerializer(attempts, many=True).data
        })