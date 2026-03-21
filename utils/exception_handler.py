from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    """
    Unified error response format for all API exceptions.
    Handles both dict-based errors (401, 403, 404) and
    list-based errors (ValidationError from serializers).
    """
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data

        if isinstance(data, list):
            # ValidationError returns a list e.g. ["You have reached max attempts."]
            message = str(data[0]) if data else "Something went wrong."
        elif isinstance(data, dict):
            if "detail" in data:
                message = str(data["detail"])
            elif "non_field_errors" in data:
                message = str(data["non_field_errors"][0])
            else:
                # Field-level errors e.g. {"email": ["This field is required."]}
                first_key = next(iter(data))
                first_error = data[first_key]
                message = f"{first_key}: {str(first_error[0]) if isinstance(first_error, list) else str(first_error)}"
        else:
            message = "Something went wrong."

        response.data = {
            "success": False,
            "status": response.status_code,
            "message": message,
            "data": None
        }

    return response