# apps/sources/views.py

import uuid

from django.http import HttpRequest
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.sources import services
from apps.sources.models import Source


class SourceAPIViewSet(viewsets.ReadOnlyModelViewSet):
    """
    POST /api/internal/v1/sources/<uuid:source_id>/report-error/
    """

    def get_queryset(self) -> list[Source]:
        return services.get_active_sources()

    @action(detail=True, methods=["post"], url_path="report-error")
    def report_error(self, request: HttpRequest, pk: uuid.UUID) -> Response:
        error_message = request.data.get("error_message", "Unknown error")
        try:
            services.register_source_error(source_id=pk, error_message=error_message)
            return Response({"detail": "Error reported"}, status=status.HTTP_200_OK)
        except Source.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
