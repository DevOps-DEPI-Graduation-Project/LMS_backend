from rest_framework import permissions
from cources.models import Enrollment 
from rest_framework.permissions import BasePermission

# ================= STUDENT =================
class IsStudent(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'student'
            and request.user.is_verified
        )

    # student 
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    
    
class IsStudentOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['student', 'admin']
        )

    def has_object_permission(self, request, view, obj):
        # admin 
        if request.user.role == 'admin':
            return True

        # student
        return obj.user == request.user

# ================= INSTRUCTOR OR ADMIN =================
from rest_framework import permissions
from users.models import Instructor

class IsInstructorOrAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['instructor', 'admin']
        )

    def has_object_permission(self, request, view, obj):

        if request.user.role == 'admin':
            return True

        if request.user.role == 'instructor':

            if isinstance(obj, Instructor):
                return obj.user == request.user

            
            if hasattr(obj, 'instructor'):
                return obj.instructor.user == request.user

        return False


# ================= ADMIN ONLY =================
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


# ================= COURSE OWNER OR ADMIN =================
class IsCourseOwnerOrAdmin(permissions.BasePermission):
    """
    Admin يقدر يعدل ويحذف أي كورس
    Instructor يقدر يعدل ويحذف الكورس بتاعه فقط
    """

    def has_object_permission(self, request, view, obj):

        # admin
        if request.user.role == 'admin':
            return True

        # instructor 
        if request.user.role == 'instructor':
            return obj.instructor.user == request.user

        return False
    
    
class IsPackageOwnerOrAdmin(permissions.BasePermission):
    """
    Admin يقدر يعدل ويحذف أي package
    Instructor يقدر يعدل ويحذف package بتاعه فقط
    """

    def has_object_permission(self, request, view, obj):

        # admin
        if request.user.role == 'admin':
            return True

        # instructor 
        if request.user.role == 'instructor':
            return obj.instructor.user == request.user

        return False
    
###### enrolled students only ########

class CanRateCourse(BasePermission):
    message = "Only students can rate courses"

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "student"
        )
     
     ### if student make enroll in course can   
class IsEnrolled(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
         return obj.course.enrollments.filter(student=request.user).exists()
     
     
class IsEnrolledOrAdminOrInstructorOwn(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == 'admin':
            return True

        if user.role == 'instructor':
            return obj.course.instructor == user

        return obj.course.enrollments.filter(student=user).exists()
    
    
from rest_framework import permissions

# ================= VIDEO OWNER OR ADMIN =================
class IsVideoOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        user = request.user

        # Unauthenticated user
        if not user or not user.is_authenticated:
            return False

        # Admin
        if user.role == "admin":
            return True

        # Instructor owns the course of this video
        if user.role == "instructor":
            return obj.course.instructor.user == user

        return False