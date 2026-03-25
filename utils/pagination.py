from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class EnrollmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data, total=None, message="Success", response_type="courses"):
        total_items = total if total is not None else self.page.paginator.count
        total_pages = math.ceil(total_items / self.page_size)

        if response_type == "courses":
            return Response({
                "success": True,
                "status": 200,
                "message": message,
                "data": {
                    "total_courses": total_items,
                    "total_pages": total_pages,
                    "current_page": self.page.number,
                    "courses": data
                }
            })
        elif response_type == "students":
            return Response({
                "success": True,
                "status": 200,
                "message": message,
                "data": {
                    "total_students": total_items,
                    "total_pages": total_pages,
                    "current_page": self.page.number,
                    "students": data
                }
        
            })
        elif response_type == "instructor":
            return Response({
                "success": True,
                "status": 200,
                "message": message,
                "data": {
                    "total_instructor": total_items,
                    "total_pages": total_pages,
                    "current_page": self.page.number,
                    "instructor": data
                }
            })
