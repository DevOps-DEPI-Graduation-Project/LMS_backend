from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math


class DynamicPagination(PageNumberPagination):
    """
    Dynamic pagination class that can be configured per-view.
    
    Usage in views:
        class MyListView(APIView):
            def get_pagination(self):
                pagination = DynamicPagination()
                pagination.page_size = 20  # Custom page size
                pagination.resource_name = 'products'  # Plural name for response
                return pagination
            
            def get(self, request):
                queryset = self.get_queryset()
                pagination = self.get_pagination()
                paginated = pagination.paginate_queryset(queryset, request)
                serializer = MySerializer(paginated, many=True)
                return pagination.get_paginated_response(
                    serializer.data,
                    message="Products retrieved successfully",
                    extra_data={"filters": {...}}
                )
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    resource_name = 'items'  # Default resource name, override in views
    total_label = 'total_items'  # Default total label, override in views

    def get_paginated_response(
        self,
        data,
        total=None,
        message="Success",
        extra_data=None
    ):
        """
        Returns a paginated response with dynamic resource naming.
        
        Args:
            data: Serialized data to paginate
            total: Optional custom total count
            message: Response message
            extra_data: Optional extra data to include (dict)
        """
        page_size = self.get_page_size(self.request) or self.page_size
        total_items = total if total is not None else self.page.paginator.count
        total_pages = math.ceil(total_items / page_size)

        # Build the response data dynamically
        base_data = {
            "total_pages": total_pages,
            "current_page": self.page.number,
            self.total_label: total_items,
            self.resource_name: data
        }

        if extra_data:
            base_data.update(extra_data)

        return Response({
            "success": True,
            "status": 200,
            "message": message,
            "data": base_data
        })


class EnrollmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    def get_paginated_response(
        self,
        data,
        total=None,
        message="Success",
        response_type="courses",
        extra_data=None
    ):
        page_size = self.get_page_size(self.request) or self.page_size
        total_items = total if total is not None else self.page.paginator.count
        total_pages = math.ceil(total_items / page_size)

        base_data = {
            "total_pages": total_pages,
            "current_page": self.page.number,
        }

        if response_type == "courses":
            base_data.update({
                "total_courses": total_items,
                "courses": data
            })

        elif response_type == "students":
            base_data.update({
                "total_students": total_items,
                "students": data
            })

        elif response_type == "instructor":
            base_data.update({
                "total_instructor": total_items,
                "instructor": data
            })

        elif response_type == "materials":
            base_data.update({
                "total_materials": total_items,
                "materials": data
            })

        elif response_type == "announcements":
            base_data.update({
                "total_announcements": total_items,
                "announcements": data
            })

        elif response_type == "notifications":
            base_data.update({
                "total_notifications": total_items,
                "notifications": data
            })

        elif response_type == "quizzes":
            base_data.update({
                "total_quizzes": total_items,
                "quizzes": data
            })

        if extra_data:
            base_data.update(extra_data)

        return Response({
            "success": True,
            "status": 200,
            "message": message,
            "data": base_data
        })


# Legacy specific pagination classes (for backward compatibility)
# These can now use DynamicPagination instead
class MaterialsPagination(DynamicPagination):
    resource_name = 'materials'
    total_label = 'total_materials'


class AnnouncementsPagination(DynamicPagination):
    resource_name = 'announcements'
    total_label = 'total_announcements'


class NotificationsPagination(DynamicPagination):
    resource_name = 'notifications'
    total_label = 'total_notifications'


class QuizzesPagination(DynamicPagination):
    resource_name = 'quizzes'
    total_label = 'total_quizzes'