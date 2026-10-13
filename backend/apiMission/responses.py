"""Standard API response envelope helpers."""

from typing import Any

from rest_framework import status as http_status
from rest_framework.response import Response

MESSAGE_OK = "OK"
MESSAGE_WARNING = "WARNING"
MESSAGE_ERROR = "ERROR"


def _normalize_data(data: Any) -> dict | list:
    """Ensure data is always a dictionary or a list of dictionaries."""
    if data is None:
        return {}
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data
    return {"value": data}


def api_response(
    *,
    data: Any = None,
    message: str = MESSAGE_OK,
    success: bool | None = None,
    http_status_code: int = http_status.HTTP_200_OK,
) -> Response:
    """
    Build the standard Mission API response envelope.

    Envelope shape:
    {
        "status": bool,
        "message": "OK" | "WARNING" | "ERROR",
        "data": dict | list
    }
    """
    if success is None:
        success = message != MESSAGE_ERROR

    return Response(
        {
            "status": success,
            "message": message,
            "data": _normalize_data(data),
        },
        status=http_status_code,
    )


def ok_response(
    data: Any = None,
    *,
    http_status_code: int = http_status.HTTP_200_OK,
) -> Response:
    """Return a successful OK envelope."""
    return api_response(
        data=data,
        message=MESSAGE_OK,
        success=True,
        http_status_code=http_status_code,
    )


def warning_response(
    data: Any = None,
    *,
    http_status_code: int = http_status.HTTP_200_OK,
) -> Response:
    """Return a WARNING envelope (business soft warning)."""
    return api_response(
        data=data,
        message=MESSAGE_WARNING,
        success=True,
        http_status_code=http_status_code,
    )


def error_response(
    data: Any = None,
    *,
    http_status_code: int = http_status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Return an ERROR envelope."""
    return api_response(
        data=data,
        message=MESSAGE_ERROR,
        success=False,
        http_status_code=http_status_code,
    )
