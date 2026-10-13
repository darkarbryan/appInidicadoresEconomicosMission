"""Project-level HTTP views."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from apiMission.responses import ok_response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """Return a simple health message for the Mission API root."""
    return ok_response(
        {
            "detail": "La API de Mission está OK.",
        }
    )
