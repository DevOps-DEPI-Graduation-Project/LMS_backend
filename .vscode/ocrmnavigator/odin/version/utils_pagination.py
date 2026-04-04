from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math


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
        total_items = total if total is not None else self.page.paginator.count
        total_pages = math.ceil(total_items / self.page_size)

        # ===== base data =====
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

        # ===== inject extra data =====
        if extra_data:
            base_data.update(extra_data)

        return Response({
            "success": True,
            "status": 200,
            "message": message,
            "data": base_data
        })