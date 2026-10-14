"""Custom middleware for request timing and structured logging."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("apiMission.requests")


class RequestLoggingMiddleware:
    """
    Log method, path, user and duration for each HTTP request.

    Required by the technical test for request observability.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - started) * 1000

        user = getattr(request, "user", None)
        user_label = "anonimo"
        if user is not None and getattr(user, "is_authenticated", False):
            user_label = getattr(user, "email", str(user.pk))

        logger.info(
            "method=%s path=%s status=%s user=%s duration_ms=%.2f",
            request.method,
            request.path,
            getattr(response, "status_code", "-"),
            user_label,
            elapsed_ms,
        )
        return response
