from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# Corrected Import
from quizzes.models import Attempt
from ..serializers import AttemptListSerializer
from users.permissions import IsInstructorOrAdmin

class AttemptViewSet(
        viewsets.GenericViewSet,
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin):
    """
    Read-only viewset for instructors and admins to monitor student quiz results.
    Uses 'slug' as the primary lookup field for consistent URLs.
    """
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = AttemptListSerializer
    lookup_field = 'slug' 

    def get_queryset(self):
        """
        Optimized queryset using select_related to prevent N+1 queries.
        """
        user = self.request.user
        queryset = Attempt.objects.select_related(
            "student",
            "quiz__course",
            "quiz__course__instructor"
        )

        if user.role == "instructor":
            queryset = queryset.filter(
                quiz__course__instructor__user=user
            )
            
        quiz_slug = self.request.query_params.get("quiz_slug")
        if quiz_slug:
            queryset = queryset.filter(quiz__slug=quiz_slug)

        return queryset

    def list(self, request, *args, **kwargs):
        """List all attempts with a success message wrapper."""
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
        """Retrieve a specific attempt detail using its slug."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Attempt retrieved successfully.",
            "data": serializer.data
        })