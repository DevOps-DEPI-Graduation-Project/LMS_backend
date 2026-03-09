from rest_framework import permissions


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

# ================= INSTRUCTOR OR ADMIN =================
class IsInstructorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['instructor', 'admin']
        )

    def has_object_permission(self, request, view, obj):
        # admin 
        if request.user.role == 'admin':
            return True

        # instructor 
        return obj.user == request.user


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
class CanRateCourse(permissions.BasePermission):
    def has_object_permission(self, request, view, course):
        user = request.user

        if user.role != "student":
            return False

        return course.students.filter(id=user.id).exists()