from rest_framework.permissions import BasePermission


class IsInstructorOrAdmin(BasePermission):
    """
    Custom permission:
    Only instructors or admins can create/update/delete materials.
    Students can only view materials.
    """

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        return request.user.role in ["admin", "instructor"]