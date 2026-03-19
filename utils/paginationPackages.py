from typing import Type
from django.db.models import QuerySet
from django.core.paginator import Paginator, Page
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer


def paginate_queryset(
    queryset: QuerySet,
    request: Request,
    serializer_class: Type[Serializer],
    data_key: str = "items",
    total_key: str = "total_items",
    message: str = "Success"
) -> Response:
    
    page_number: int = int(request.query_params.get("page", 1))
    page_size: int = int(request.query_params.get("page_size", 10))

    paginator: Paginator = Paginator(queryset, page_size)
    page: Page = paginator.get_page(page_number)

    serializer: Serializer = serializer_class(
        page.object_list,
        many=True,
        context={"request": request}
    )

    return Response({
        "success": True,
        "status": 200,
        "message": message,
        "data": {
            total_key: paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            data_key: serializer.data
        }
    })