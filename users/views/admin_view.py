
#### admin profile view
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from rest_framework import status
from users.models import User
from users.permissions import IsAdmin
from users.serializers import AdminProfileSerializer
from utils.apiResponse import success_response, error_response
from rest_framework.exceptions import NotFound

# ======================= Admin Profile =======================

class AdminProfileView(RetrieveAPIView):
    queryset = User.objects.filter(role="admin")
    serializer_class = AdminProfileSerializer
    permission_classes = [IsAdmin]
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        try:
            admin = self.get_object()
        except NotFound:
            return error_response(
                message="Admin profile not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(admin)

        return success_response(
            message="Admin profile retrieved successfully",
            data=serializer.data
        )