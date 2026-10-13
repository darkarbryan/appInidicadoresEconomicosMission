"""Custom DRF exception handling with the standard API envelope."""

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from apiMission.responses import error_response


def _extract_error_data(detail) -> dict | list:
    """Normalize DRF exception detail into a dict or list for the data field."""
    if detail is None:
        return {"detail": "Ocurrió un error inesperado."}
    if isinstance(detail, (dict, list)):
        return detail
    return {"detail": str(detail)}


def custom_exception_handler(exc, context):
    """
    Wrap DRF/API exceptions into the standard Mission response envelope.

    status=false, message=ERROR, data=<error payload>
    """
    response = exception_handler(exc, context)

    if response is None:
        return error_response(
            {"detail": "Ocurrió un error interno en el servidor."},
            http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    http_code = response.status_code
    if isinstance(exc, APIException):
        data = _extract_error_data(exc.detail)
    else:
        data = _extract_error_data(response.data)

    return error_response(data, http_status_code=http_code)
