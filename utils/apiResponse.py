from rest_framework.response import Response
from rest_framework import status

def success_response(message, data=None, status_code=status.HTTP_200_OK):
    """
    Standard success response
    """
    return Response(
        {
            "success": True,
            "status": status_code,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standard error response
    """
    return Response(
        {
            "success": False,
            "status": status_code,
            "message": message,
            "errors": errors,
        },
        status=status_code,
    )