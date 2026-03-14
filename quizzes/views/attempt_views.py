from django.utils.decorators import method_decorator
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from quizzes.models import Attempt
from quizzes.serializers import AttemptListSerializer
from users.permissions import IsInstructorOrAdmin


def success_response(message, data=None, status_code=200):
    return Response({"success": True, "status": status_code, "message": message, "data": data}, status=status_code)


@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Student Performance']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Student Performance']))
class AttemptViewSet(
        viewsets.GenericViewSet,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = AttemptListSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        user = self.request.user
        queryset = Attempt.objects.select_related(
            "student",
            "quiz__course",
            "quiz__course__instructor"
        ).prefetch_related("answers")

        if user.role == "instructor":
            queryset = queryset.filter(quiz__course__instructor__user=user)

        quiz_slug = self.request.query_params.get("quiz_slug")
        if quiz_slug:
            queryset = queryset.filter(quiz__slug=quiz_slug)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response("Attempts retrieved successfully.", data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response("Attempt retrieved successfully.", data=serializer.data)