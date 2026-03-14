from django.utils.decorators import method_decorator
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

# Using absolute import for stability
from quizzes.models import Attempt
from quizzes.serializers import AttemptListSerializer
from users.permissions import IsInstructorOrAdmin

# Properly applying Swagger tags to organize the documentation
@method_decorator(name='list', decorator=swagger_auto_schema(tags=['Student Performance']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=['Student Performance']))
class AttemptViewSet(
        viewsets.GenericViewSet,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin):
    """
    Read-only viewset for instructors and admins to monitor student quiz results.
    Lookups are performed via 'slug' for consistent and clean URLs.
    """
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = AttemptListSerializer
    lookup_field = 'slug' 

    def get_queryset(self):
        """
        Fetches attempts with optimized queries. 
        Instructors can only see attempts from their own courses.
        """
        user = self.request.user
        queryset = Attempt.objects.select_related(
            "student",
            "quiz__course",
            "quiz__course__instructor"
        ).prefetch_related("answers") # Added prefetch for related answers efficiency

        if user.role == "instructor":
            queryset = queryset.filter(
                quiz__course__instructor__user=user
            )
            
        # Optional filtering by quiz slug through query parameters
        quiz_slug = self.request.query_params.get("quiz_slug")
        if quiz_slug:
            queryset = queryset.filter(quiz__slug=quiz_slug)

        return queryset

    def list(self, request, *args, **kwargs):
        """Returns a wrapped success response with a list of attempts."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "Attempts retrieved successfully.",
            "data": serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Returns a wrapped success response for a single attempt detail."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Attempt retrieved successfully.",
            "data": serializer.data
        })