from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema, no_body

from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from users.permissions import IsStudent
from utils.apiResponse import success_response, error_response
from utils.pagination import NotificationsPagination


class NotificationListView(APIView):
    permission_classes = [IsStudent]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request):
        queryset = self.get_queryset()
        
        # Pagination
        paginator = NotificationsPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        if paginated_queryset is None:
            serializer = NotificationSerializer(queryset, many=True)
            return success_response(
                "Notifications retrieved successfully.",
                {
                    "unread_count": queryset.filter(is_read=False).count(),
                    "notifications": serializer.data
                }
            )
        
        serializer = NotificationSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(
            serializer.data,
            message="Notifications retrieved successfully.",
            extra_data={"unread_count": queryset.filter(is_read=False).count()}
        )


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        instance = get_object_or_404(Notification, user=request.user, slug=slug)
        serializer = NotificationSerializer(instance)
        return success_response("Notification retrieved successfully.", serializer.data)


class NotificationMarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=no_body, operation_description="Mark a specific notification as read. No request body required.")
    def post(self, request, slug):
        notification = get_object_or_404(Notification, user=request.user, slug=slug)
        notification.mark_as_read()
        return success_response("Notification marked as read.", None)


class NotificationMarkAllAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=no_body, operation_description="Mark all unread notifications as read at once. No request body required.")
    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return success_response(f"{updated} notification(s) marked as read.", None)
