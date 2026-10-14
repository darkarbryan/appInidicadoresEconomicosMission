"""Pagination classes that preserve the Mission API response envelope."""

from rest_framework.pagination import PageNumberPagination

from apiMission.responses import ok_response


class StandardPagination(PageNumberPagination):
    """Page-number pagination with configurable page_size (default 20)."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Wrap paginated results inside the standard API envelope."""
        return ok_response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "results": data,
            }
        )
